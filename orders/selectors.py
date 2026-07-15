"""
Selectors for the orders app — read-only queries.
"""

from orders.models import Order


def get_orders_by_date(*, date):
    """
    Retorna todos os pedidos de uma data, ordenados por horário e comanda.
    """
    return (
        Order.objects.filter(order_date=date)
        .select_related('created_by', 'cancelled_by')
        .order_by('order_time', 'comanda_number')
    )


def get_order_detail(*, order_id):
    """
    Retorna um pedido com itens e adicionais pré-carregados.
    """
    return (
        Order.objects.select_related('created_by', 'cancelled_by')
        .prefetch_related(
            'items__addons',
            'items__product',
            'items__variant__size',
        )
        .get(pk=order_id)
    )
