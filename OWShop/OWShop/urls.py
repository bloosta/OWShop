"""
Definition of urls for OWShop.
"""

from datetime import datetime
from django.urls import path
from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from app import forms, views

from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings
from django.contrib.auth.decorators import login_required
from app import views as app_views                  


urlpatterns = [
    path('', views.home, name='home'),
    path('contact/', views.contact, name='contact'),
    path('registration/', views.registration, name='registration'),
    path('blog/', views.blog_list, name='blog_list'),
    path('blog/<int:pk>/', views.blog_detail, name='blog_detail'),
    path('newpost/', views.newpost, name='newpost'),
    path('videopost/', views.videopost, name='videopost'),
    path('login/',
         LoginView.as_view
         (
             template_name='app/login.html',
             authentication_form=forms.BootstrapAuthenticationForm,
             extra_context=
             {
                 'title': 'Войти',
                 'year' : datetime.now().year,
             }
         ),
         name='login'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('admin/', admin.site.urls),
     path('catalog/', app_views.catalog_list, name='catalog_list'),
    path('category/<slug:slug>/', app_views.category_detail, name='category_detail'),
    path('product/<slug:slug>/', app_views.product_detail, name='product_detail'),

    # корзина и оформление (только для клиентов)
    path('cart/', app_views.cart_view, name='cart_view'),
    path('cart/add/<slug:slug>/', app_views.add_to_cart, name='add_to_cart'),
    path('cart/update/', app_views.update_cart, name='update_cart'),
    path('checkout/', app_views.checkout, name='checkout'),

    # мои заказы (клиент) и заказы для менеджера
    path('my-orders/', app_views.my_orders, name='my_orders'),
    path('orders/', app_views.manager_orders, name='manager_orders'),
    path('orders/<int:order_id>/', app_views.order_detail, name='order_detail'),
    path('orders/<int:order_id>/set-status/', app_views.order_set_status, name='order_set_status'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += staticfiles_urlpatterns()