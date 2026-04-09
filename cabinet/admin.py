from django.contrib import admin
from django.utils.html import format_html
from .models import Company, Patient, KnowledgeBase, Outreach, MessageLog
from .forms import CompanyForm
# from publisher.models import SocialGroup, AutoPost, PostLog # Это здесь не нужно, т.к. SocialGroupAdmin в publisher/admin.py

# --- Определение Миксина для ограничения прав (чтобы каждый видел только своё) ---
class OwnerRestrictedAdminMixin:
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'company') and request.user.company:
            filter_kwargs = {self.company_field: request.user.company}
            return qs.filter(**filter_kwargs)
        return qs.none()

    def save_model(self, request, obj, form, change):
        # Привязываем объект к компании пользователя, если поле company_field указано как 'company'
        if not request.user.is_superuser and hasattr(request.user, 'company') and self.company_field == 'company':
            obj.company = request.user.company
        super().save_model(request, obj, form, change)


# --- Админка для Компаний / Инстансов ---
@admin.register(Company)
class CompanyAdmin(OwnerRestrictedAdminMixin, admin.ModelAdmin):
    company_field = 'id' # Для самой компании фильтруем по её ID
    list_display = ('name', 'instance_type_badge', 'green_api_id')
    list_filter = ('instance_type',)
    form = CompanyForm 

    # Переопределяем get_queryset для CompanyAdmin, чтобы обычные пользователи видели только свою компанию
    def get_queryset(self, request):
        qs = super(admin.ModelAdmin, self).get_queryset(request) # вызываем оригинальный get_queryset
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'company'):
            return qs.filter(id=request.user.company.id)
        return qs.none()
        
    def instance_type_badge(self, obj):
        colors = {'max': '#007bff', 'tg': '#17a2b8', 'wa': '#28a745'}
        # ЭТА СТРОКА (51-я в оригинальном файле), убедитесь в её отступе!
        color = colors.get(obj.instance_type, '#6c757d') 
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 10px; font-weight: bold; font-size: 11px;">{}</span>',
            color, obj.get_instance_type_display()
        )
    instance_type_badge.short_description = "Тип сети"

# --- Админка для Пациентов ---
@admin.register(Patient)
class PatientAdmin(OwnerRestrictedAdminMixin, admin.ModelAdmin):
    company_field = 'company'
    list_display = ('name', 'phone', 'status', 'last_contact', 'company')
    list_filter = ('status', 'company')
    search_fields = ('name', 'phone', 'company__name')

# --- Админка для Базы Знаний ---
@admin.register(KnowledgeBase)
class KnowledgeBaseAdmin(OwnerRestrictedAdminMixin, admin.ModelAdmin):
    company_field = 'company'
    list_display = ('company', 'content_preview') 
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if obj.content else '-'
    content_preview.short_description = "Содержимое"

# --- Админка для Outreach ---
@admin.register(Outreach)
class OutreachAdmin(OwnerRestrictedAdminMixin, admin.ModelAdmin):
    company_field = 'company'
    list_display = ('name', 'is_active', 'company') 
    list_filter = ('is_active', 'company')
    search_fields = ('name', 'prompt', 'company__name')

# --- Админка для Лог сообщений (Реаниматор) ---
# --- Админка для Лог сообщений (Реаниматор) ---
# --- Админка для Лог сообщений (Реаниматор) ---
@admin.register(MessageLog)
class MessageLogAdmin(OwnerRestrictedAdminMixin, admin.ModelAdmin):
    company_field = 'patient__company'
    # list_display должен быть полным кортежем, убираем 'der', 'text' (они уже есть в readonly)
    list_display = ('patient', 'sender', 'text_preview', 'created_at') 
    # readonly_fields тоже должен быть полным, и поля должны существовать
    readonly_fields = ('patient', 'sender', 'text', 'created_at') 
    list_filter = ('sender', 'created_at', 'patient__company')
    # search_fields должны использовать правильные имена полей
    search_fields = ('patient__name', 'patient__phone', 'text') # ИСПРАВЛЕНО: patient__name, patient__phone

    def text_preview(self, obj):
        return obj.text[:50] + '...' if obj.text else '-'
    text_preview.short_description = "Текст"

