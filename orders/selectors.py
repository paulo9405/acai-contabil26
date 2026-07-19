"""
Selectors for the orders app — read-only queries.
"""

from decimal import Decimal

from django.db.models import Count, ExpressionWrapper, F, IntegerField, Sum
from django.db.models.functions import ExtractHour

from orders.models import Addon, Order, OrderItem, OrderItemAddon, ProductCategory


def get_orders_by_date(*, date):
    """
    Retorna todos os pedidos de uma data, ordenados por horário e comanda.
    """
    return (
        Order.objects.filter(order_date=date)
        .select_related("created_by", "cancelled_by")
        .order_by("order_time", "comanda_number")
    )


def get_order_detail(*, order_id):
    """
    Retorna um pedido com itens e adicionais pré-carregados.
    """
    return (
        Order.objects.select_related("created_by", "cancelled_by")
        .prefetch_related(
            "items__addons",
            "items__product",
            "items__variant__size",
        )
        .get(pk=order_id)
    )


def get_orders_by_date_with_items(*, date):
    """
    Retorna pedidos de uma data com itens pré-carregados (para listagem).
    """
    return (
        Order.objects.filter(order_date=date)
        .select_related("created_by", "cancelled_by")
        .prefetch_related("items")
        .order_by("order_time", "comanda_number")
    )


def _active_orders_qs(start_date, end_date):
    return Order.objects.filter(
        status=Order.Status.ACTIVE,
        order_date__gte=start_date,
        order_date__lte=end_date,
    )


def get_orders_summary(*, start_date, end_date):
    agg = _active_orders_qs(start_date, end_date).aggregate(
        total_orders=Count("id"),
        total_revenue=Sum("total"),
    )
    total_orders = agg["total_orders"] or 0
    total_revenue = agg["total_revenue"] or Decimal("0")
    avg_ticket = (total_revenue / total_orders) if total_orders > 0 else Decimal("0")
    return {
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "average_ticket": avg_ticket,
    }


def get_sales_by_payment_method(*, start_date, end_date):
    return list(
        _active_orders_qs(start_date, end_date)
        .values("payment_method")
        .annotate(total=Sum("total"), count=Count("id"))
        .order_by("-total")
    )


def get_top_products(*, start_date, end_date, limit=10):
    return list(
        OrderItem.objects.filter(
            order__status=Order.Status.ACTIVE,
            order__order_date__gte=start_date,
            order__order_date__lte=end_date,
        )
        .values("product_name")
        .annotate(
            total_quantity=Sum("quantity"),
            total_revenue=Sum("line_total"),
        )
        .order_by("-total_quantity")[:limit]
    )


def get_top_sizes(*, start_date, end_date, limit=10):
    return list(
        OrderItem.objects.filter(
            order__status=Order.Status.ACTIVE,
            order__order_date__gte=start_date,
            order__order_date__lte=end_date,
            size_name__gt="",
        )
        .values("size_name")
        .annotate(total_quantity=Sum("quantity"))
        .order_by("-total_quantity")[:limit]
    )


def get_liters_sold(*, start_date, end_date):
    result = (
        OrderItem.objects.filter(
            order__status=Order.Status.ACTIVE,
            order__order_date__gte=start_date,
            order__order_date__lte=end_date,
            variant__isnull=False,
            variant__size__isnull=False,
        )
        .annotate(
            item_ml=ExpressionWrapper(
                F("variant__size__volume_ml") * F("quantity"),
                output_field=IntegerField(),
            )
        )
        .aggregate(total_ml=Sum("item_ml"))
    )
    total_ml = result["total_ml"] or 0
    return Decimal(str(total_ml)) / Decimal("1000")


def get_top_addons(*, start_date, end_date, limit=10):
    date_filter = dict(
        order__status=Order.Status.ACTIVE,
        order__order_date__gte=start_date,
        order__order_date__lte=end_date,
    )

    # Adicionais do Monte seu Açaí (vinculados via OrderItemAddon)
    from_linked = (
        OrderItemAddon.objects.filter(
            order_item__order__status=Order.Status.ACTIVE,
            order_item__order__order_date__gte=start_date,
            order_item__order__order_date__lte=end_date,
        )
        .values("name")
        .annotate(count=Count("id"))
    )

    # Acréscimos avulsos do picker (MANUAL OrderItems cujo nome é um addon cadastrado)
    addon_names = set(Addon.objects.filter(active=True).values_list("name", flat=True))
    from_picker = (
        OrderItem.objects.filter(
            item_type=OrderItem.ItemType.MANUAL,
            product_name__in=addon_names,
            **date_filter,
        )
        .values("product_name")
        .annotate(count=Count("id"))
    )

    totals: dict[str, int] = {}
    for row in from_linked:
        totals[row["name"]] = totals.get(row["name"], 0) + row["count"]
    for row in from_picker:
        totals[row["product_name"]] = totals.get(row["product_name"], 0) + row["count"]

    return [
        {"name": name, "count": count}
        for name, count in sorted(totals.items(), key=lambda x: -x[1])[:limit]
    ]


def get_peak_hours(*, start_date, end_date):
    return list(
        _active_orders_qs(start_date, end_date)
        .annotate(hour=ExtractHour("order_time"))
        .values("hour")
        .annotate(count=Count("id"))
        .order_by("hour")
    )


def get_divergences(*, start_date, end_date):
    return (
        _active_orders_qs(start_date, end_date)
        .filter(informed_total__isnull=False)
        .exclude(informed_total=F("total"))
        .select_related("created_by")
        .order_by("order_date", "order_time")
    )


def get_daily_order_totals(*, start_date, end_date):
    return list(
        _active_orders_qs(start_date, end_date)
        .values("order_date")
        .annotate(
            total_revenue=Sum("total"),
            order_count=Count("id"),
        )
        .order_by("order_date")
    )


def get_catalog_json():
    """
    Retorna o catálogo ativo como dict estruturado para embedding via json_script.
    Preços são strings para evitar problemas de serialização de Decimal.
    """
    categories = []
    for cat in (
        ProductCategory.objects.filter(active=True)
        .prefetch_related("products__variants__size")
        .order_by("sort_order", "name")
    ):
        products = []
        for prod in cat.products.filter(active=True).order_by("sort_order", "name"):
            variants = []
            for v in prod.variants.filter(active=True).order_by("size__sort_order"):
                variants.append(
                    {
                        "id": v.id,
                        "display": v.size.name if v.size else prod.name,
                        "price": str(v.price),
                        "included_addons_limit": v.included_addons_limit,
                    }
                )
            if variants:
                products.append(
                    {
                        "id": prod.id,
                        "name": prod.name,
                        "product_type": prod.product_type,
                        "variants": variants,
                    }
                )
        if products:
            categories.append(
                {
                    "id": cat.id,
                    "name": cat.name,
                    "kind": cat.kind,
                    "products": products,
                }
            )

    addons = [
        {
            "id": a.id,
            "name": a.name,
            "price": str(a.price),
            "is_free_option": a.is_free_option,
        }
        for a in Addon.objects.filter(active=True).order_by("sort_order", "name")
    ]

    return {"categories": categories, "addons": addons}
