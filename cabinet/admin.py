from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Company, Patient, Outreach, MessageLog, KnowledgeBase, Profile

class OwnerRestrictedAdminMixin:
    """
    Безопасный миксин, который ограничивает queryset объектов по связям company__owner,
    если пользователь не суперпользователь. Если модель не содержит поля company, возвращаем весь queryset.
    Это минимальная и безопасная реализация для совместимости с другими приложениями.
    """
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        try:
            if request.user.is_superuser:
                return qs
            return qs.filter(company__owner=request.user)
        except Exception:
            return qs

    # Не меняем поведение сохранения по умолчанию, но даём возможность переопределять при необходимости.
    def save_model(self, request, obj, form, change):
        if not hasattr(obj, 'company') and hasattr(request.user, 'owned_companies'):
            # если модель не имеет company, ничего специального не делаем
            pass
        super().save_model(request, obj, form, change)

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'auto_reply_enabled', 'is_reanimator_enabled')
    list_editable = ('is_active', 'auto_reply_enabled', 'is_reanimator_enabled')
    actions = ['toggle_reanimator']

    @admin.action(description=_('Вкл/Выкл Реаниматор для выбранных компаний'))
    def toggle_reanimator(self, request, queryset):
        for company in queryset:
            company.is_reanimator_enabled = not company.is_reanimator_enabled
            company.save()
        self.message_user(request, _("Статус реаниматора изменен."))

@admin.register(Patient)
class PatientAdmin(OwnerRestrictedAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'phone', 'company', 'next_contact')
    search_fields = ('name', 'phone')

@admin.register(Outreach)
class OutreachAdmin(OwnerRestrictedAdminMixin, admin.ModelAdmin):
    list_display = ('patient', 'company', 'status',)
    list_filter = ('status',)

@admin.register(MessageLog)
class MessageLogAdmin(OwnerRestrictedAdminMixin, admin.ModelAdmin):
    list_display = ('chat_id', 'sender', 'company', 'created_at')
    readonly_fields = ('created_at',)

@admin.register(KnowledgeBase)
class KnowledgeBaseAdmin(OwnerRestrictedAdminMixin, admin.ModelAdmin):
    list_display = ('topic', 'company')

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone')

# сохраняем также простую регистрацию на случай, если кто-то импортирует напрямую
# admin.site.register(Outreach)
# admin.site.register(MessageLog)
# admin.site.register(KnowledgeBase)
# admin.site.register(Profile)
