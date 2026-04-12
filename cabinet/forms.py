# cabinet/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import get_user_model
from .models import Company, Patient

User = get_user_model()

# 1. Форма регистрации нового пользователя
class CustomUserCreationForm(UserCreationForm):
    company_name = forms.CharField(
        max_length=200,
        label="Название компании",
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Название вашей компании'
        })
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('company_name',)

        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Логин',
                'required': True
            }),
        }
        labels = {
            'username': "Логин",
            'password': "Пароль",
            'password2': "Подтверждение пароля",
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Пользователь с таким логином уже существует.")
        return username

# 2. Форма для редактирования профиля
class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')

# 3. ОСНОВНАЯ ФОРМА КОМПАНИИ
# CompanyForm в cabinet/forms.py
class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = [
            'owner',
            'name',
            'instance_type',
            'description',
            'system_prompt',
            'green_api_id',
            'green_api_token',
            'openai_key'
        ]

        labels = {
            "owner": "Владелец (User)",
            "name": "Название компании",
            "instance_type": "Тип аккаунта / Инстанса",
            "description": "Краткое описание",
            "green_api_id": "Green API ID",
            "green_api_token": "Green API Token",
            "openai_key": "OpenAI API Key",
            "system_prompt": "Системный промпт (Инструкция для ИИ)",
        }

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Название вашей компании'
            }),
            'instance_type': forms.Select(attrs={'class': 'form-control form-control-lg'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Краткое описание деятельности'
            }),
            'green_api_id': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'ID вашего Green API'
            }),
            'green_api_token': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Токен вашего Green API'
            }),
            'openai_key': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Ваш ключ OpenAI API'
            }),
            'system_prompt': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Напишите здесь, как ИИ должен общаться с клиентами...'
            }),
        }


# 4. ФОРМА ЗАГРУЗКИ КЛИЕНТОВ ЧЕРЕЗ CSV
class PatientCSVUploadForm(forms.Form):
    csv_file = forms.FileField(
        label="Выберите CSV файл",
        help_text="Загрузите CSV файл. Ожидаемые заголовки: first_name,last_name,email,phone,date_of_birth,notes",
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )