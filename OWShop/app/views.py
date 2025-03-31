"""
Definition of views.
"""

from datetime import datetime
from django.shortcuts import render, redirect
from django.http import HttpRequest
from .forms import PoolForm
from django.contrib.auth.forms import UserCreationForm


def home(request):
    """Renders the home page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/index.html',
        {
            'title':'Главная',
            'year':datetime.now().year,
        }
    )

def contact(request):
    """Renders the contact page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/contact.html',
        {
            'title':'Контакты',
            'message':'Наша страница контактов',
            'year':datetime.now().year,
        }
    )

def about(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/about.html',
        {
            'title':'О нас',
            'message':'Наша страница о нас',
            'year':datetime.now().year,
        }
    )


def links (request):
    assert isinstance(request, HttpRequest)
    return render(
    request,
    'app/links.html',
    {
        'title':'Ссылки',
        'message':'Полезные ссылки',
        'year':datetime.now().year,
    }
)

def pool(request):
    submitted = False
    if request.method == 'POST':
        form = PoolForm(request.POST)
        if form.is_valid():
            submitted = True
            field_names = {
                'rating_overall': 'Общая оценка сайта',
                'rating_design': 'Оценка услуг',
                'rating_content': 'Оценка техподдержки',
                'features_liked': 'Приобретенный товар',
                'features_improve': 'Что можно улучшить',
                'newsletter': 'Подписка на рассылку',
                'contact_method': 'Способ связи',
            }
            submitted_data = [f'{field_names[field]}: {value}' for field, value in form.cleaned_data.items()]
            for i in submitted_data:
                if 'Подписка на рассылку' in i:
                    index = submitted_data.index(i)
                    submitted_data[index] = 'Подписка на рассылку: Получать' if 'True' in i else 'Подписка на рассылку: Не получать'
                if 'Способ связи' in i:
                    index = submitted_data.index(i)
                    submitted_data[index] = 'Способ связи: Сообщить по телефону' if 'phone' in i else 'Способ связи: Сообщить на email'
    else:
        form = PoolForm()
    return render(request, 'app/pool.html', {'form': form, 'title':'Обратная связь', 'submitted': submitted, 'submitted_data': submitted_data if submitted else None})


def registration(request):
    assert isinstance(request, HttpRequest)
    if request.method == "POST": # после отправки формы
        regform = UserCreationForm(request.POST)
        if regform.is_valid(): #валидация полей формы
            reg_f = regform.save(commit=False) # не сохраняем автоматически данные формы
            reg_f.is_staff = False # запрещен вход в административный раздел
            reg_f.is_active = True # активный пользователь
            reg_f.is_superuser = False # не является суперпользователем
            reg_f.date_joined = datetime.now() # дата регистрации
            reg_f.last_login = datetime.now() # дата последней авторизации
            reg_f.save() # сохраняем изменения после добавления данных

            return redirect('home') # переадресация на главную страницу после регистрации
    else:
        regform = UserCreationForm() # создание объекта формы для ввода данных нового пользователя
    return render(
        request,
        'app/registration.html',
        {
            'regform': regform, # передача формы в шаблон веб-страницы
            'year':datetime.now().year,
        }
    )

