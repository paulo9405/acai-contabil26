"""
Testes para a Fase 7 — Relatórios de Pedidos.
"""

from datetime import date, time, timedelta
from decimal import Decimal

from django.urls import reverse

from orders.models import Order
from orders.selectors import (
    get_daily_order_totals,
    get_divergences,
    get_liters_sold,
    get_orders_summary,
    get_peak_hours,
    get_sales_by_payment_method,
    get_top_addons,
    get_top_products,
    get_top_sizes,
)
from tests.conftest import (
    OrderFactory,
    OrderItemAddonFactory,
    OrderItemFactory,
    ProductCategoryFactory,
    ProductFactory,
    ProductVariantFactory,
    SizeFactory,
    UserFactory,
)

TODAY = date.today()
YESTERDAY = TODAY - timedelta(1)


# ============================================================================
# Helpers
# ============================================================================


def _order(
    db,
    *,
    order_date=None,
    payment_method=Order.PaymentMethod.PIX,
    total="18.00",
    status=Order.Status.ACTIVE,
):
    user = UserFactory()
    return OrderFactory(
        created_by=user,
        order_date=order_date or TODAY,
        payment_method=payment_method,
        total=Decimal(total),
        status=status,
    )


def _item(
    order,
    *,
    product_name="Produto A",
    size_name="300 ml",
    quantity=1,
    line_total="18.00",
    variant=None,
):
    return OrderItemFactory(
        order=order,
        product_name=product_name,
        size_name=size_name,
        quantity=quantity,
        line_total=Decimal(line_total),
        unit_price=Decimal(line_total),
        variant=variant,
    )


# ============================================================================
# get_orders_summary
# ============================================================================


class TestGetOrdersSummary:
    def test_empty_period(self, db):
        result = get_orders_summary(start_date=TODAY, end_date=TODAY)
        assert result["total_orders"] == 0
        assert result["total_revenue"] == Decimal("0")
        assert result["average_ticket"] == Decimal("0")

    def test_counts_active_orders(self, db):
        _order(db, total="20.00")
        _order(db, total="30.00")
        _order(db, total="10.00", status=Order.Status.CANCELLED)

        result = get_orders_summary(start_date=TODAY, end_date=TODAY)
        assert result["total_orders"] == 2
        assert result["total_revenue"] == Decimal("50.00")
        assert result["average_ticket"] == Decimal("25.00")

    def test_filters_by_date(self, db):
        _order(db, order_date=TODAY, total="18.00")
        _order(db, order_date=YESTERDAY, total="99.00")

        result = get_orders_summary(start_date=TODAY, end_date=TODAY)
        assert result["total_orders"] == 1
        assert result["total_revenue"] == Decimal("18.00")

    def test_date_range_inclusive(self, db):
        start = TODAY - timedelta(3)
        _order(db, order_date=start, total="10.00")
        _order(db, order_date=TODAY, total="20.00")

        result = get_orders_summary(start_date=start, end_date=TODAY)
        assert result["total_orders"] == 2
        assert result["total_revenue"] == Decimal("30.00")


# ============================================================================
# get_sales_by_payment_method
# ============================================================================


class TestGetSalesByPaymentMethod:
    def test_groups_by_method(self, db):
        _order(db, payment_method=Order.PaymentMethod.PIX, total="20.00")
        _order(db, payment_method=Order.PaymentMethod.PIX, total="30.00")
        _order(db, payment_method=Order.PaymentMethod.CASH, total="15.00")

        rows = get_sales_by_payment_method(start_date=TODAY, end_date=TODAY)
        by_method = {r["payment_method"]: r for r in rows}

        assert by_method["PIX"]["total"] == Decimal("50.00")
        assert by_method["PIX"]["count"] == 2
        assert by_method["CASH"]["total"] == Decimal("15.00")
        assert by_method["CASH"]["count"] == 1

    def test_excludes_cancelled(self, db):
        _order(
            db,
            payment_method=Order.PaymentMethod.CARD,
            total="50.00",
            status=Order.Status.CANCELLED,
        )

        rows = get_sales_by_payment_method(start_date=TODAY, end_date=TODAY)
        assert rows == []


# ============================================================================
# get_top_products
# ============================================================================


