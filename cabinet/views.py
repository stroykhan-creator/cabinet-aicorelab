# cabinet/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login # Импортируем login для автоматического входа после регистрации
from django.contrib.auth.decorators import login_required # Для защиты страниц
from django.contrib.auth.models import User # Стандартная модель пользователя Django
from .forms import CustomUserCreationForm, CompanyForm # Наши кастомные формы
from .models import Company # Наша модель Company

# Главная страница (дашборд)
@login_required
def dashboard(request):
    # Получаем компанию текущего пользователя, если она есть
    company = None
    if request.user.is_authenticated:
        try:
            # Предполагаем, что у пользователя есть связь с Company через поле owner
            company = try:
    company = Company.objects.get(owner=request.user)
except Exception:
    # fallback: если нет поля owner или компания не найдена, берём первую компанию
    company = Company.objects.first()

        except Company.DoesNotExist:
            company = None # Пользователь есть, но компания еще не создана
        except AttributeError:
            # Если у пользователя нет связи с Company, это может быть, если User не кастомный
            company = None

    context = {
        'company': company,
        # Добавьте другие данные, необходимые для дашборда
    }
    return render(request, 'cabinet/dashboard.html', context)

# Список пациентов
@login_required
def patient_list(request):
    # Здесь будет логика для списка пациентов
    return render(request, 'cabinet/patient_list.html')

# Список базы знаний
@login_required
def knowledge_base_list(request):
    # Здесь будет логика для базы знаний
    return render(request, 'cabinet/knowledge_base_list.html')

# Чат с клиентом
@login_required
def client_chat(request):
    # Здесь будет логика для чата
    return render(request, 'cabinet/client_chat.html')

# Пользовательский вход
# Эту функцию можно использовать для кастомной страницы входа.
# Если вы используете django.contrib.auth.views.LoginView, то эта функция не нужна.
def custom_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard') # Если пользователь уже вошел, перенаправляем на дашборд

    # Здесь должна быть ваша форма для входа (например, AuthenticationForm)
    # Предполагается, что у вас есть login.html
    return render(request, 'cabinet/login.html', {})

# Выход пользователя
# Django имеет встроенный LogoutView, который предпочтительнее.
# Если вы используете его, этот view не нужен.
def custom_logout(request):
    # Если вы хотите сделать свой view для выхода, то он должен выглядеть примерно так:
    from django.contrib.auth import logout
    logout(request)
    return redirect('login')  # Или на главную страницу

    # Регистрация компании и пользователя


def registration_company(request):
    if request.user.is_authenticated:
        return redirect('dashboard')  # Если пользователь уже вошел, не даем регистрироваться снова

    if request.method == 'POST':
        # Создаем экземпляр формы регистрации пользователя с данными из POST-запроса
        form = CustomUserCreationForm(request.POST)

        if form.is_valid():
            # Сохраняем пользователя (без сохранения в базу, так как UserCreationForm делает это)
            user = form.save()

            # Получаем название компании из валидных данных формы
            company_name = form.cleaned_data.get('company_name')

            # Создаем объект компании, связывая его с только что созданным пользователем
            # ВАЖНО: Убедитесь, что у вашей модели Company есть поле 'owner'
            # которое является ForeignKey или OneToOneField на модель User.
            Company.objects.create(name=company_name, owner=user)

            # Автоматически входим в систему после успешной регистрации
            login(request, user)

            # Перенаправляем пользователя на главную страницу после регистрации
            return redirect('dashboard')  # Предполагается, что у вас есть URL с именем 'dashboard'
        else:
            # Если форма невалидна, ошибки будут автоматически переданы в шаблон
            # и форма будет отображена снова с ошибками.
            pass

    else:  # Если это GET-запрос (первое открытие страницы регистрации)
        form = CustomUserCreationForm()

    context = {
        'form': form
    }
    return render(request, 'cabinet/registration.html', context)

    # Страница ожидания одобрения (если такая есть)


@login_required
def pending_approval(request):
    # Логика для страницы ожидания
    return render(request, 'cabinet/pending_approval.html')