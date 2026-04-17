from django.db import models
from django.conf import settings
from django.utils import timezone


class Company(models.Model):
    is_active = models.BooleanField(default=True, verbose_name="Компания активна")
    name = models.CharField(max_length=255, verbose_name="Название компании", default="Новая компания")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_companies',
        null=True,
        blank=True,
    )
    description = models.TextField(blank=True, null=True)
    instance_type = models.CharField(
        max_length=20,
        choices=[('trial', 'Пробный'), ('pro', 'Профессиональный'), ('business', 'Бизнес')],
        default='trial',
    )
    system_prompt = models.TextField(blank=True, null=True)
    openai_key = models.CharField(max_length=255, blank=True, null=True)

    # Поля для управления ИИ
    auto_reply_enabled = models.BooleanField(default=False, verbose_name="Автоответчик включен")
    is_reanimator_enabled = models.BooleanField(default=False, verbose_name="Реаниматор включен")

    is_wa_enabled = models.BooleanField(default=True, verbose_name="WhatsApp активен")
    is_max_enabled = models.BooleanField(default=False, verbose_name="Макс активен")
    green_api_id = models.CharField(max_length=100, blank=True, null=True)
    green_api_token = models.CharField(max_length=255, blank=True, null=True)
    max_api_id = models.CharField(max_length=100, blank=True, null=True)
    max_api_token = models.CharField(max_length=255, blank=True, null=True)
    green_api_receive_timeout = models.IntegerField(default=5)
    green_api_send_timeout = models.IntegerField(default=10)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Компания"
        verbose_name_plural = "Компании"

    def __str__(self):
        return self.name


class Patient(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='patients', null=True)
    name = models.CharField(max_length=255, default="Не указано")
    phone = models.CharField(max_length=20, blank=True, null=True)
    next_contact = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=50, default='В работе')

    def __str__(self):
        return self.name


class KnowledgeBase(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='knowledge_base', null=True)
    topic = models.CharField(max_length=255, default="Общее")
    information = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.topic


class Outreach(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='outreaches', null=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='patient_outreaches', null=True)
    status = models.CharField(max_length=20, default='Не начат')
    created_at = models.DateTimeField(default=timezone.now) # <--- ДОБАВЬТЕ ЭТУ СТРОКУ

    def __str__(self):
        patient_name = self.patient.name if self.patient else "Без пациента"
        return f"{patient_name} - {self.status}"


class MessageLog(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='logs', null=True)
    chat_id = models.CharField(max_length=100, blank=True, null=True)
    sender = models.CharField(max_length=50, default="system")
    text = models.TextField(default="")
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        cid = self.chat_id or "no-chat"
        # Форматируем дату в строке, чтобы избежать проблем с неоконченной строкой при отладке
        created = self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else "no-date"
        return f"{cid} | {self.sender} | {created}"


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, default='staff')
    phone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        username = getattr(self.user, 'username', str(self.user))
        return f"{username}"