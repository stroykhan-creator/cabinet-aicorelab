
# cabinet/views.py
import csv
import io
from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone # Для работы с датами и временем

from .models import Company, Patient # Убедитесь, что Patient импортирован
from .forms import CustomUserCreationForm, CompanyForm, PatientCSVUploadForm

# --- АУТЕНТИФИКАЦИЯ И РЕГИСТРАЦИЯ ---

def custom_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    # TODO: Реализовать логику входа с использованием AuthenticationForm
    # Пример:
    # if request.method == 'POST':
    #     form = AuthenticationForm(request, data=request.POST)
    #     if form.is_valid():
    #         user = form.get_user()
    #         login(request, user)
    #         return redirect('dashboard')
    # else:
    #     form = AuthenticationForm()
    # return render(request, 'cabinet/login.html', {'form': form})
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
            login(request, user)
            messages.success(request, "Аккаунт и компания успешно созданы!")
            return redirect('dashboard')
        else:
            messages.error(request, "Пожалуйста, исправьте ошибки в форме регистрации.")
    else:
        form = CustomUserCreationForm()
    return render(request, 'cabinet/registration.html', {'form': form})

@login_required
def pending_approval(request):
    # Если у пользователя нет компании или она на модерации
    # TODO: Добавить проверку статуса компании
    return render(request, 'cabinet/pending_approval.html') # Предполагаем, что шаблон есть


# --- ЛИЧНЫЙ КАБИНЕТ И ОСНОВНЫЕ ФУНКЦИИ ---

@login_required
def dashboard(request):
    company = Company.objects.filter(owner=request.user).first()
    return render(request, 'cabinet/dashboard.html', {'company': company})

@login_required
def patient_list(request):
    # Получаем компанию текущего пользователя
    company = Company.objects.filter(owner=request.user).first()
    if not company:
        messages.warning(request, "У вас нет активной компании. Создайте ее, чтобы управлять пациентами.")
        return redirect('company_create') # Перенаправляем на создание компании

    patients = Patient.objects.filter(company=company).order_by('name') # Получаем пациентов для этой компании
    return render(request, 'cabinet/patient_list.html', {'patients': patients, 'company': company})

@login_required
def knowledge_base_list(request):
    # TODO: Получить статьи базы знаний, связанные с компанией пользователя
    return render(request, 'cabinet/knowledge_base_list.html')

@login_required
def client_chat(request, patient_id=None):
    # TODO: Реализовать логику чата с конкретным пациентом
    patient = get_object_or_404(Patient, id=patient_id, company__owner=request.user) # Проверка владения
    return render(request, 'cabinet/client_chat.html', {'patient': patient})


# --- УПРАВЛЕНИЕ КОМПАНИЕЙ (ИНСТАНСОМ) ---

