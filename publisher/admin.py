
import requests
from django.contrib import admin, messages
from django.utils.html import format_html
from cabinet.admin import OwnerRestrictedAdminMixin
from .models import SocialGroup, AutoPost, PostLog # <--- ЭТА СТРОКА ДОЛЖНА БЫТЬ

# --- Админка для Вещателя (SocialGroup) ---
@admin.register(SocialGroup)
class SocialGroupAdmin(OwnerRestrictedAdminMixin, admin.ModelAdmin):
    company_field = 'company'
    list_display = ('name', 'platform_badge', 'is_active', 'groups_count', 'company')
    actions = ['process_invite_links', 'sync_group_ids']

    # Переопределяем метод get_actions, чтобы динамически включать/отключать кнопки
    def get_actions(self, request):
        actions = super().get_actions(request)
        
        # !!!! ИСПРАВЛЕНИЕ ДЛЯ СТАРЫХ ВЕРСИЙ DJANGO (до 4.0) !!!!
        # Вместо admin.ACTION_CHECKBOX_NAME используем '_selected_action'
        if not request.POST.getlist('_selected_action'):
            return actions

        # Получаем выбранные объекты
        queryset = self.get_queryset(request).filter(pk__in=request.POST.getlist('_selected_action'))
        # !!!! КОНЕЦ ИСПРАВЛЕНИЯ !!!!
        
        has_max_groups = any(item.company.instance_type == 'max' for item in queryset)
        
        if has_max_groups:
            if 'process_invite_links' in actions:
                del actions['process_invite_links']
        
        return actions

    def platform_badge(self, obj):
        colors = {'max': '#007bff', 'tg': '#17a2b8', 'wa': '#28a745'}
        color = colors.get(obj.platform, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 10px; font-weight: bold; font-size: 11px;">{}</span>',
            color, obj.get_platform_display()
        )
    platform_badge.short_description = "Сеть"

    def groups_count(self, obj):
        return len(obj.get_id_list())
    groups_count.short_description = "Групп в списке"

    @admin.action(description="🔥 ВСТУПИТЬ по ссылкам (Только обычный WhatsApp)")
    def process_invite_links(self, request, queryset):
        for group_list in queryset:
            company = group_list.company
            if company.instance_type == 'max':
                self.message_user(
                    request, 
                    f"Список '{group_list.name}' привязан к MAX. Автоматическое вступление по ссылкам не поддерживается. Используйте ручное добавление ID.", 
                    messages.WARNING
                )
                continue

            base_url = "https://api.green-api.com"
            join_url = f"{base_url}/waInstance{company.green_api_id}/joinGroup/{company.green_api_token}"
            
            new_ids = []
            links_processed = 0
            for link in group_list.get_links_list():
                link = link.strip()
                if not link: continue
                links_processed += 1
                try:
                    invite_code = link.split('/')[-1].replace('+', '')
                    resp = requests.post(join_url, json={"inviteLink": invite_code}, timeout=20)
                    if resp.status_code == 200:
                        data = resp.json()
                        if 'chatId' in data:
                            chat_id = data['chatId']
                            if chat_id not in group_list.get_id_list() and chat_id not in new_ids:
                                new_ids.append(chat_id)
                        else:
                             self.message_user(request, f"Ошибка API (нет chatId) для '{link}': {data}", messages.WARNING)
                    else:
                        self.message_user(request, f"Ошибка API (Код {resp.status_code}) для '{link}': {resp.text}", messages.ERROR)
                except requests.exceptions.Timeout:
                    self.message_user(request, f"Тайм-аут при вступлении по ссылке '{link}'.", messages.ERROR)
                except Exception as e:
                    self.message_user(request, f"Ошибка при обработке ссылки '{link}': {str(e)}", messages.ERROR)
            
            if new_ids:
                updated_ids = list(set(group_list.get_id_list() + new_ids))
                group_list.identifiers = "\n".join(updated_ids)
                group_list.save()
                self.message_user(request, f"Добавлено {len(new_ids)} новых групп в '{group_list.name}'. Всего ссылок обработано: {links_processed}", messages.SUCCESS)
            elif links_processed > 0:
                self.message_user(request, f"Новых групп не добавлено из {links_processed} ссылок для '{group_list.name}'. Проверьте ссылки и статус инстанса.", messages.INFO)
            else:
                self.message_user(request, f"Для списка '{group_list.name}' не указано ни одной ссылки.", messages.INFO)


    @admin.action(description="🔄 СИНХРОНИЗИРОВАТЬ ID из аккаунта (Для MAX: см. инструкцию)")
    def sync_group_ids(self, request, queryset):
        for group_list in queryset:
            company = group_list.company
            if company.instance_type == 'max':
                self.message_user(
                    request, 
                    f"Для MAX инстанса ({company.name}) автоматическая синхронизация списка всех групп аккаунта не поддерживается Green API. "
                    "Вступите в группы вручную, затем получите Chat ID каждой группы с помощью бота "
                    f"`@id380124799522_1_bot` в MAX (перешлите ему сообщение из группы). "
                    "После получения ID, добавьте их в поле 'Идентификаторы групп (Chat ID)' вручную (каждый ID с новой строки).",
                    messages.WARNING
                )
                continue

            base_url = company.green_api_url.rstrip('/')
            url = f"{base_url}/waInstance{company.green_api_id}/getChats/{company.green_api_token}"
            
            try:
                resp = requests.get(url, timeout=20)
                if resp.status_code == 200:
                    chats = resp.json()
                    current_ids = set(group_list.get_id_list())
                    found_ids = []
                    for chat in chats:
                        cid = chat.get('chatId')
                        if cid and '@g.us' in cid:
                            found_ids.append(cid)
                    
                    if found_ids:
                        all_ids = list(current_ids | set(found_ids))
                        group_list.identifiers = "\n".join(all_ids)
                        group_list.save()
                        self.message_user(request, f"Синхронизировано! В списке '{group_list.name}' теперь {len(all_ids)} групп.", messages.SUCCESS)
                    else:
                        self.message_user(request, f"Активных групп не найдено в аккаунте '{company.name}'. Сначала вступите в них с телефона.", messages.WARNING)
                else:
                    self.message_user(request, f"Ошибка API при синхронизации ID для '{company.name}' (Код {resp.status_code}): {resp.text}", messages.ERROR)
            except requests.exceptions.Timeout:
                self.message_user(request, f"Тайм-аут при синхронизации ID для '{company.name}'.", messages.ERROR)
            except Exception as e:
                self.message_user(request, f"Ошибка при синхронизации ID для '{company.name}': {str(e)}", messages.ERROR)

# --- Админка для Вещателя (AutoPost) ---
@admin.register(AutoPost)
class AutoPostAdmin(OwnerRestrictedAdminMixin, admin.ModelAdmin):
    company_field = 'company'
    list_display = ('title', 'post_time', 'is_active', 'company')
    filter_horizontal = ('targets',)
    search_fields = ('title', 'company__name')

# --- Админка для Вещателя (PostLog) ---
@admin.register(PostLog)
class PostLogAdmin(OwnerRestrictedAdminMixin, admin.ModelAdmin):
    company_field = 'autopost__company'
    list_display = ('autopost', 'group_id', 'status', 'created_at')
    readonly_fields = ('created_at', 'response', 'autopost', 'group_id', 'status')
    list_filter = ('status', 'created_at', 'autopost__company')
    search_fields = ('group_id', 'autopost__title', 'autopost__company__name')
