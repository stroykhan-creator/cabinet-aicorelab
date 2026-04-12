# core/urls.py
from django.contrib import admin
from django.urls import path

# Импортируем все нужные view функции И НАШУ НОВУЮ company_create
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
    patient_import_csv # <<< ДОБАВИЛИ ЭТУ ФУНКЦИЮ
)

urlpatterns = [
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
    path('knowledge/', knowledge_base_list, name='knowledge_base'), # Имя 'knowledge_base' из вашего GitHub
    path('chat/<int:patient_id>/', client_chat, name='client_chat'),
    
    # <<< НОВЫЙ URL ДЛЯ СОЗДАНИЯ КОМПАНИИ
    path('companies/create/', company_create, name='company_create'), # <<< ДОБАВЛЕН
    
    # Стандартная админка Django
    path('admin/', admin.site.urls),
    
    path('patients/import/', patient_import_csv, name='patient_import_csv'), # <<< ДОБАВЛЕН
]

