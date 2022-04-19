"""App URLs."""

# Django
from django.urls import path

# Views
from app import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='index'),
    path('cart/add', views.AddShoppingCart.as_view(), name='shopping_add'),
    path('checkout', views.CheckoutView.as_view(), name='checkout'),
    
    path('quantity/down/<int:pk>', views.QuantityDowngradeView.as_view(), name='quantity_down'),
    path('quantity/up/<int:pk>', views.QuantityUpgradeView.as_view(), name='quantity_up'),

    path('payment', views.PaymentCheckout.as_view(), name='payment'),
    path('confirmation', views.ConfirmationView.as_view(), name='confirmation'),

    path('orders', views.OrderView.as_view(), name='orders'),
    path('order/<str:code>', views.OrderDetailView.as_view(), name='order_detail'),
]