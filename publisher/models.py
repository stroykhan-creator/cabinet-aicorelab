from django.db import models
from cabinet.models import Company

class SocialGroup(models.Model):
    PLATFORM_CHOICES = [
        ('wa', 'Обычный WhatsApp'),
        ('max', 'MAX (Green API)'),
        ('tg', 'Telegram (Green API)'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name="Инстанс (Аккаунт)")
    name = models.CharField(max_length=255, verbose_name="Название списка групп")
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, default='wa', verbose_name="Тип сети")
    
    invite_links = models.TextField(
        verbose_name="Ссылки-приглашения", 
        blank=True, 
        help_text="Вставьте ссылки (каждая с новой строки): t.me/..., max.ru/join/... или chat.whatsapp.com/..."
    )
    
    identifiers = models.TextField(
        verbose_name="Готовые Chat ID", 
        blank=True,
        help_text="Заполняется автоматически после нажатия кнопки 'Вступить'."
    )
    
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    class Meta:
        verbose_name = "Список групп"
        verbose_name_plural = "Списки групп"

    def __str__(self):
        return f"{self.name} ({self.get_platform_display()})"

    def get_id_list(self):
        if not self.identifiers: return []
        return [i.strip() for i in self.identifiers.split('\n') if i.strip()]

    def get_links_list(self):
        if not self.invite_links: return []
        return [l.strip() for l in self.invite_links.split('\n') if l.strip()]


class AutoPost(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name="Инстанс (Аккаунт)")
    title = models.CharField(max_length=200, verbose_name="Заголовок поста")
    text = models.TextField(verbose_name="Текст сообщения / Подпись к фото")
    
    # ПОЛЕ ДЛЯ ЗАГРУЗКИ ФАЙЛА
    media_file = models.FileField(
        upload_to='post_media/', 
        blank=True, 
        null=True, 
        verbose_name="Медиафайл (фото/видео)",
        help_text="Загрузите файл напрямую. Если есть файл, он будет отправлен с текстом сообщения."
    )
    
    targets = models.ManyToManyField(SocialGroup, verbose_name="Списки для публикации")
    
    # ПЕРИОД ПУБЛИКАЦИИ
    start_date = models.DateField(null=True, blank=True, verbose_name="Дата начала")
    end_date = models.DateField(null=True, blank=True, verbose_name="Дата окончания")

    # ДНИ НЕДЕЛИ
    monday = models.BooleanField(default=False, verbose_name="Пн")
    tuesday = models.BooleanField(default=False, verbose_name="Вт")
    wednesday = models.BooleanField(default=False, verbose_name="Ср")
    thursday = models.BooleanField(default=False, verbose_name="Чт")
    friday = models.BooleanField(default=False, verbose_name="Пт")
    saturday = models.BooleanField(default=False, verbose_name="Сб")
    sunday = models.BooleanField(default=False, verbose_name="Вс")
    
    post_time = models.TimeField(verbose_name="Время публикации")
    is_active = models.BooleanField(default=True, verbose_name="Включить расписание")

    class Meta:
        verbose_name = "Рекламный пост"
        verbose_name_plural = "Рекламные посты"

    def __str__(self):
        return self.title


class PostLog(models.Model):
    autopost = models.ForeignKey(AutoPost, on_delete=models.CASCADE, verbose_name="Пост")
    group_id = models.CharField(max_length=255, verbose_name="ID конкретной группы")
    status = models.CharField(max_length=50, verbose_name="Статус")
    response = models.TextField(blank=True, null=True, verbose_name="Ответ API")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата отправки")

    class Meta:
        verbose_name = "Лог публикации"
        verbose_name_plural = "Логи публикаций"