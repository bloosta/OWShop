"""
Definition of views.
"""

from datetime import datetime
from django.shortcuts import render
from django.http import HttpRequest
from .forms import PoolForm

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
                'rating_design': 'Оценка дизайна',
                'rating_content': 'Оценка контента',
                'features_liked': 'Что понравилось',
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
    return render(request, 'app/pool.html', {'form': form, 'submitted': submitted, 'submitted_data': submitted_data if submitted else None})
