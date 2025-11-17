"""
Definition of models.
"""

from django.db import models
from django.contrib import admin
from datetime import datetime
from django.urls import reverse
from django.contrib.auth.models import User

from django.db import models
from django.contrib import admin
from django.urls import reverse
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal


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



class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Название категории')
    slug = models.SlugField(max_length=120, unique=True, verbose_name='slug')
    description = models.TextField(blank=True, verbose_name='Описание категории')

    class Meta:
        db_table = "Category"
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category_detail', args=[self.slug])


class Product(models.Model):
    title = models.CharField(max_length=150, verbose_name='Название товара')
    slug = models.SlugField(max_length=170, unique=True, verbose_name='slug')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name='Категория')
    description = models.TextField(verbose_name='Описание', blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name='Изображение')
    stock = models.PositiveIntegerField(default=0, verbose_name='На складе')
    active = models.BooleanField(default=True, verbose_name='Активен')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Добавлен')

    class Meta:
        db_table = "Product"
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} ({self.category})'

    def get_absolute_url(self):
        return reverse('product_detail', args=[self.slug])


class Order(models.Model):
    STATUS_NEW = 'new'
    STATUS_PROCESS = 'processing'
    STATUS_DONE = 'done'
    STATUS_CANCEL = 'cancelled'
    STATUS_CHOICES = (
        (STATUS_NEW, 'Новый'),
        (STATUS_PROCESS, 'В обработке'),
        (STATUS_DONE, 'Выполнен'),
        (STATUS_CANCEL, 'Отменён'),
    )

    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', verbose_name='Клиент')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW, verbose_name='Статус')
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name='Итоговая сумма')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлён')

    class Meta:
        db_table = "Order"
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ['-created_at']

    def __str__(self):
        return f'Заказ #{self.id} — {self.customer} — {self.get_status_display()}'

    def recalc_total(self):
        total = Decimal('0.00')
        for item in self.items.all():
            total += item.line_total()
        self.total_price = total
        self.save(update_fields=['total_price'])


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='Заказ')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name='Товар')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Количество')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена на момент заказа')

    class Meta:
        db_table = "OrderItem"
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказов"

    def __str__(self):
        return f'{self.product.title} x{self.quantity}'

    def line_total(self):
        return Decimal(self.price) * Decimal(self.quantity)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name='Профиль')
    phone = models.CharField(max_length=30, blank=True, verbose_name='Телефон')
    address = models.TextField(blank=True, verbose_name='Адрес')
    # Дополнительные поля: баланс, примечания и т.п.
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')

    class Meta:
        db_table = "Profile"
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"

    def __str__(self):
        return f'Профиль {self.user.username}'


# Сигнал для автоматического создания Profile при создании User
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        instance.profile.save()


# --- Admin registration для новых моделей ---
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ('price',)
    extra = 0

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'status', 'total_price', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('customer__username', 'id')
    inlines = [OrderItemInline]
    readonly_fields = ('created_at', 'updated_at')

admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Order, OrderAdmin)
admin.site.register(Profile)