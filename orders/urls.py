from django.urls import path
from orders.views import OrderCreateView

urlpatterns = [
    path('pedidos/novo/', OrderCreateView.as_view(), name='order-create'),
]
