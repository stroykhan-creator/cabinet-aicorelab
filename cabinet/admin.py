
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

from .models import Company, Patient, KnowledgeBase, Outreach, MessageLog, Profile
from .forms import CompanyForm, PatientCSVUploadForm

class OwnerRestrictedAdminMixin:
    """
    Миксин для ограничения доступа: суперпользователь видит всё,
    обычный пользователь — только объекты своей компании (owner).
    """
    company_field = None

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs

        user_company = Company.objects.filter(owner=request.user).first()
        if user_company:
            if getattr(self, "model", None) == Company or getattr(self, "opts", None).model == Company:
                return qs.filter(id=user_company.id)
            elif self.company_field:
                filter_kwargs = {self.company_field: user_company}
                return qs.filter(**filter_kwargs)
        return qs.none()

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            user_company = Company.objects.filter(owner=request.user).first()
            if user_company and hasattr(obj, 'company'):
                if obj.company is None:
                    obj.company = user_company
        super().save_model(request, obj, form, change)


@admin.register(Company)
class CompanyAdmin(OwnerRestrictedAdminMixin, admin.ModelAdmin):
    company_field = 'id'
    
    list_display = ('name', 'owner', 'is_wa_enabled', 'is_max_enabled', 'instance_type', 'created_at')
    list_editable = ('is_wa_enabled', 'is_max_enabled')
    search_fields = ('name', 'owner__username', 'green_api_id')
    raw_id_fields = ('owner',)
    form = CompanyForm

    fieldsets = (
        ("Основная информация", {
            'fields': ('name', 'owner', 'instance_type', 'is_active', 'description')
        }),
        ("Каналы связи (Включение)", {
            'fields': ('is_wa_enabled', 'is_max_enabled'),
        }),
        ("Настройки WhatsApp (Green API)", {
            'fields': ('green_api_id', 'green_api_token'),
        }),
        ("Настройки МАКС (Green API)", {
            'fields': ('max_api_id', 'max_api_token'),
        }),
        ("Настройки ИИ (OpenAI)", {
            'fields': ('openai_key', 'system_prompt'),
        }),
        ("Технические параметры", {
            'fields': ('green_api_receive_timeout', 'green_api_send_timeout', 'created_at'),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ('created_at',)


@admin.register(KnowledgeBase)
class KnowledgeBaseAdmin(OwnerRestrictedAdminMixin, admin.ModelAdmin):
    company_field = 'company'
    # ИСПРАВЛЕНО: используем 'topic' вместо 'title'
    list_display = ('topic', 'company', 'created_at')
    # ИСПРАВЛЕНО: используем 'topic' и 'information' вместо 'title' и 'content'
    search_fields = ('topic', 'information', 'company__name')
    list_filter = ('company', 'created_at')
    raw_id_fields = ('company',)


@admin.register(Patient)
class PatientAdmin(OwnerRestrictedAdminMixin, admin.ModelAdmin):
    company_field = 'company'
    list_display = ('name', 'company', 'status', 'phone', 'next_contact', 'created_at')
    list_filter = ('company', 'status', 'created_at')
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
        if request.user.is_superuser:
            allowed_qs = Company.objects.all()
        else:
            allowed_qs = Company.objects.filter(owner=request.user)

        allowed_count = allowed_qs.count()
        if allowed_count == 0:
            self.message_user(request, "Нет зарегистрированных компаний.", level=messages.ERROR)
            return redirect('admin:cabinet_company_add')

        company_id = request.GET.get('company_id') or request.POST.get('company_id')
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
                context.update({'title': 'Выберите компанию', 'allowed_companies': allowed_qs})
                return render(request, 'admin/cabinet/patient/patient_import_choose_company.html', context)
            return redirect('admin:cabinet_patient_changelist')

        errors_list = []
        if request.method == 'POST':
            form = PatientCSVUploadForm(request.POST, request.FILES)
            if form.is_valid():
                csv_file = request.FILES['csv_file']
                try:
                    decoded_file = io.TextIOWrapper(csv_file.file, encoding='utf-8')
                    reader = csv.DictReader(decoded_file)
                    expected_headers = ['first_name', 'last_name', 'email', 'phone', 'date_of_birth', 'notes']
                    
                    patients_to_create = []
                    for row in reader:
                        first_name = row.get('first_name', '').strip()
                        last_name = row.get('last_name', '').strip()
                        patients_to_create.append(Patient(
                            company=user_company,
                            name=f"{first_name} {last_name}".strip() or "Не указано",
                            first_name=first_name,
                            last_name=last_name,
                            email=row.get('email', '').strip(),
                            phone=row.get('phone', '').strip(),
                            notes=row.get('notes', '').strip()
                        ))
                    
                    with transaction.atomic():
                        Patient.objects.bulk_create(patients_to_create)
                    self.message_user(request, "Импорт завершен.", level=messages.SUCCESS)
                    return redirect('admin:cabinet_patient_changelist')
                except Exception as e:
                    self.message_user(request, f"Ошибка: {e}", level=messages.ERROR)
        else:
            form = PatientCSVUploadForm()

        context = dict(self.admin_site.each_context(request))
        context.update({'form': form, 'errors_list': errors_list, 'title': 'Импорт из CSV', 'user_company': user_company})
        return render(request, 'admin/cabinet/patient/patient_import_csv_admin.html', context)


@admin.register(Outreach)
class OutreachAdmin(OwnerRestrictedAdminMixin, admin.ModelAdmin):
    company_field = 'company'
    list_display = ('patient', 'company', 'status', 'created_at')
    list_filter = ('company', 'status', 'created_at')
    raw_id_fields = ('company', 'patient')


@admin.register(MessageLog)
class MessageLogAdmin(OwnerRestrictedAdminMixin, admin.ModelAdmin):
    company_field = 'company'
    list_display = ('chat_id', 'sender', 'company', 'created_at')
    readonly_fields = ('company', 'patient', 'chat_id', 'sender', 'text', 'created_at')
    list_filter = ('company', 'sender', 'created_at')
    search_fields = ('chat_id', 'text', 'patient__name')
    raw_id_fields = ('company', 'patient')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone')
