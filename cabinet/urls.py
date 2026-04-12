from django.urls import path
from . import views

app_name = 'cabinet'

urlpatterns = [
    # Главная страница кабинета
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Создание компании (то, что мы восстанавливаем)
    path('companies/create/', views.company_create, name='company_create'),
    
    # Список пациентов (если у вас есть такая функция)
    path('patients/', views.patient_list, name='patient_list'),
    
    # База знаний
    path('knowledge/', views.knowledgebase_list, name='knowledgebase_list'),
]
