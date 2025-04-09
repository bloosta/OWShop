"""
Definition of views.
"""

from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpRequest
from .forms import PoolForm
from django.contrib.auth.forms import UserCreationForm
from django.db import models
from .models import Blog, Comment
from .forms import CommentForm


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


def blog_list(request):
    posts = Blog.objects.all()
    return render(request, 'app/blog_list.html', {'posts': posts})

def blog_detail(request, pk):
    post = get_object_or_404(Blog, pk=pk)
    comments = Comment.objects.filter(post=pk)

    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment_f = form.save(commit=False)
            comment_f.author = request.user
            comment_f.date = datetime.now()
            comment_f.post = post
            comment_f.save()

            return redirect('blog_detail', pk=post.id)
    else:
        form = CommentForm()
    return render(
        request,
        'app/blog_detail.html',
        {
            'post': post,
            'comments': comments,
            'form': form,
            'year': datetime.now().year
        }
    )