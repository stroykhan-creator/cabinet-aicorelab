from django.db import models
from django.conf import settings
from django.utils import timezone

# --- МОДЕЛЬ КОМПАНИИ ---
class Company(models.Model):
    INSTANCE_CHOICES = [
        ('trial', 'Пробный'),
        ('pro', 'Профессиональный'),
        ('business', 'Бизнес'),
    ]

    is_active = models.BooleanField(default=True, verbose_name="Компания активна")
    name = models.CharField(max_length=255, verbose_name="Название компании", default="Новая компания")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_companies', null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    instance_type = models.CharField(max_length=20, choices=INSTANCE_CHOICES, default='trial')
    system_prompt = models.TextField(blank=True, null=True)
    openai_key = models.CharField(max_length=255, blank=True, null=True)

    # Флажки активации каналов
    is_wa_enabled = models.BooleanField(default=True, verbose_name="WhatsApp активен")
    is_max_enabled = models.BooleanField(default=False, verbose_name="Макс активен")
    
    # Настройки WhatsApp (используем ваши старые поля, чтобы ничего не сломать)
    green_api_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="WA Instance ID")
    green_api_token = models.CharField(max_length=255, blank=True, null=True, verbose_name="WA Token")
    
    # Настройки МАКС (новые поля для второго инстанса Green API)
    max_api_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="МАКС Instance ID")
    max_api_token = models.CharField(max_length=255, blank=True, null=True, verbose_name="МАКС Token")

    # Таймауты
    green_api_receive_timeout = models.IntegerField(default=5, verbose_name="Таймаут получения")
    green_api_send_timeout = models.IntegerField(default=10, verbose_name="Таймаут отправки")

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Компания"
        verbose_name_plural = "Компании"

    def __str__(self):
        return self.name

# --- ПРОФИЛЬ ---
class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, default='staff')
    phone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username if hasattr(self.user, 'username') else str(self.user)}"

# --- ПАЦИЕНТЫ ---
class Patient(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='patients', null=True, blank=True)
    name = models.CharField(max_length=255, verbose_name="ФИО", default="Не указано")
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    status = models.CharField(max_length=50, default="new", verbose_name="Статус")
    last_contact = models.DateTimeField(null=True, blank=True, verbose_name="Последний контакт")
    next_contact = models.DateField(null=True, blank=True, verbose_name="Дата след. контакта")
    created_at = models.DateTimeField(default=timezone.now)
    date_of_birth = models.DateField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name

# --- БАЗА ЗНАНИЙ ---
class KnowledgeBase(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='knowledge_base', null=True, blank=True)
    topic = models.CharField(max_length=255, default="Общее")
    information = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.topic

# --- РАССЫЛКИ ---
class Outreach(models.Model):
    STATUS_CHOICES = [
        ('Не начат', 'Не начат'),
        ('Отправлено', 'Отправлено'),
        ('ОТКАЗ', 'ОТКАЗ'),
        ('ИНТЕРЕС', 'ИНТЕРЕС'),
        ('Записан', 'Записан'),
        ('Диалог', 'Диалог'),
    ]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='outreaches', null=True, blank=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='patient_outreaches', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Не начат')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.patient.name if self.patient else 'No Patient'} - {self.status}"

# --- ЛОГИ СООБЩЕНИЙ ---
class MessageLog(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='logs', null=True, blank=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='logs', null=True, blank=True)
    chat_id = models.CharField(max_length=100, blank=True, null=True)
    sender = models.CharField(max_length=50, default="system") # "Клиент", "ИИ Администратор (WA)", "ИИ Администратор (MAX)"
    text = models.TextField(default="", blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.chat_id} - {self.sender}"