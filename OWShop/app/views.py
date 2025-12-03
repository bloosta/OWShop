"""
Definition of views.
"""

from datetime import datetime
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpRequest
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group, User
from django.views.decorators.http import require_POST

from .forms import CommentForm, BlogForm
from .models import Blog, Comment, Category, Product, Order, OrderItem, Profile

# ---------------- Utility helpers ----------------
def in_group(user, group_name):
    return user.is_authenticated and user.groups.filter(name=group_name).exists()


def is_client(user):
    return in_group(user, 'Client') or user.is_superuser


def is_manager(user):
    return in_group(user, 'Manager') or user.is_superuser

# ---------------- Main pages ----------------
def home(request):
    """Renders the home page with 3 latest news."""
    assert isinstance(request, HttpRequest)
    latest_news = Blog.objects.order_by('-posted')[:3]
    return render(
        request,
        'app/index.html',
        {
            'title': 'Главная',
            'year': datetime.now().year,
            'latest_news': latest_news,
        }
    )


def contact(request):
    """Renders the contact page."""
    assert isinstance(request, HttpRequest)
    address = 'г. Псков, ул. Льва Толстого, 4'
    phones = ['+7 (900) 000-00-00', '+7 (900) 000-00-01']
    developer = 'Капустин А. А.'
    support = 'OWShop@support.com'
    return render(
        request,
        'app/contact.html',
        {
            'title': 'Контакты',
            'address': address,
            'phones': phones,
            'developer': developer,
            'support': support,
            'year': datetime.now().year,
        }
    )


def about(request):
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/about.html',
        {
            'title': 'О нас',
            'message': 'Наша страница о нас',
            'year': datetime.now().year,
        }
    )


def links(request):
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/links.html',
        {
            'title': 'Ссылки',
            'message': 'Полезные ссылки',
            'year': datetime.now().year,
        }
    )


def pool(request):
    submitted = False
    submitted_data = None
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
            submitted_data = [f'{field_names.get(field, field)}: {value}' for field, value in form.cleaned_data.items()]
            for i_idx, i in enumerate(submitted_data):
                if 'Подписка на рассылку' in i:
                    submitted_data[i_idx] = 'Подписка на рассылку: Получать' if 'True' in i else 'Подписка на рассылку: Не получать'
                if 'Способ связи' in i:
                    submitted_data[i_idx] = 'Способ связи: Сообщить по телефону' if 'phone' in i else 'Способ связи: Сообщить на email'
    else:
        form = PoolForm()
    return render(request, 'app/pool.html', {'form': form, 'title': 'Обратная связь', 'submitted': submitted, 'submitted_data': submitted_data})


# ---------------- Blog ----------------
def blog_list(request):
    posts = Blog.objects.order_by('-posted')
    return render(request, 'app/blog_list.html', {'posts': posts})


def blog_detail(request, pk):
    post = get_object_or_404(Blog, pk=pk)
    comments = Comment.objects.filter(post=pk)

    if request.method == 'POST' and request.user.is_authenticated:
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


def newpost(request):
    """Create a new blog post."""
    assert isinstance(request, HttpRequest)

    if request.method == "POST":
        blogform = BlogForm(request.POST, request.FILES)
        if blogform.is_valid():
            blog_f = blogform.save(commit=False)
            blog_f.posted = datetime.now()
            # note: author field name in model may be 'author' or 'autor' — adapt if needed
            try:
                blog_f.author = request.user
            except Exception:
                pass
            blog_f.save()
            return redirect('blog_list')
    else:
        blogform = BlogForm()

    return render(
        request,
        'app/newpost.html',
        {
            'blogform': blogform,
            'title': 'Добавить статью блога',
            'year': datetime.now().year,
        }
    )


def videopost(request):
    return render(request, "app/videopost.html")