@login_required
def company_create(request):
    # Проверяем, есть ли уже компания у пользователя
    if Company.objects.filter(owner=request.user).exists():
        messages.info(request, "У вас уже есть активная компания.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = CompanyForm(request.POST)
        if form.is_valid():
            company = form.save(commit=False)
            company.owner = request.user
            company.save()
            messages.success(request, "Компания успешно создана!")
            return redirect('dashboard')
        else:
            messages.error(request, "Пожалуйста, исправьте ошибки в форме создания компании.")
    else:
        form = CompanyForm()
    return render(request, 'cabinet/company_form.html', {'form': form})


# --- ИМПОРТ ПАЦИЕНТОВ ИЗ CSV ---

@login_required
def patient_import_csv(request):
    company = Company.objects.filter(owner=request.user).first()
    if not company:
        messages.error(request, "Сначала создайте компанию, чтобы импортировать пациентов.")
        return redirect('company_create')

    errors_list = []
    if request.method == 'POST':
        form = PatientCSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            
            if not csv_file.name.lower().endswith('.csv'):
                messages.error(request, "Неверный формат файла. Пожалуйста, загрузите CSV файл.")
                return render(request, 'cabinet/patient_import_csv.html', {'form': form, 'errors_list': errors_list})

            try:
                decoded_file = io.TextIOWrapper(csv_file.file, encoding='utf-8')
                reader = csv.DictReader(decoded_file)
            except Exception as e:
                messages.error(request, f"Ошибка при чтении файла: {e}. Убедитесь, что это корректный CSV файл в кодировке UTF-8.")
                return render(request, 'cabinet/patient_import_csv.html', {'form': form, 'errors_list': errors_list})

            patients_to_create = []
            
            expected_headers = ['first_name', 'last_name', 'email', 'phone', 'date_of_birth', 'notes']
            missing_headers = [h for h in expected_headers if h not in reader.fieldnames]
            if missing_headers:
                messages.error(request, f"В CSV файле отсутствуют обязательные заголовки: {', '.join(missing_headers)}. Ожидаемые: {', '.join(expected_headers)}")
                return render(request, 'cabinet/patient_import_csv.html', {'form': form, 'errors_list': errors_list})

            line_num = 1 # Отсчет строк для отчетов об ошибках (начиная со второй строки файла)

            for row in reader:
                line_num += 1
                patient_data = {
                    'company': company,
                    'status': 'new', # Дефолтный статус
                    'created_at': timezone.now(),
                    'last_contact': None,
                }
                current_row_errors = []

                first_name = row.get('first_name', '').strip()
                last_name = row.get('last_name', '').strip()
                
                patient_data['first_name'] = first_name
                patient_data['last_name'] = last_name
                patient_data['name'] = f"{first_name} {last_name}".strip() if first_name or last_name else "Не указано"

                email = row.get('email', '').strip()
                phone = row.get('phone', '').strip()

                if not phone and not email:
                    current_row_errors.append("Необходимо указать либо телефон, либо email для пациента.")
                
                if email:
                    try:
                        forms.EmailField().clean(email)
                        patient_data['email'] = email
                    except forms.ValidationError:
                        current_row_errors.append(f"Неверный формат email '{email}'.")
                else:
                    patient_data['email'] = None

                patient_data['phone'] = phone if phone else None # Телефон может быть пустым

                date_of_birth_str = row.get('date_of_birth', '').strip()
                if date_of_birth_str:
                    try:
                        patient_data['date_of_birth'] = datetime.strptime(date_of_birth_str, '%Y-%m-%d').date()
                    except ValueError:
                        current_row_errors.append(f"Неверный формат даты рождения '{date_of_birth_str}'. Ожидается YYYY-MM-DD.")
                else:
                    patient_data['date_of_birth'] = None
                
                patient_data['notes'] = row.get('notes', '').strip()


                if current_row_errors:
                    errors_list.append(f"Строка {line_num}: {'; '.join(current_row_errors)}")
                else:
                    patients_to_create.append(Patient(**patient_data))

            if errors_list:
                messages.error(request, f"Обнаружены ошибки при импорте: {len(errors_list)} строк содержат ошибки. Пациенты не были импортированы.")
                return render(request, 'cabinet/patient_import_csv.html', {'form': form, 'errors_list': errors_list})
            
            if patients_to_create:
                try:
                    with transaction.atomic():
                        Patient.objects.bulk_create(patients_to_create)
                    messages.success(request, f"Успешно импортировано {len(patients_to_create)} пациентов.")
                    return redirect('patient_list')
                except Exception as e:
                    messages.error(request, f"Произошла ошибка при сохранении пациентов в базу данных: {e}")
                    return render(request, 'cabinet/patient_import_csv.html', {'form': form, 'errors_list': errors_list})
            else:
                messages.warning(request, "Нет данных для импорта или все строки содержали ошибки.")
                return render(request, 'cabinet/patient_import_csv.html', {'form': form, 'errors_list': errors_list})
        else:
            messages.error(request, "Пожалуйста, исправьте ошибки в форме загрузки файла.")
    else:
        form = PatientCSVUploadForm()
    
    return render(request, 'cabinet/patient_import_csv.html', {'form': form, 'errors_list': errors_list})

