from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('companies/create/', views.company_create, name='company_create'),
    path('patients/', views.patient_list, name='patient_list'),
    path('knowledge/', views.knowledgebase_list, name='knowledgebase_list'),
    # Путь для переключения реаниматора
    path('company/<int:company_id>/toggle-reanimator/', views.toggle_reanimator, name='toggle_reanimator'),
]
