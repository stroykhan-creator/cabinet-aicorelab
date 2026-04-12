
# cabinet/admin.py
import csv
import io
from datetime import datetime

from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import render, redirect
from django.db import transaction
from django import forms
from django.utils import timezone
from django.utils.html import format_html

from .models import Company, Patient, KnowledgeBase, Outreach, MessageLog
from .forms import CompanyForm, PatientCSVUploadForm


class OwnerRestrictedAdminMixin:
    """
    Миксин для ограничения доступа: суперпользователь видит всё,
    обычный пользователь — только объекты своей компании (owner).
    """
    company_field = None  # должен быть переопределён в админ-классах

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs

        user_company = Company.objects.filter(owner=request.user).first()
        if user_company:
            if self.opts.model == Company:
                return qs.filter(id=user_company.id)
            elif self.company_field:
                filter_kwargs = {self.company_field: user_company}
                return qs.filter(**filter_kwargs)
        return qs.none()

    def save_model(self, request, obj, form, change):
        """
        При сохранении автоматически привязываем объект к компании владельца,
        если это уместно (и если это не суперпользователь).
        """
        if not request.user.is_superuser:
            user_company = Company.objects.filter(owner=request.user).first()
            if user_company and hasattr(obj, 'company'):
                if obj.company is None:
                    obj.company = user_company
        super().save_model(request, obj, form, change)


@admin.register(Company)
class CompanyAdmin(OwnerRestrictedAdminMixin, admin.ModelAdmin):
    company_field = 'id'
    list_display = ('name', 'instance_type_badge', 'green_api_id')
    list_filter = ('instance_type',)
    search_fields = ('name', 'owner__username', 'green_api_id')
    raw_id_fields = ('owner',)
    form = CompanyForm

    def instance_type_badge(self, obj):
        colors = {'max': '#007bff', 'tg': '#17a2b8', 'wa': '#28a745'}
        color = colors.get(obj.instance_type, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 10px; font-weight: bold; font-size: 11px;">{}</span>',
            color, obj.get_instance_type_display()
        )
    instance_type_badge.short_description = "Тип сети"


