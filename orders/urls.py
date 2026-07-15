from django.urls import path
from orders.views import (
    OrderCreateView,
    OrderListView,
    OrderDetailView,
    OrderUpdateView,
    OrderCancelView,
)

urlpatterns = [
    path('pedidos/novo/', OrderCreateView.as_view(), name='order-create'),
    path('pedidos/', OrderListView.as_view(), name='order-list'),
    path('pedidos/<str:order_date>/', OrderListView.as_view(), name='order-list-date'),
    path('pedidos/<int:pk>/detalhe/', OrderDetailView.as_view(), name='order-detail'),
    path('pedidos/<int:pk>/editar/', OrderUpdateView.as_view(), name='order-update'),
    path('pedidos/<int:pk>/cancelar/', OrderCancelView.as_view(), name='order-cancel'),
]
