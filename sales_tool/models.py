from django.db import models

class Product(models.Model):
    company = models.ForeignKey('cabinet.Company', on_delete=models.CASCADE, null=True, blank=True, verbose_name='Компания (Company)')
    sku = models.CharField(max_length=100, unique=True, verbose_name='Артикул (SKU)')
    name = models.CharField(max_length=255, verbose_name='Название (Name)')
    description = models.TextField(blank=True, null=True, verbose_name='Описание (Description)')
    attributes_json = models.TextField(blank=True, null=True, verbose_name='Характеристики (Attributes JSON)')
    base_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='Цена розн. (Retail price)')
    wholesale_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='Цена опт. (Wholesale price)')
    stock_qty = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True, verbose_name='Остаток (Stock)')
    measure_unit = models.CharField(max_length=50, blank=True, null=True, verbose_name='Ед. изм. (Unit)')
    weight_kg = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, verbose_name='Вес (kg)')
    length_m = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, verbose_name='Длина (m)')
    width_m = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, verbose_name='Ширина (m)')
    height_m = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, verbose_name='Высота (m)')
    shipping_per_km = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Доставка за км (shipping per km)')
    image = models.FileField(upload_to='product_images/', blank=True, null=True, verbose_name='Изображение (Image)')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано (Created)')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено (Updated)')

    def __str__(self):
        return f"{self.sku} - {self.name}"

class ClientProfile(models.Model):
    patient = models.OneToOneField('cabinet.Patient', on_delete=models.CASCADE, related_name='client_profile', verbose_name='Пациент (Patient)')
    manager = models.CharField(max_length=255, blank=True, null=True, verbose_name='Менеджер/Врач (Manager / Doctor)')
    phone = models.CharField(max_length=50, blank=True, null=True, verbose_name='Телефон (Phone)')
    last_visit = models.DateField(blank=True, null=True, verbose_name='Дата последнего визита (Last visit)')
    notes = models.TextField(blank=True, null=True, verbose_name='История / Заметки (History / Notes)')

    def __str__(self):
        try:
            return f"{self.patient.name}"
        except:
            return f"ClientProfile {self.id}"

class Treatment(models.Model):
    company = models.ForeignKey('cabinet.Company', on_delete=models.CASCADE, null=True, blank=True, verbose_name='Компания (Company)')
    patient = models.ForeignKey('cabinet.Patient', on_delete=models.CASCADE, related_name='treatments', verbose_name='Пациент (Patient)')
    date = models.DateField(blank=True, null=True, verbose_name='Дата (Date)')
    doctor = models.CharField(max_length=255, blank=True, null=True, verbose_name='Врач/Менеджер (Doctor/Manager)')
    procedure = models.CharField(max_length=255, blank=True, null=True, verbose_name='Процедура / Товар (Procedure / Product)')
    price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='Цена (Price)')
    notes = models.TextField(blank=True, null=True, verbose_name='Заметки (Notes)')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано (Created)')

    def __str__(self):
        return f"{self.patient.name} - {self.procedure} ({self.date})"

class CalculationTemplate(models.Model):
    company = models.ForeignKey('cabinet.Company', on_delete=models.CASCADE, null=True, blank=True, verbose_name='Компания (Company)')
    name = models.CharField(max_length=255, verbose_name='Имя шаблона (Template name)')
    description = models.TextField(blank=True, null=True, verbose_name='Описание (Description)')
    required_inputs = models.TextField(blank=True, null=True, verbose_name='Поля ввода (required inputs JSON)')
    template_code = models.TextField(blank=True, null=True, verbose_name='Код/формула (Template code)')
    ui_steps = models.TextField(blank=True, null=True, verbose_name='UI шаги (UI steps JSON)')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано (Created)')

    def __str__(self):
        return f"{self.name}"

class Proposal(models.Model):
    company = models.ForeignKey('cabinet.Company', on_delete=models.CASCADE, null=True, blank=True, verbose_name='Компания (Company)')
    client = models.ForeignKey('cabinet.Patient', on_delete=models.CASCADE, null=True, blank=True, verbose_name='Клиент (Client)')
    template = models.ForeignKey(CalculationTemplate, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Шаблон (Template)')
    inputs = models.TextField(blank=True, null=True, verbose_name='Вводные данные (Inputs JSON)')
    result = models.TextField(blank=True, null=True, verbose_name='Результат (Result JSON)')
    file = models.FileField(upload_to='proposals/', blank=True, null=True, verbose_name='Файл КП (Proposal file)')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано (Created)')

    def __str__(self):
        return f"Proposal {self.id} for {self.client}"

class ButtonAction(models.Model):
    company = models.ForeignKey('cabinet.Company', on_delete=models.CASCADE, null=True, blank=True, verbose_name='Компания (Company)')
    key = models.CharField(max_length=20, verbose_name='Ключ кнопки (Button key)')
    label = models.CharField(max_length=255, verbose_name='Текст кнопки (Label)')
    action_type = models.CharField(max_length=100, verbose_name='Тип действия (Action type)')
    payload = models.TextField(blank=True, null=True, verbose_name='Пейлоад (Payload JSON)')

    def __str__(self):
        return f"{self.key} - {self.label}"
