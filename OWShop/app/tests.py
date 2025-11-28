"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".
"""

import django
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from .models import Category, Product, Order, OrderItem

# TODO: Configure your database in settings.py and sync before running tests.

class ViewTest(TestCase):
    """Tests for the application views."""

    if django.VERSION[:2] >= (1, 7):
        # Django 1.7 requires an explicit setup() when running tests in PTVS
        @classmethod
        def setUpClass(cls):
            super(ViewTest, cls).setUpClass()
            django.setup()

    def test_home(self):
        """Tests the home page."""
        response = self.client.get('/')
        self.assertContains(response, 'Home Page', 1, 200)

    def test_contact(self):
        """Tests the contact page."""
        response = self.client.get('/contact')
        self.assertContains(response, 'Contact', 3, 200)

    def test_about(self):
        """Tests the about page."""
        response = self.client.get('/about')
        self.assertContains(response, 'About', 3, 200)


class ShopFlowTests(TestCase):
    def setUp(self):
        # группы
        self.client_group, _ = Group.objects.get_or_create(name='Client')
        self.manager_group, _ = Group.objects.get_or_create(name='Manager')

        # пользователи
        self.superuser = User.objects.create_superuser(username='admin', email='admin@example.com', password='adminpass')
        self.client_user = User.objects.create_user(username='client', password='clientpass')
        self.client_user.groups.add(self.client_group)
        self.manager_user = User.objects.create_user(username='manager', password='managerpass')
        self.manager_user.groups.add(self.manager_group)
        self.other_user = User.objects.create_user(username='other', password='otherpass')  # не в группе

        # категории и товары
        self.cat = Category.objects.create(name='Категория 1', slug='cat-1', description='Описание категории')
        # создаём 2 товара
        self.prod1 = Product.objects.create(title='Товар 1', slug='prod-1', category=self.cat,
                                           description='Товар 1 описание', price=Decimal('100.00'), stock=10)
        self.prod2 = Product.objects.create(title='Товар 2', slug='prod-2', category=self.cat,
                                           description='Товар 2 описание', price=Decimal('50.00'), stock=5)

        # тестовый клиент из django.test
        self.client_client = Client()
        self.manager_client = Client()
        self.anonymous_client = Client()

    def test_catalog_and_product_pages(self):
        # каталог
        resp = self.anonymous_client.get(reverse('catalog_list'))
        self.assertEqual(resp.status_code, 200)
        # категория
        resp = self.anonymous_client.get(reverse('category_detail', args=[self.cat.slug]))
        self.assertEqual(resp.status_code, 200)
        # продукт
        resp = self.anonymous_client.get(reverse('product_detail', args=[self.prod1.slug]))
        self.assertEqual(resp.status_code, 200)
        # содержимое страницы продукта
        self.assertContains(resp, self.prod1.title)

    def test_registration_assigns_client_group(self):
        # post на регистрацию (используем стандартный view registration)
        resp = self.anonymous_client.post(reverse('registration'), {
            'username': 'newclient',
            'password1': 'strongpass123',
            'password2': 'strongpass123',
        }, follow=True)
        # пользователь создан?
        u = User.objects.filter(username='newclient').first()
        self.assertIsNotNone(u)
        # принадлежит группе Client
        self.assertTrue(u.groups.filter(name='Client').exists())

    def test_add_to_cart_and_checkout_flow(self):
        # логиним клиента
        login_ok = self.client_client.login(username='client', password='clientpass')
        self.assertTrue(login_ok)

        # добавляем товар (POST)
        add_url = reverse('add_to_cart', args=[self.prod1.slug])
        resp = self.client_client.post(add_url, follow=True)
        # редирект или успех на cart_view
        self.assertIn(resp.status_code, (200, 302))

        # сессия содержит cart
        session = self.client_client.session
        cart = session.get('cart', {})
        self.assertTrue(str(self.prod1.id) in cart)

        # просмотр корзины
        resp = self.client_client.get(reverse('cart_view'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.prod1.title)

        # оформление заказа
        resp = self.client_client.get(reverse('checkout'), follow=True)
        # checkout ожидает POST? в реализации у вас GET вызывает checkout and creates order without confirmation? 
        # В нашей реализации checkout - login_required view (GET allowed). После оформления редирект на my_orders.
        self.assertIn(resp.status_code, (200,302))
        # в БД должен появиться заказ
        order = Order.objects.filter(customer=self.client_user).first()
        self.assertIsNotNone(order)
        # позиция заказа
        items = order.items.all()
        self.assertTrue(items.exists())
        self.assertEqual(order.total_price, items[0].line_total())

    def test_update_cart_quantity(self):
        # логин и добавить
        self.client_client.login(username='client', password='clientpass')
        self.client_client.post(reverse('add_to_cart', args=[self.prod2.slug]))
        # обновляем qty до 3
        resp = self.client_client.post(reverse('update_cart'), {'qty_%s' % self.prod2.id: '3'}, follow=True)
        self.assertIn(resp.status_code, (200,302))
        cart = self.client_client.session.get('cart', {})
        self.assertEqual(int(cart[str(self.prod2.id)]['qty']), 3)

    def test_my_orders_access_control(self):
        # неавторизованный — редирект
        resp = self.anonymous_client.get(reverse('my_orders'))
        self.assertIn(resp.status_code, (302, 301))
        # обычный пользователь не в Client (other_user) — при логине должен быть редирект/ошибка
        self.anonymous_client.login(username='other', password='otherpass')
        resp = self.anonymous_client.get(reverse('my_orders'))
        # ожидаем редирект или сообщение об ошибке (view проверяет группу)
        self.assertIn(resp.status_code, (302, 200))
        self.anonymous_client.logout()
        # клиент может
        self.client_client.login(username='client', password='clientpass')
        resp = self.client_client.get(reverse('my_orders'))
        self.assertEqual(resp.status_code, 200)

    def test_manager_orders_and_status_change(self):
        # создаём заказ от client для проверки
        o = Order.objects.create(customer=self.client_user, total_price=Decimal('0.00'))
        OrderItem.objects.create(order=o, product=self.prod1, quantity=2, price=self.prod1.price)
        o.recalc_total()

        # manager доступ
        self.manager_client.login(username='manager', password='managerpass')
        resp = self.manager_client.get(reverse('manager_orders'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, f'Заказ #{o.id}' or str(o.id))

        # тест изменения статуса (POST)
        resp = self.manager_client.post(reverse('order_set_status', args=[o.id]), {'status': Order.STATUS_DONE}, follow=True)
        self.assertIn(resp.status_code, (200,302))
        o.refresh_from_db()
        self.assertEqual(o.status, Order.STATUS_DONE)

    def test_admin_site_accessible_by_superuser(self):
        c = Client()
        self.assertTrue(c.login(username='admin', password='adminpass'))
        resp = c.get('/admin/')
        self.assertEqual(resp.status_code, 200)