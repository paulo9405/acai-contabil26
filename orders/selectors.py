"""
Selectors for the orders app — read-only queries.
"""

from decimal import Decimal

from django.db.models import Count, ExpressionWrapper, F, IntegerField, Sum
from django.db.models.functions import ExtractHour

from orders.models import (
    GIFT_CATEGORY_NAME,
    Addon,
    Order,
    OrderItem,
    OrderItemAddon,
    OrderPayment,
    ProductCategory,
    ProductVariant,
)


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
    # Soma sobre as linhas de pagamento para atribuir corretamente os pedidos
    # com pagamento dividido. `count` é o nº de linhas (vendas) por forma.
    return list(
        OrderPayment.objects.filter(
            order__status=Order.Status.ACTIVE,
            order__order_date__gte=start_date,
            order__order_date__lte=end_date,
        )
        .values(payment_method=F("method"))
        .annotate(total=Sum("amount"), count=Count("id"))
        .order_by("-total")
    )


def get_top_products(*, start_date, end_date, limit=10):
    return list(
        OrderItem.objects.filter(
            order__status=Order.Status.ACTIVE,
            order__order_date__gte=start_date,
            order__order_date__lte=end_date,
        )
        .exclude(product__category__name=GIFT_CATEGORY_NAME)
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
        .exclude(product__category__name=GIFT_CATEGORY_NAME)
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
        .exclude(product__category__name=GIFT_CATEGORY_NAME)
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

    # Acréscimos cortesia da aba Brindes (CATALOG na categoria de brindes cujo
    # nome casa com um adicional) — aparecem também aqui, junto dos pagos.
    from_gifts = (
        OrderItem.objects.filter(
            item_type=OrderItem.ItemType.CATALOG,
            product__category__name=GIFT_CATEGORY_NAME,
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
    for row in from_gifts:
        totals[row["product_name"]] = totals.get(row["product_name"], 0) + row["count"]

    return [
        {"name": name, "count": count}
        for name, count in sorted(totals.items(), key=lambda x: -x[1])[:limit]
    ]


def _gift_reference_price(name, size_name, addon_prices):
    """
    Preço de varejo estimado do item equivalente, para valorizar o brinde.
    Não é custo de ingrediente — só uma estimativa do valor de venda.

    - Acréscimos cortesia: preço do adicional de mesmo nome.
    - Açaí brinde (ex.: "Açaí Ninho (brinde)"): variação paga mais barata cujo
      produto casa com o miolo do nome e o mesmo tamanho.
    """
    if name in addon_prices:
        return addon_prices[name]
    core = name.replace("(brinde)", "").strip()
    qs = ProductVariant.objects.filter(active=True, price__gt=0, product__name__icontains=core)
    if size_name:
        qs = qs.filter(size__name=size_name)
    variant = qs.order_by("price").first()
    return variant.price if variant else Decimal("0.00")


def get_gifts_report(*, start_date, end_date):
    """
    Itens dados de graça no período (categoria de brindes): açaí do cartão
    fidelidade e acréscimos cortesia da Quinta Maluca. Retorna, por item, a
    quantidade e o valor estimado (preço de venda), além dos totais.
    """
    rows = (
        OrderItem.objects.filter(
            order__status=Order.Status.ACTIVE,
            order__order_date__gte=start_date,
            order__order_date__lte=end_date,
            item_type=OrderItem.ItemType.CATALOG,
            product__category__name=GIFT_CATEGORY_NAME,
        )
        .values("product_name", "size_name")
        .annotate(quantity=Sum("quantity"))
        .order_by("-quantity", "product_name")
    )

    addon_prices = dict(Addon.objects.values_list("name", "price"))

    items = []
    total_quantity = 0
    total_value = Decimal("0.00")
    for row in rows:
        qty = row["quantity"] or 0
        unit_price = _gift_reference_price(row["product_name"], row["size_name"], addon_prices)
        value = unit_price * qty
        total_quantity += qty
        total_value += value
        items.append(
            {
                "name": row["product_name"],
                "size_name": row["size_name"],
                "quantity": qty,
                "unit_price": unit_price,
                "value": value,
            }
        )

    return {
        "items": items,
        "total_quantity": total_quantity,
        "total_value": total_value,
    }


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