@admin.register(Patient)
class PatientAdmin(OwnerRestrictedAdminMixin, admin.ModelAdmin):
    company_field = 'company'
    list_display = ('name', 'phone', 'email', 'status', 'last_contact', 'company')
    list_filter = ('status', 'company')
    search_fields = ('name', 'phone', 'email', 'notes', 'company__name')
    raw_id_fields = ('company',)

    change_list_template = 'admin/cabinet/patient/change_list_with_import_button.html'

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('import-csv/', self.admin_site.admin_view(self.import_csv_admin_view), name='cabinet_patient_import_csv_admin'),
        ]
        return my_urls + urls

    def import_csv_admin_view(self, request):
        """
        Безопасный импорт CSV:
        - суперпользователь: доступ ко всем компаниям;
        - обычный пользователь: только к компаниям, где он owner.
        """
        if request.user.is_superuser:
            allowed_qs = Company.objects.all()
        else:
            allowed_qs = Company.objects.filter(owner=request.user)

        allowed_count = allowed_qs.count()

        if allowed_count == 0:
            self.message_user(request, "Для импорта пациентов у вас должна быть зарегистрирована хотя бы одна компания.", level=messages.ERROR)
            return redirect('admin:cabinet_company_add')

        company_id = (
            request.GET.get('company_id') or
            request.POST.get('company_id') or
            request.GET.get('company_id__exact') or
            request.GET.get('company__id__exact') or
            request.GET.get('company__exact')
        )

        user_company = None
        if company_id:
            try:
                user_company = allowed_qs.get(id=company_id)
            except Company.DoesNotExist:
                user_company = None

        if not user_company and allowed_count == 1:
            user_company = allowed_qs.first()

        if not user_company and allowed_count > 1:
            if request.method == 'GET':
                context = dict(self.admin_site.each_context(request))
                context.update({
                    'title': 'Выберите компанию для импорта',
                    'allowed_companies': allowed_qs,
                })
                return render(request, 'admin/cabinet/patient/patient_import_choose_company.html', context)
            else:
                self.message_user(request, "Не выбрана компания для импорта. Пожалуйста, укажите компанию.", level=messages.ERROR)
                return redirect('admin:cabinet_patient_changelist')

        errors_list = []
        if request.method == 'POST':
            form = PatientCSVUploadForm(request.POST, request.FILES)
            if form.is_valid():
                csv_file = request.FILES['csv_file']

                if not csv_file.name.lower().endswith('.csv'):
                    self.message_user(request, "Неверный формат файла. Пожалуйста, загрузите CSV файл.", level=messages.ERROR)
                else:
                    try:
                        decoded_file = io.TextIOWrapper(csv_file.file, encoding='utf-8')
                        reader = csv.DictReader(decoded_file)
                    except Exception as e:
                        self.message_user(request, f"Ошибка при чтении файла: {e}", level=messages.ERROR)
                        reader = None

                    if reader:
                        expected_headers = ['first_name', 'last_name', 'email', 'phone', 'date_of_birth', 'notes']
                        if reader.fieldnames is None:
                            self.message_user(request, "CSV файл пуст или имеет некорректные заголовки.", level=messages.ERROR)
                        else:
                            missing = [h for h in expected_headers if h not in reader.fieldnames]
                            if missing:
                                self.message_user(request, f"В CSV файле отсутствуют заголовки: {', '.join(missing)}", level=messages.ERROR)
                            else:
                                patients_to_create = []
                                line_num = 1
                                for row in reader:
                                    line_num += 1
                                    current_row_errors = []

                                    first_name = row.get('first_name', '').strip()
                                    last_name = row.get('last_name', '').strip()
                                    name = f"{first_name} {last_name}".strip() or "Не указано"

                                    email = row.get('email', '').strip()
                                    phone = row.get('phone', '').strip()
                                    date_of_birth_str = row.get('date_of_birth', '').strip()
                                    notes = row.get('notes', '').strip()

                                    if not email and not phone:
                                        current_row_errors.append("Необходимо указать email или phone.")

                                    if email:
                                        try:
                                            forms.EmailField().clean(email)
                                        except forms.ValidationError:
                                            current_row_errors.append(f"Неверный email: {email}")
                                            email = None

                                    dob = None
                                    if date_of_birth_str:
                                        try:
                                            dob = datetime.strptime(date_of_birth_str, '%Y-%m-%d').date()
                                        except ValueError:
                                            current_row_errors.append(f"Неверный формат date_of_birth: {date_of_birth_str}")

                                    if current_row_errors:
                                        errors_list.append(f"Строка {line_num}: {'; '.join(current_row_errors)}")
                                    else:
                                        patients_to_create.append(Patient(
                                            company=user_company,
                                            status='new',
                                            created_at=timezone.now(),
                                            last_contact=None,
                                            first_name=first_name or None,
                                            last_name=last_name or None,
                                            name=name,
                                            email=email,
                                            phone=phone or None,
                                            date_of_birth=dob,
                                            notes=notes
                                        ))

                                if errors_list:
                                    self.message_user(request, f"Обнаружены ошибки в {len(errors_list)} строках. Импорт отменён.", level=messages.ERROR)
                                else:
                                    try:
                                        with transaction.atomic():
                                            Patient.objects.bulk_create(patients_to_create)
                                        self.message_user(request, f"Успешно импортировано {len(patients_to_create)} пациентов в компанию \"{user_company.name}\".", level=messages.SUCCESS)
                                        return redirect('admin:cabinet_patient_changelist')
                                    except Exception as e:
                                        self.message_user(request, f"Ошибка при сохранении: {e}", level=messages.ERROR)
            else:
                self.message_user(request, "Пожалуйста, выберите CSV файл.", level=messages.ERROR)
        else:
            form = PatientCSVUploadForm()

        context = dict(self.admin_site.each_context(request))
        context.update({'form': form, 'errors_list': errors_list, 'title': 'Импорт пациентов из CSV', 'user_company': user_company})
        return render(request, 'admin/cabinet/patient/patient_import_csv_admin.html', context)


@admin.register(KnowledgeBase)
class KnowledgeBaseAdmin(OwnerRestrictedAdminMixin, admin.ModelAdmin):
    company_field = 'company'
    list_display = ('company', 'content_preview', 'category', 'created_at')
    search_fields = ('title', 'content', 'company__name')
    list_filter = ('company', 'category', 'created_at')
    raw_id_fields = ('company',)

    def content_preview(self, obj):
        return obj.content[:50] + '...' if obj.content else '-'
    content_preview.short_description = "Содержимое"


@admin.register(Outreach)
class OutreachAdmin(OwnerRestrictedAdminMixin, admin.ModelAdmin):
    company_field = 'company'
    list_display = ('name', 'is_active', 'company', 'created_at')
    list_filter = ('is_active', 'company', 'created_at')
    search_fields = ('name', 'prompt', 'company__name')
    raw_id_fields = ('company',)


@admin.register(MessageLog)
class MessageLogAdmin(OwnerRestrictedAdminMixin, admin.ModelAdmin):
    company_field = 'patient__company'
    list_display = ('patient', 'sender', 'text_preview', 'created_at')
    readonly_fields = ('patient', 'sender', 'text', 'created_at')
    list_filter = ('sender', 'created_at', 'patient__company')
    search_fields = ('patient__name', 'patient__phone', 'text')
    raw_id_fields = ('patient',)

    def text_preview(self, obj):
        return obj.text[:50] + '...' if obj.text else '-'
    text_preview.short_description = "Текст"
