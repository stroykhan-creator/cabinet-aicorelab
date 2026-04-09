"""
Django settings for core project.
(автоматически сгенерированный / отредактированный файл)
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY: замените 'STR_KEY' на реальный секрет в .env на продакшене
SECRET_KEY = 'STR_KEY'

# DEBUG (в продакшене поставьте False)
DEBUG = True

ALLOWED_HOSTS = ['cabinet.aicorelab.ru', 'www.cabinet.aicorelab.ru']

# Application definition
INSTALLED_APPS = [
    'jazzmin',  # обычно желают видеть джазмин первым
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # ваши приложения
    'cabinet',
    'publisher',

    # новый инструмент расчётов / КП
    'sales_tool',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],  # при необходимости добавьте свои директории шаблонов
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# Database: оставляем sqlite как у вас
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation (как было)
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

# Internationalization
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static and Media
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# CSRF trusted origins — корректный список (убираем слитую строку)
CSRF_TRUSTED_ORIGINS = [
    'https://cabinet.aicorelab.ru',
    'https://www.cabinet.aicorelab.ru',
]

# Jazzmin (сохранена базовая конфигурация; можно расширить в будущем)
JAZZMIN_SETTINGS = {
    "site_title": "AI Core Lab",
    "site_header": "AI Core Lab",
    "site_brand": "Панель управления",
    "welcome_sign": "Добро пожаловать в систему управления",
    "copyright": "AI Core Lab Ltd",
    "search_model": ["cabinet.Patient", "publisher.AutoPost"],
    "show_sidebar": True,
    "navigation_expanded": True,
}

# Default auto field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Email / other settings (оставляю пустыми — можно настроить по необходимости)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Опционально: путь к медиа/статике и другие параметры можно добавить ниже
# END OF SETTINGS
