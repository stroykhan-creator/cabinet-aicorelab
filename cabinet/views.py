import csv
import io
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Company, Patient
from .forms import CustomUserCreationForm, CompanyForm, PatientCSVUploadForm

@login_required
def dashboard(request):
    company = Company.objects.filter(owner=request.user).first()
    if not company:
        messages.info(request, "Сначала создайте профиль вашей клиники.")
        return redirect('company_create')
    
    # Заглушки для статистики, если данных еще нет
    context = {
        'company': company,
        'total_patients': Patient.objects.filter(company=company).count(),
        'total_messages': 0,
        'funnel': {'Отправлено': 0, 'Диалог': 0, 'ИНТЕРЕС': 0, 'Записан': 0}
    }
    return render(request, 'cabinet/dashboard.html', context)

@login_required
@require_POST
def toggle_reanimator(request, company_id):
    company = get_object_or_404(Company, id=company_id, owner=request.user)
    company.is_reanimator_enabled = not company.is_reanimator_enabled
    company.save()
    return JsonResponse({
        'status': 'success', 
        'is_reanimator_enabled': company.is_reanimator_enabled
    })

def custom_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'cabinet/login.html', {})

def custom_logout(request):
    logout(request)
    return redirect('login')

def registration_company(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            company_name = form.cleaned_data.get('company_name')
            Company.objects.create(name=company_name, owner=user)
            from django.contrib.auth import login
            login(request, user)
            messages.success(request, "Аккаунт успешно создан!")
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'cabinet/registration.html', {'form': form})

@login_required
def company_create(request):
    if Company.objects.filter(owner=request.user).exists():
        return redirect('dashboard')
    if request.method == 'POST':
        form = CompanyForm(request.POST)
        if form.is_valid():
            company = form.save(commit=False)
            company.owner = request.user
            company.save()
            return redirect('dashboard')
    else:
        form = CompanyForm()
    return render(request, 'cabinet/company_form.html', {'form': form})

@login_required
def patient_list(request):
    company = Company.objects.filter(owner=request.user).first()
    if not company: return redirect('company_create')
    patients = Patient.objects.filter(company=company).order_by('name')
    return render(request, 'cabinet/patient_list.html', {'patients': patients, 'company': company})

@login_required
def knowledge_base_list(request):
    return render(request, 'cabinet/knowledge_base_list.html')

@login_required
def client_chat(request, patient_id=None):
    patient = get_object_or_404(Patient, id=patient_id, company__owner=request.user)
    return render(request, 'cabinet/client_chat.html', {'patient': patient})

@login_required
def pending_approval(request):
    return render(request, 'cabinet/pending_approval.html')

@login_required
def patient_import_csv(request):
    # Упрощенная версия для восстановления работоспособности
    return render(request, 'cabinet/patient_import_csv.html')
