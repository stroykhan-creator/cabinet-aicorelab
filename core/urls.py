# core/urls.py
from django.contrib import admin
from django.urls import path
# Импортируем все нужные view функции
from cabinet.views import dashboard, patient_list, knowledge_base_list, client_chat, custom_login, custom_logout, registration_company, pending_approval  # Добавили registration_company

urlpatterns = [
    # Главная страница сайта - наша кастомная страница входа
    path('', custom_login, name='login'),
    path('logout/', custom_logout, name='logout'),
# Новый URL страница ожидания
    path('pending/', pending_approval, name='pending_approval'), # Новый URL
    # Страница регистрации
    path('register/', registration_company, name='registration_company'),  # Вот он, наш новый URL!

    # Основные страницы dashboard'а
    path('dashboard/', dashboard, name='dashboard'),
    path('patients/', patient_list, name='patient_list'),
    path('knowledge/', knowledge_base_list, name='knowledge_base'),
    path('chat/<int:patient_id>/', client_chat, name='client_chat'),

    # Стандартная админка Django
    path('admin/', admin.site.urls),
]