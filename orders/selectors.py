"""
Selectors for the orders app — read-only queries.
"""

from orders.models import Order, ProductCategory, Addon


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


def get_orders_by_date_with_items(*, date):
    """
    Retorna pedidos de uma data com itens pré-carregados (para listagem).
    """
    return (
        Order.objects.filter(order_date=date)
        .select_related('created_by', 'cancelled_by')
        .prefetch_related('items')
        .order_by('order_time', 'comanda_number')
    )


def get_catalog_json():
    """
    Retorna o catálogo ativo como dict estruturado para embedding via json_script.
    Preços são strings para evitar problemas de serialização de Decimal.
    """
    categories = []
    for cat in (
        ProductCategory.objects
        .filter(active=True)
        .prefetch_related('products__variants__size')
        .order_by('sort_order', 'name')
    ):
        products = []
        for prod in cat.products.filter(active=True).order_by('sort_order', 'name'):
            variants = []
            for v in prod.variants.filter(active=True).order_by('size__sort_order'):
                variants.append({
                    'id': v.id,
                    'display': v.size.name if v.size else prod.name,
                    'price': str(v.price),
                    'included_addons_limit': v.included_addons_limit,
                })
            if variants:
                products.append({
                    'id': prod.id,
                    'name': prod.name,
                    'product_type': prod.product_type,
                    'variants': variants,
                })
        if products:
            categories.append({
                'id': cat.id,
                'name': cat.name,
                'kind': cat.kind,
                'products': products,
            })

    addons = [
        {
            'id': a.id,
            'name': a.name,
            'price': str(a.price),
            'is_free_option': a.is_free_option,
        }
        for a in Addon.objects.filter(active=True).order_by('sort_order', 'name')
    ]

    return {'categories': categories, 'addons': addons}
