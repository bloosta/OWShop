"""
Definition of models.
"""

from django.db import models
from django.contrib import admin
from datetime import datetime
from django.urls import reverse
from django.contrib.auth.models import User


# Create your models here.

class Blog(models.Model):
    title = models.CharField(max_length=100, unique_for_date="posted", verbose_name="Заголовок")
    description = models.TextField(verbose_name="Краткое содержание")
    content = models.TextField(verbose_name="Полное содержание")
    posted = models.DateTimeField(default=datetime.now, db_index=True, verbose_name="Опубликована")
    author = models.ForeignKey(User, null=True, blank=True, on_delete = models.SET_NULL, verbose_name = "Автор")
    image = models.FileField(default='temp.jpg', verbose_name="Путь к картинке")

    def get_absolute_url(self):
        return reverse("blogpost", args=[str(self.id)])
    
    def __str__(self):
        return self.title
    
    class Meta:
        db_table = "Posts"
        ordering = ["-posted"]
        verbose_name = "статья блога"
        verbose_name_plural = "статьи блога"

admin.site.register(Blog)

class Comment(models.Model):
     text = models.TextField(verbose_name="Текст комментария")
     date = models.DateTimeField(default=datetime.now, db_index=True, verbose_name="Дата комментария")
     author = models.ForeignKey(User, null=True, blank=True, verbose_name=("Автор комментария"), on_delete=models.CASCADE)
     post = models.ForeignKey(Blog, verbose_name=("Статья комментария"), on_delete=models.CASCADE)
 
     def __str__(self):
         return f'Комментарий {self.id} {self.author} к {self.post}'
     
     class Meta:
         db_table = "Comment"
         ordering = ["-date"]
         verbose_name = "Комментарий"
         verbose_name_plural = "Комментарии"


admin.site.register(Comment)