# ---------------- Catalog / Product ----------------
def catalog_list(request):
    categories = Category.objects.all()
    return render(request, 'app/catalog.html', {
        'title': 'Каталог',
        'categories': categories,
    })


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = category.products.filter(active=True)
    return render(request, 'app/category.html', {
        'title': f'Категория: {category.name}',
        'category': category,
        'products': products,
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, active=True)
    return render(request, 'app/product_detail.html', {
        'title': product.title,
        'product': product,
    })


# ---------------- Cart / Orders ----------------
CART_SESSION_ID = 'cart'


def _get_cart(request):
    return request.session.get(CART_SESSION_ID, {})


def _save_cart(request, cart):
    request.session[CART_SESSION_ID] = cart
    request.session.modified = True


@login_required(login_url='/login/')
def cart_view(request):
    """
    Показывает содержимое корзины (только для клиентов).
    """
    if not is_client(request.user):
        messages.error(request, "Страница доступна только клиентам.")
        return redirect('home')

    cart = _get_cart(request)
    items = []
    total = Decimal('0.00')
    for pid, data in cart.items():
        try:
            product = Product.objects.get(pk=int(pid))
        except (Product.DoesNotExist, ValueError):
            continue
        qty = int(data.get('qty', 0))
        price = Decimal(data.get('price', str(product.price)))
        line_total = price * qty
        items.append({
            'product': product,
            'quantity': qty,
            'price': price,
            'line_total': line_total
        })
        total += line_total

    return render(request, 'app/cart.html', {
        'title': 'Корзина',
        'items': items,
        'total': total,
    })


@require_POST
@login_required(login_url='/login/')
def add_to_cart(request, slug):
    """
    Добавляет 1 шт. товара в корзину, но только если:
      - пользователь в группе Client или superuser
      - товар активен и есть на складе
      - не превысит текущий stock
    """
    if not is_client(request.user):
        messages.error(request, "Добавлять в корзину могут только клиенты. Пожалуйста, зарегистрируйтесь или обратитесь к администратору.")
        return redirect('product_detail', slug=slug)

    product = get_object_or_404(Product, slug=slug, active=True)

    # проверка наличия
    if product.stock <= 0:
        messages.error(request, f'Товар "{product.title}" отсутствует на складе.')
        return redirect('product_detail', slug=slug)

    cart = _get_cart(request)
    pid = str(product.id)
    current_qty = int(cart.get(pid, {}).get('qty', 0))

    if current_qty + 1 > product.stock:
        messages.error(request, f'Нельзя добавить больше {product.stock} шт. товара "{product.title}".')
        return redirect('product_detail', slug=slug)

    # добавляем/увеличиваем
    item = cart.get(pid, {'qty': 0, 'price': str(product.price)})
    item['qty'] = int(item['qty']) + 1
    item['price'] = str(product.price)
    cart[pid] = item
    _save_cart(request, cart)
    messages.success(request, f'Товар "{product.title}" добавлен в корзину.')
    return redirect('cart_view')


@require_POST
@login_required(login_url='/login/')
def update_cart(request):
    """
    Обновляет корзину; не позволяет установить qty больше, чем product.stock.
    Ожидаются поля вида qty_<product_id>
    """
    cart = _get_cart(request)
    changed = False

    for key, val in request.POST.items():
        if not key.startswith('qty_'):
            continue
        pid = key.split('qty_', 1)[1]
        try:
            qty = int(val)
        except (ValueError, TypeError):
            qty = 0

        # проверяем наличие товара в БД
        try:
            product = Product.objects.get(pk=int(pid))
        except (Product.DoesNotExist, ValueError):
            # удаляем из корзины на всякий случай
            if pid in cart:
                cart.pop(pid, None)
                changed = True
            continue

        if qty <= 0:
            if pid in cart:
                cart.pop(pid, None)
                changed = True
        else:
            if qty > product.stock:
                messages.error(request, f'Товара "{product.title}" в количестве {qty} нет на складе (доступно: {product.stock}).')
                # не применяем это изменение - пользователь должен скорректировать
                continue
            # применяем изменение
            if pid in cart:
                cart[pid]['qty'] = qty
                changed = True

    if changed:
        _save_cart(request, cart)
        messages.success(request, "Корзина обновлена.")
    else:
        messages.info(request, "Изменений в корзине не обнаружено.")
    return redirect('cart_view')


@login_required(login_url='/login/')
def checkout(request):
    """
    Перед созданием заказа проверяем, что по всем позициям хватает stock.
    Если всё ок — создаём Order и OrderItem, уменьшаем stock у Product.
    """
    if not is_client(request.user):
        messages.error(request, "Оформлять заказ могут только клиенты.")
        return redirect('home')

    cart = _get_cart(request)
    if not cart:
        messages.info(request, "Ваша корзина пуста.")
        return redirect('catalog_list')

    # проверка запасов
    for pid, data in cart.items():
        try:
            product = Product.objects.get(pk=int(pid))
        except (Product.DoesNotExist, ValueError):
            messages.error(request, "В корзине найден несуществующий товар. Удалите его.")
            return redirect('cart_view')
        qty = int(data.get('qty', 0))
        if qty <= 0:
            continue
        if product.stock < qty:
            messages.error(request, f'Недостаточно "{product.title}" на складе (доступно: {product.stock}, в корзине: {qty}).')
            return redirect('cart_view')

    # создаём заказ
    order = Order.objects.create(customer=request.user, total_price=Decimal('0.00'))
    total = Decimal('0.00')
    for pid, data in cart.items():
        product = Product.objects.get(pk=int(pid))
        qty = int(data.get('qty', 0))
        price = Decimal(data.get('price', str(product.price)))
        if qty <= 0:
            continue
        OrderItem.objects.create(order=order, product=product, quantity=qty, price=price)
        total += price * qty
        # списываем со склада
        product.stock = max(0, product.stock - qty)
        product.save(update_fields=['stock'])

    order.total_price = total
    order.save()
    # очищаем корзину
    request.session.pop(CART_SESSION_ID, None)
    messages.success(request, f'Заказ #{order.id} создан. Менеджер свяжется с вами.')
    return redirect('my_orders')


# ---------------- Orders (client/manager) ----------------
@login_required
def my_orders(request):
    if not is_client(request.user):
        messages.error(request, "Страница доступна только клиентам.")
        return redirect('home')
    orders = Order.objects.filter(customer=request.user).order_by('-created_at')
    return render(request, 'app/my_orders.html', {'orders': orders, 'title': 'Мои заказы'})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, pk=order_id)

    if request.user != order.customer and not is_manager(request.user) and not request.user.is_superuser:
        messages.error(request, "Просмотр заказа запрещён.")
        return redirect('home')

    can_change_status = request.user.is_authenticated and (is_manager(request.user) or request.user.is_superuser)

    status_list = []
    for val, label in Order.STATUS_CHOICES:
        status_list.append({
            'val': val,
            'label': label,
            'selected': (order.status == val)
        })

    context = {
        'order': order,
        'title': f'Заказ #{order.id}',
        'can_change_status': can_change_status,
        'status_list': status_list,
    }
    return render(request, 'app/order_detail.html', context)


@login_required
@user_passes_test(is_manager)
def manager_orders(request):
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'app/orders_manager.html', {'orders': orders, 'title': 'Заказы (менеджер)'})


@login_required
@user_passes_test(is_manager)
@require_POST
def order_set_status(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    new_status = request.POST.get('status')
    if new_status in dict(Order.STATUS_CHOICES):
        order.status = new_status
        order.save()
        messages.success(request, f'Статус заказа #{order.id} изменён на {order.get_status_display()}.')
    return redirect('order_detail', order_id=order.id)


# ---------------- Registration helper ----------------
def registration(request):
    assert isinstance(request, HttpRequest)
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_staff = False
            user.is_active = True
            user.is_superuser = False
            user.date_joined = datetime.now()
            user.save()
            client_group, _ = Group.objects.get_or_create(name='Client')
            user.groups.add(client_group)
            messages.success(request, 'Регистрация прошла успешно. Вы добавлены в группу "Client".')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'app/registration.html', {'regform': form, 'year': datetime.now().year})
