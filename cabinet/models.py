from django.db import models

class Company(models.Model):
    INSTANCE_TYPES = [
        ('wa', 'Обычный WhatsApp'),
        ('max', 'MAX (Выделенный канал)'),
        ('tg', 'Telegram (через Green API)'),
    ]

    name = models.CharField(max_length=255, verbose_name="Название компании")
    
    # Поля для РЕАНИМАТОРА (OpenAI)
    openai_key = models.CharField(max_length=255, blank=True, null=True, verbose_name="OpenAI API Key")
    system_prompt = models.TextField(blank=True, null=True, verbose_name="Системный промпт (Инструкция для ИИ)")

    # Поля для ВЕЩАТЕЛЯ (Green API)
    instance_type = models.CharField(
        max_length=10, 
        choices=INSTANCE_TYPES, 
        default='wa', 
        verbose_name="Тип сети / Инстанса"
    )
    green_api_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="Green API ID")
    green_api_token = models.CharField(max_length=255, blank=True, null=True, verbose_name="Green API Token")
    
    green_api_url = models.URLField(
        default="https://api.green-api.com", 
        blank=True, null=True,
        verbose_name="API URL",
        help_text="Система сама подставит нужный URL в зависимости от типа сети."
    )

    def save(self, *args, **kwargs):
        if self.instance_type == 'max':
            self.green_api_url = "https://3100.api.green-api.com"
        else:
            self.green_api_url = "https://api.green-api.com"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} [{self.get_instance_type_display()}]"

    class Meta:
        verbose_name = "Инстанс (Настройка API)"
        verbose_name_plural = "Инстансы (Настройки API)"

# --- Модели для Реаниматора ---

class Patient(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    status = models.CharField(max_length=50, default='new')
    last_contact = models.DateTimeField(auto_now=True)
    def __str__(self): return f"{self.name} ({self.phone})"

class KnowledgeBase(models.Model):
    company = models.OneToOneField(Company, on_delete=models.CASCADE)
    content = models.TextField(blank=True, null=True)

class Outreach(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=True, null=True) # Добавили null=True
    prompt = models.TextField(blank=True, null=True) # Добавили null=True
    is_active = models.BooleanField(default=True)

class MessageLog(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, blank=True, null=True)
    sender = models.CharField(max_length=10) 
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)