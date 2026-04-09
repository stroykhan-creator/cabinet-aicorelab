# cabinet/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User
from .models import Company

# Наша кастомная форма регистрации пользователя
class CustomUserCreationForm(UserCreationForm):
    # Добавляем поле для названия компании
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
        # UserCreationForm.Meta.fields уже включает 'username', 'password', 'password2'.
        # Мы просто добавляем 'company_name' к этому списку.
        fields = UserCreationForm.Meta.fields + ('company_name',)

        # Кастомизируем виджеты и метки для всех полей, включая унаследованные
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Логин',
                'required': True
            }),
            'password': forms.PasswordInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Пароль',
                'required': True
            }),
            'password2': forms.PasswordInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Повторите пароль',
                'required': True
            }),
        }
        labels = {
            'username': "Логин",
            'password': "Пароль",
            'password2': "Подтверждение пароля",
            # 'company_name' уже имеет метку, определенную выше
        }
        help_texts = {
            'username': None, # Убираем стандартный help text для username
        }

    # Эти методы clean можно оставить, если нужны кастомные сообщения,
    # иначе UserCreationForm предоставляет свои базовые проверки.
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Пользователь с таким логином уже существует.")
        return username

    # clean_password2 уже реализован в UserCreationForm, но можно переопределить для кастомного сообщения
    # def clean_password2(self):
    #     password = self.cleaned_data.get("password")
	#     password2 = self.cleaned_data.get("password2")
    #     if password and password2 and password != password2:
    #         raise forms.ValidationError("Пароли не совпадают.")
    #     return password2


# Форма для редактирования профиля пользователя (если понадобится)
class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = UserCreationForm.Meta.fields

# Форма для данных компании
class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        # ИСПРАВЛЕНО: Добавлено 'instance_type' в список полей
        fields = ['name', 'instance_type', 'green_api_id', 'green_api_token', 'openai_key', 'system_prompt']
        labels = {
            "name": "Название компании",
            "instance_type": "Тип сети / Инстанса", # Добавлено для ясности
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
            'instance_type': forms.Select(attrs={
                'class': 'form-control form-control-lg',
                # placeholder здесь не нужен для Select
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
                'rows': 4,
                'placeholder': 'Инструкции для ИИ'
            }),
        }
		