# core/urls.py
from django.contrib import admin
from django.urls import path
# Импортируем все нужные view функции
from cabinet.views import (
    dashboard,
    patient_list,
    knowledge_base_list,
    client_chat,
    custom_login,
    custom_logout,
    registration_company,
    pending_approval,
    company_create,
    patient_import_csv,
    toggle_reanimator  # <<< ДОБАВЛЕНА ЭТА ФУНКЦИЯ
)

urlpatterns = [
    # Путь для переключения реаниматора
    path('company/<int:company_id>/toggle-reanimator/', toggle_reanimator, name='toggle_reanimator'),

    # Главная страница сайта - наша кастомная страница входа
    path('', custom_login, name='login'),
    path('logout/', custom_logout, name='logout'),

    # Страница ожидания
    path('pending/', pending_approval, name='pending_approval'),

    # Страница регистрации
    path('register/', registration_company, name='registration_company'),

    # Основные страницы dashboard'а
    path('dashboard/', dashboard, name='dashboard'),
    path('patients/', patient_list, name='patient_list'),
    path('knowledge/', knowledge_base_list, name='knowledge_base'),
    path('chat/<int:patient_id>/', client_chat, name='client_chat'),

    # URL для создания компании
    path('companies/create/', company_create, name='company_create'),

    # Стандартная админка Django
    path('admin/', admin.site.urls),

    path('patients/import/', patient_import_csv, name='patient_import_csv'),
]