class TestGetTopProducts:
    def test_ranks_by_quantity(self, db):
        o = _order(db)
        _item(o, product_name="Açaí Oreo", quantity=3, line_total="78.00")
        _item(o, product_name="Açaí Ninho", quantity=1, line_total="22.00")

        rows = get_top_products(start_date=TODAY, end_date=TODAY)
        assert rows[0]["product_name"] == "Açaí Oreo"
        assert rows[0]["total_quantity"] == 3
        assert rows[1]["product_name"] == "Açaí Ninho"

    def test_aggregates_same_product_across_orders(self, db):
        o1 = _order(db)
        o2 = _order(db)
        _item(o1, product_name="Vitamina", quantity=2, line_total="40.00")
        _item(o2, product_name="Vitamina", quantity=1, line_total="20.00")

        rows = get_top_products(start_date=TODAY, end_date=TODAY)
        assert rows[0]["total_quantity"] == 3
        assert rows[0]["total_revenue"] == Decimal("60.00")

    def test_excludes_cancelled_orders(self, db):
        o = _order(db, status=Order.Status.CANCELLED)
        _item(o, product_name="Produto X", quantity=5, line_total="50.00")

        rows = get_top_products(start_date=TODAY, end_date=TODAY)
        assert rows == []


# ============================================================================
# get_top_sizes
# ============================================================================


class TestGetTopSizes:
    def test_ranks_sizes(self, db):
        o = _order(db)
        _item(o, size_name="500 ml", quantity=4, line_total="96.00")
        _item(o, size_name="300 ml", quantity=2, line_total="36.00")
        _item(o, size_name="", quantity=1, line_total="25.00")  # sem tamanho — excluído

        rows = get_top_sizes(start_date=TODAY, end_date=TODAY)
        size_names = [r["size_name"] for r in rows]
        assert "500 ml" in size_names
        assert "300 ml" in size_names
        assert "" not in size_names
        assert rows[0]["size_name"] == "500 ml"


# ============================================================================
# get_liters_sold
# ============================================================================


class TestGetLitersSold:
    def test_calculates_liters_via_variant_size(self, db):
        size = SizeFactory(volume_ml=500)
        cat = ProductCategoryFactory()
        prod = ProductFactory(category=cat)
        variant = ProductVariantFactory(product=prod, size=size)

        o = _order(db)
        OrderItemFactory(
            order=o,
            variant=variant,
            quantity=2,
            size_name="500 ml",
            product_name="Açaí",
            unit_price=Decimal("24.00"),
            addons_total=Decimal("0"),
            line_total=Decimal("48.00"),
        )

        liters = get_liters_sold(start_date=TODAY, end_date=TODAY)
        assert liters == Decimal("1.0")  # 500ml × 2 = 1000ml = 1 L

    def test_zero_when_no_orders(self, db):
        assert get_liters_sold(start_date=TODAY, end_date=TODAY) == Decimal("0")

    def test_excludes_cancelled_orders(self, db):
        size = SizeFactory(volume_ml=1000)
        cat = ProductCategoryFactory()
        prod = ProductFactory(category=cat)
        variant = ProductVariantFactory(product=prod, size=size)

        o = _order(db, status=Order.Status.CANCELLED)
        OrderItemFactory(
            order=o,
            variant=variant,
            quantity=3,
            size_name="1 litro",
            product_name="Açaí",
            unit_price=Decimal("38.00"),
            addons_total=Decimal("0"),
            line_total=Decimal("114.00"),
        )

        assert get_liters_sold(start_date=TODAY, end_date=TODAY) == Decimal("0")

    def test_items_without_variant_excluded(self, db):
        o = _order(db)
        OrderItemFactory(
            order=o,
            variant=None,
            quantity=5,
            size_name="1 litro",
            product_name="Açaí",
            unit_price=Decimal("38.00"),
            addons_total=Decimal("0"),
            line_total=Decimal("190.00"),
        )

        assert get_liters_sold(start_date=TODAY, end_date=TODAY) == Decimal("0")


# ============================================================================
# get_top_addons
# ============================================================================


class TestGetTopAddons:
    def test_ranks_by_count(self, db):
        o = _order(db)
        item = _item(o)
        OrderItemAddonFactory(
            order_item=item, name="Granola", is_included=True, line_total=Decimal("0")
        )
        OrderItemAddonFactory(
            order_item=item, name="Granola", is_included=False, line_total=Decimal("3.00")
        )
        OrderItemAddonFactory(
            order_item=item, name="Nutella", is_included=False, line_total=Decimal("7.50")
        )

        rows = get_top_addons(start_date=TODAY, end_date=TODAY)
        by_name = {r["name"]: r for r in rows}
        assert by_name["Granola"]["count"] == 2
        assert by_name["Nutella"]["count"] == 1
        assert rows[0]["name"] == "Granola"


# ============================================================================
# get_peak_hours
# ============================================================================


