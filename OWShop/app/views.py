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

from .forms import PoolForm, CommentForm, BlogForm
from .models import Blog, Comment, Category, Product, Order, OrderItem, Profile


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

# ---------------- Blog related ----------------
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
    """Create a new blog post (requires login in templates/admin side)."""
    assert isinstance(request, HttpRequest)

    if request.method == "POST":
        blogform = BlogForm(request.POST, request.FILES)
        if blogform.is_valid():
            blog_f = blogform.save(commit=False)
            blog_f.posted = datetime.now()
            blog_f.autor = request.user
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


# ---- Helpers for groups ----
def in_group(user, group_name):
    return user.is_authenticated and user.groups.filter(name=group_name).exists()


def is_client(user):
    return in_group(user, 'Client') or user.is_superuser


def is_manager(user):
    return in_group(user, 'Manager') or user.is_superuser


# ---- Каталог / Товары ----
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


# ---- Корзина в сессии ----
CART_SESSION_ID = 'cart'


def _get_cart(request):
    return request.session.get(CART_SESSION_ID, {})


def _save_cart(request, cart):
    request.session[CART_SESSION_ID] = cart
    request.session.modified = True


@require_POST
@login_required(login_url='/login/')
def add_to_cart(request, slug):
    if not is_client(request.user):
        messages.error(request, "Добавлять в корзину могут только клиенты. Пожалуйста, зарегистрируйтесь или обратитесь к администратору, чтобы получить роль Клиента.")
        return redirect('catalog_list')


    product = get_object_or_404(Product, slug=slug, active=True)
    cart = _get_cart(request)
    item = cart.get(str(product.id), {'qty': 0, 'price': str(product.price)})
    item['qty'] = int(item['qty']) + 1
    item['price'] = str(product.price)
    cart[str(product.id)] = item
    _save_cart(request, cart)
    messages.success(request, f'Товар \"{product.title}\" добавлен в корзину.')
    return redirect('cart_view')


@login_required
def cart_view(request):
    if not is_client(request.user):
        messages.error(request, "Страница доступна только клиентам.")
        return redirect('home')

    cart = _get_cart(request)
    items = []
    total = Decimal('0.00')
    for pid, data in cart.items():
        try:
            product = Product.objects.get(pk=int(pid))
        except Product.DoesNotExist:
            continue
        qty = int(data.get('qty', 0))
        price = Decimal(data.get('price', str(product.price)))
        line = {
            'product': product,
            'quantity': qty,
            'price': price,
            'line_total': price * qty
        }
        total += line['line_total']
        items.append(line)
    return render(request, 'app/cart.html', {
        'title': 'Корзина',
        'items': items,
        'total': total,
    })


@require_POST
@login_required
def update_cart(request):
    cart = _get_cart(request)
    for key, val in request.POST.items():
        if key.startswith('qty_'):
            pid = key.split('qty_')[1]
            try:
                qty = int(val)
            except ValueError:
                qty = 0
            if qty <= 0:
                cart.pop(pid, None)
            else:
                if pid in cart:
                    cart[pid]['qty'] = qty
    _save_cart(request, cart)
    messages.success(request, "Корзина обновлена.")
    return redirect('cart_view')


# ---- Оформление заказа ----
@login_required
def checkout(request):
    if not is_client(request.user):
        messages.error(request, "Оформлять заказ могут только клиенты.")
        return redirect('home')

    cart = _get_cart(request)
    if not cart:
        messages.info(request, "Ваша корзина пуста.")
        return redirect('catalog_list')

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
    order.total_price = total
    order.save()
    request.session.pop(CART_SESSION_ID, None)
    messages.success(request, f'Заказ #{order.id} создан. Менеджер свяжется с вами.')
    return redirect('my_orders')


# ---- Мои заказы (клиент) ----
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


# ---- Заказы для менеджера ----
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


# ---- Регистрация: автоматическое добавление в группу Client ----
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


# End of file
