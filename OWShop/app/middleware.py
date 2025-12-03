# файл: app/middleware.py

from django.shortcuts import redirect
from django.urls import reverse

class AdminOnlyMiddleware:
    """
    Перенаправляет всех, кто не является superuser, с /admin/* на главную.
    Примечание: суперпользователь и автологин админа сможет зайти.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        # проверяем, начинается ли путь с /admin (учитываем и /admin)
        if path.startswith('/admin'):
            user = getattr(request, 'user', None)
            # пропускаем статические/медиа файлы для админки, если нужно
            if not (user and user.is_authenticated and user.is_superuser):
                # редиректим на домашнюю (можно заменить на messages и redirect)
                return redirect('home')
        return self.get_response(request)