class TestGetPeakHours:
    def test_groups_by_hour(self, db):
        user = UserFactory()
        OrderFactory(
            created_by=user, order_date=TODAY, order_time=time(14, 0), total=Decimal("18.00")
        )
        OrderFactory(
            created_by=user, order_date=TODAY, order_time=time(14, 30), total=Decimal("18.00")
        )
        OrderFactory(
            created_by=user, order_date=TODAY, order_time=time(16, 0), total=Decimal("18.00")
        )

        rows = get_peak_hours(start_date=TODAY, end_date=TODAY)
        by_hour = {r["hour"]: r["count"] for r in rows}
        assert by_hour[14] == 2
        assert by_hour[16] == 1

    def test_ordered_by_hour(self, db):
        user = UserFactory()
        OrderFactory(
            created_by=user, order_date=TODAY, order_time=time(18, 0), total=Decimal("18.00")
        )
        OrderFactory(
            created_by=user, order_date=TODAY, order_time=time(11, 0), total=Decimal("18.00")
        )

        rows = get_peak_hours(start_date=TODAY, end_date=TODAY)
        hours = [r["hour"] for r in rows]
        assert hours == sorted(hours)


# ============================================================================
# get_divergences
# ============================================================================


class TestGetDivergences:
    def test_returns_orders_with_divergence(self, db):
        user = UserFactory()
        o = OrderFactory(
            created_by=user,
            order_date=TODAY,
            total=Decimal("18.00"),
            informed_total=Decimal("20.00"),
        )
        result = list(get_divergences(start_date=TODAY, end_date=TODAY))
        assert len(result) == 1
        assert result[0].pk == o.pk

    def test_excludes_matching_total(self, db):
        user = UserFactory()
        OrderFactory(
            created_by=user,
            order_date=TODAY,
            total=Decimal("18.00"),
            informed_total=Decimal("18.00"),
        )
        assert list(get_divergences(start_date=TODAY, end_date=TODAY)) == []

    def test_excludes_null_informed_total(self, db):
        user = UserFactory()
        OrderFactory(created_by=user, order_date=TODAY, total=Decimal("18.00"), informed_total=None)
        assert list(get_divergences(start_date=TODAY, end_date=TODAY)) == []


# ============================================================================
# get_daily_order_totals
# ============================================================================


class TestGetDailyOrderTotals:
    def test_groups_by_date(self, db):
        _order(db, order_date=TODAY, total="18.00")
        _order(db, order_date=TODAY, total="24.00")
        _order(db, order_date=YESTERDAY, total="10.00")

        rows = get_daily_order_totals(start_date=YESTERDAY, end_date=TODAY)
        by_date = {r["order_date"]: r for r in rows}
        assert by_date[TODAY]["total_revenue"] == Decimal("42.00")
        assert by_date[TODAY]["order_count"] == 2
        assert by_date[YESTERDAY]["total_revenue"] == Decimal("10.00")

    def test_ordered_by_date(self, db):
        start = TODAY - timedelta(3)
        for i in range(4):
            _order(db, order_date=start + timedelta(i))

        rows = get_daily_order_totals(start_date=start, end_date=TODAY)
        dates = [r["order_date"] for r in rows]
        assert dates == sorted(dates)


# ============================================================================
# OrderReportView
# ============================================================================


class TestOrderReportView:
    def test_superuser_can_access(self, db, superuser_client):
        url = reverse("order-report")
        resp = superuser_client.get(url + "?period=this_month")
        assert resp.status_code == 200

    def test_operacao_user_denied(self, db):
        from django.contrib.auth.models import Group
        from django.test import Client

        group, _ = Group.objects.get_or_create(name="Operacao")
        user = UserFactory()
        user.groups.add(group)
        client = Client()
        client.force_login(user)
        url = reverse("order-report")
        resp = client.get(url)
        assert resp.status_code == 403

    def test_anonymous_redirects_to_login(self, db, client):
        url = reverse("order-report")
        resp = client.get(url)
        assert resp.status_code == 302

    def test_renders_summary_data(self, db, superuser_client):
        user = UserFactory()
        OrderFactory(created_by=user, order_date=date.today(), total=Decimal("50.00"))

        url = reverse("order-report") + "?period=today"
        resp = superuser_client.get(url)
        assert resp.status_code == 200
        assert resp.context["total_orders"] == 1
        assert resp.context["total_revenue"] == Decimal("50.00")

    def test_invalid_form_still_renders(self, db, superuser_client):
        url = reverse("order-report") + "?period=custom"  # custom sem datas
        resp = superuser_client.get(url)
        assert resp.status_code == 200
        assert "form" in resp.context
