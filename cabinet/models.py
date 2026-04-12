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

    name = models.CharField(
        max_length=255,
        verbose_name="Название компании",
        default="Новая компания"
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_companies',
        null=True,
        blank=True
    )
    description = models.TextField(blank=True, null=True)
    instance_type = models.CharField(
        max_length=20,
        choices=INSTANCE_CHOICES,
        default='trial'
    )
    system_prompt = models.TextField(blank=True, null=True)
    green_api_id = models.CharField(max_length=100, blank=True, null=True)
    green_api_token = models.CharField(max_length=255, blank=True, null=True)
    openai_key = models.CharField(max_length=255, blank=True, null=True)
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
    created_at = models.DateTimeField(default=timezone.now)
    date_of_birth = models.DateField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


# --- БАЗА ЗНАНИЙ ---
class KnowledgeBase(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='articles', null=True, blank=True)
    title = models.CharField(max_length=255, default="Без заголовка")
    content = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


# --- РАССЫЛКИ ---
class Outreach(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='outreaches', null=True, blank=True)
    name = models.CharField(max_length=255, default="Без названия")
    is_active = models.BooleanField(default=True)
    subject = models.CharField(max_length=255, blank=True, null=True)
    body = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name


# --- ЛОГИ СООБЩЕНИЙ ---
class MessageLog(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, null=True, blank=True)
    sender = models.CharField(max_length=50, default="system")
    text = models.TextField(default="", blank=True, null=True)
    status = models.CharField(max_length=20, default="sent")
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.patient.name if self.patient else 'Unknown'} - {self.status}"