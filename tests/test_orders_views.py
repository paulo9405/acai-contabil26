"""
Testes para as views do app orders — Fases 4 e 5.
"""

from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth.models import Group
from django.urls import reverse

from orders.models import Order
from tests.conftest import (
    AddonFactory,
    DailyClosingFactory,
    OrderFactory,
    ProductCategoryFactory,
    ProductFactory,
    ProductVariantFactory,
    SizeFactory,
    UserFactory,
)

# ============================================================================
# Helpers
# ============================================================================


def _make_operacao_user(db):
    group, _ = Group.objects.get_or_create(name="Operacao")
    user = UserFactory()
    user.groups.add(group)
    return user


def _operacao_client(db):
    from django.test import Client

    user = _make_operacao_user(db)
    client = Client()
    client.force_login(user)
    return client, user


def _superuser_client(db):
    from django.test import Client

    user = UserFactory(is_superuser=True, is_staff=True)
    client = Client()
    client.force_login(user)
    return client


def _build_your_own_variant(db):
    cat = ProductCategoryFactory(kind="BUILD_YOUR_OWN")
    prod = ProductFactory(category=cat, product_type="BUILD_YOUR_OWN")
    size = SizeFactory(name="300 ml", volume_ml=300)
    return ProductVariantFactory(
        product=prod, size=size, price=Decimal("18.00"), included_addons_limit=2
    )


def _standard_variant(db):
    cat = ProductCategoryFactory(kind="STANDARD")
    prod = ProductFactory(category=cat, product_type="STANDARD")
    size = SizeFactory(name="500 ml", volume_ml=500)
    return ProductVariantFactory(product=prod, size=size, price=Decimal("24.00"))


# ============================================================================
# GET — permissões
# ============================================================================


@pytest.mark.django_db
class TestOrderCreateViewPermissions:
    def test_redirect_if_not_logged_in(self):
        from django.test import Client

        response = Client().get(reverse("order-create"))
        assert response.status_code == 302
        assert "/accounts/login/" in response["Location"]

    def test_forbidden_for_regular_user(self, authenticated_client):
        response = authenticated_client.get(reverse("order-create"))
        assert response.status_code == 403

    def test_allowed_for_operacao_user(self, db):
        client, _ = _operacao_client(db)
        response = client.get(reverse("order-create"))
        assert response.status_code == 200

    def test_allowed_for_superuser(self, superuser_client):
        response = superuser_client.get(reverse("order-create"))
        assert response.status_code == 200

    def test_template_used(self, db):
        client, _ = _operacao_client(db)
        response = client.get(reverse("order-create"))
        assert "orders/order_form.html" in [t.name for t in response.templates]

    def test_context_contains_catalog(self, db):
        client, _ = _operacao_client(db)
        response = client.get(reverse("order-create"))
        assert "catalog_json" in response.context
        assert "categories" in response.context["catalog_json"]
        assert "addons" in response.context["catalog_json"]

    def test_context_contains_today(self, db):
        client, _ = _operacao_client(db)
        response = client.get(reverse("order-create"))
        assert "today" in response.context
        assert response.context["today"] == date.today().isoformat()


# ============================================================================
# POST — validação de campos obrigatórios
# ============================================================================


@pytest.mark.django_db
class TestOrderCreateViewValidation:
    def _post(self, db, data):
        client, _ = _operacao_client(db)
        return client.post(reverse("order-create"), data)

    def test_missing_comanda_number_shows_error(self, db):
        variant = _standard_variant(db)
        response = self._post(
            db,
            {
                "order_date": "2026-07-15",
                "order_time": "14:30",
                "payment_method": "PIX",
                "item_variant_id[]": [str(variant.id)],
                "item_quantity[]": ["1"],
                "item_addon_ids[]": [""],
            },
        )
        assert response.status_code == 200
        errors = response.context["form_errors"]
        assert any("comanda" in e.lower() for e in errors)

    def test_missing_order_time_shows_error(self, db):
        variant = _standard_variant(db)
        response = self._post(
            db,
            {
                "comanda_number": "5",
                "order_date": "2026-07-15",
                "payment_method": "PIX",
                "item_variant_id[]": [str(variant.id)],
                "item_quantity[]": ["1"],
                "item_addon_ids[]": [""],
            },
        )
        assert response.status_code == 200
        errors = response.context["form_errors"]
        assert any("horário" in e.lower() for e in errors)

    def test_no_items_shows_error(self, db):
        response = self._post(
            db,
            {
                "comanda_number": "5",
                "order_date": "2026-07-15",
                "order_time": "14:30",
                "payment_method": "PIX",
            },
        )
        assert response.status_code == 200
        errors = response.context["form_errors"]
        assert any("item" in e.lower() for e in errors)

    def test_missing_payment_method_shows_error(self, db):
        variant = _standard_variant(db)
        response = self._post(
            db,
            {
                "comanda_number": "5",
                "order_date": "2026-07-15",
                "order_time": "14:30",
                "item_variant_id[]": [str(variant.id)],
                "item_quantity[]": ["1"],
                "item_addon_ids[]": [""],
            },
        )
        assert response.status_code == 200
        errors = response.context["form_errors"]
        assert any("pagamento" in e.lower() for e in errors)


# ============================================================================
# POST — criação com sucesso
# ============================================================================


@pytest.mark.django_db
class TestOrderCreateViewSuccess:
    def test_creates_order_with_single_item(self, db):
        client, user = _operacao_client(db)
        variant = _standard_variant(db)

        response = client.post(
            reverse("order-create"),
            {
                "comanda_number": "10",
                "order_date": "2026-07-15",
                "order_time": "16:30",
                "payment_method": "PIX",
                "item_variant_id[]": [str(variant.id)],
                "item_quantity[]": ["1"],
                "item_addon_ids[]": [""],
            },
        )

        assert response.status_code == 302
        order = Order.objects.get(comanda_number="10")
        assert response["Location"] == reverse("order-detail", kwargs={"pk": order.pk})

        assert order.status == Order.Status.ACTIVE
        assert order.total == Decimal("24.00")
        assert order.created_by == user
        assert order.items.count() == 1

    def test_creates_order_with_multiple_items(self, db):
        client, _ = _operacao_client(db)
        variant1 = _standard_variant(db)
        variant2 = _standard_variant(db)

        response = client.post(
            reverse("order-create"),
            {
                "comanda_number": "11",
                "order_date": "2026-07-15",
                "order_time": "17:00",
                "payment_method": "CASH",
                "item_variant_id[]": [str(variant1.id), str(variant2.id)],
                "item_quantity[]": ["1", "2"],
                "item_addon_ids[]": ["", ""],
            },
        )

        assert response.status_code == 302
        order = Order.objects.get(comanda_number="11")
        assert order.items.count() == 2
        expected_total = variant1.price + variant2.price * 2
        assert order.total == expected_total

    def test_creates_order_with_addons_build_your_own(self, db):
        client, _ = _operacao_client(db)
        variant = _build_your_own_variant(db)
        addon1 = AddonFactory(price=Decimal("3.00"), is_free_option=True)
        addon2 = AddonFactory(price=Decimal("3.50"), is_free_option=True)
        addon3 = AddonFactory(price=Decimal("4.00"), is_free_option=False)

        response = client.post(
            reverse("order-create"),
            {
                "comanda_number": "12",
                "order_date": "2026-07-15",
                "order_time": "15:00",
                "payment_method": "CARD",
                "item_variant_id[]": [str(variant.id)],
                "item_quantity[]": ["1"],
                "item_addon_ids[]": [f"{addon1.id},{addon2.id},{addon3.id}"],
            },
        )

        assert response.status_code == 302
        order = Order.objects.get(comanda_number="12")
        item = order.items.first()
        # 2 adicionais grátis (limit=2), 1 pago (R$ 4,00)
        assert item.addons_total == Decimal("4.00")
        assert order.total == Decimal("22.00")  # 18.00 + 4.00

    def test_informed_total_divergence_does_not_block(self, db):
        client, _ = _operacao_client(db)
        variant = _standard_variant(db)

        response = client.post(
            reverse("order-create"),
            {
                "comanda_number": "13",
                "order_date": "2026-07-15",
                "order_time": "10:00",
                "payment_method": "PIX",
                "informed_total": "30.00",
                "item_variant_id[]": [str(variant.id)],
                "item_quantity[]": ["1"],
                "item_addon_ids[]": [""],
            },
        )

        assert response.status_code == 302
        order = Order.objects.get(comanda_number="13")
        assert order.total == Decimal("24.00")
        assert order.informed_total == Decimal("30.00")
        assert order.has_total_divergence

    def test_success_message_shown(self, db):
        client, _ = _operacao_client(db)
        variant = _standard_variant(db)

        client.post(
            reverse("order-create"),
            {
                "comanda_number": "14",
                "order_date": "2026-07-15",
                "order_time": "11:00",
                "payment_method": "PIX",
                "item_variant_id[]": [str(variant.id)],
                "item_quantity[]": ["1"],
                "item_addon_ids[]": [""],
            },
        )

        order = Order.objects.get(comanda_number="14")
        # Verificar que o pedido foi criado com sucesso
        assert order.status == Order.Status.ACTIVE

    def test_notes_saved(self, db):
        client, _ = _operacao_client(db)
        variant = _standard_variant(db)

        client.post(
            reverse("order-create"),
            {
                "comanda_number": "15",
                "order_date": "2026-07-15",
                "order_time": "12:00",
                "payment_method": "PIX",
                "notes": "Sem granola",
                "item_variant_id[]": [str(variant.id)],
                "item_quantity[]": ["1"],
                "item_addon_ids[]": [""],
            },
        )

        order = Order.objects.get(comanda_number="15")
        assert order.notes == "Sem granola"

    def test_same_comanda_number_allowed_twice(self, db):
        client, _ = _operacao_client(db)
        variant = _standard_variant(db)

        data = {
            "comanda_number": "1",
            "order_date": "2026-07-15",
            "order_time": "10:00",
            "payment_method": "PIX",
            "item_variant_id[]": [str(variant.id)],
            "item_quantity[]": ["1"],
            "item_addon_ids[]": [""],
        }
        client.post(reverse("order-create"), data)
        data["order_time"] = "11:00"
        client.post(reverse("order-create"), data)

        assert Order.objects.filter(comanda_number="1").count() == 2


# ============================================================================
# ORDER LIST VIEW — Fase 5
# ============================================================================


@pytest.mark.django_db
class TestOrderListView:
    def test_forbidden_for_regular_user(self, authenticated_client):
        response = authenticated_client.get(reverse("order-list"))
        assert response.status_code == 403

    def test_allowed_for_operacao_user(self, db):
        client, _ = _operacao_client(db)
        response = client.get(reverse("order-list"))
        assert response.status_code == 200

    def test_defaults_to_today(self, db):
        client, user = _operacao_client(db)
        response = client.get(reverse("order-list"))
        assert response.status_code == 200
        assert response.context["order_date"] == date.today()

    def test_shows_orders_for_date(self, db):
        client, user = _operacao_client(db)
        today = date.today()
        order = OrderFactory(created_by=user, order_date=today)
        response = client.get(reverse("order-list"))
        assert order in list(response.context["orders"])

    def test_date_navigation_via_url(self, db):
        client, _ = _operacao_client(db)
        response = client.get(reverse("order-list-date", kwargs={"order_date": "2026-07-01"}))
        assert response.status_code == 200
        from datetime import date as d

        assert response.context["order_date"] == d(2026, 7, 1)

    def test_invalid_date_falls_back_to_today(self, db):
        client, _ = _operacao_client(db)
        response = client.get(reverse("order-list-date", kwargs={"order_date": "naoadata"}))
        assert response.status_code == 200
        assert response.context["order_date"] == date.today()

    def test_cancelled_orders_shown_with_badge(self, db):
        client, user = _operacao_client(db)
        today = date.today()
        order = OrderFactory(created_by=user, order_date=today, status=Order.Status.CANCELLED)
        response = client.get(reverse("order-list"))
        orders = list(response.context["orders"])
        assert order in orders

    def test_edit_button_hidden_when_day_closed_for_operacao(self, db):
        client, user = _operacao_client(db)
        today = date.today()
        DailyClosingFactory(date=today)
        response = client.get(reverse("order-list"))
        assert response.context["can_edit"] is False

    def test_edit_button_visible_for_superuser_even_after_close(self, db):
        client = _superuser_client(db)
        today = date.today()
        DailyClosingFactory(date=today)
        response = client.get(reverse("order-list"))
        assert response.context["can_edit"] is True

    def test_cancel_button_only_for_superuser(self, db):
        client_op, _ = _operacao_client(db)
        client_su = _superuser_client(db)
        response_op = client_op.get(reverse("order-list"))
        response_su = client_su.get(reverse("order-list"))
        assert response_op.context["can_cancel"] is False
        assert response_su.context["can_cancel"] is True

    def test_same_comanda_number_two_orders_both_listed(self, db):
        client, user = _operacao_client(db)
        today = date.today()
        OrderFactory(created_by=user, order_date=today, comanda_number="1")
        OrderFactory(created_by=user, order_date=today, comanda_number="1")
        response = client.get(reverse("order-list"))
        comanda_1_orders = [o for o in response.context["orders"] if o.comanda_number == "1"]
        assert len(comanda_1_orders) == 2


# ============================================================================
# ORDER DETAIL VIEW — Fase 5
# ============================================================================


@pytest.mark.django_db
class TestOrderDetailView:
    def test_forbidden_for_regular_user(self, db, authenticated_client):
        user = UserFactory()
        order = OrderFactory(created_by=user)
        response = authenticated_client.get(reverse("order-detail", kwargs={"pk": order.pk}))
        assert response.status_code == 403

    def test_allowed_for_operacao_user(self, db):
        client, user = _operacao_client(db)
        order = OrderFactory(created_by=user)
        response = client.get(reverse("order-detail", kwargs={"pk": order.pk}))
        assert response.status_code == 200

    def test_404_for_nonexistent_order(self, db):
        client, _ = _operacao_client(db)
        response = client.get(reverse("order-detail", kwargs={"pk": 99999}))
        assert response.status_code == 404

    def test_can_edit_true_when_day_open(self, db):
        client, user = _operacao_client(db)
        order = OrderFactory(created_by=user)
        response = client.get(reverse("order-detail", kwargs={"pk": order.pk}))
        assert response.context["can_edit"] is True

    def test_can_edit_false_when_day_closed_for_operacao(self, db):
        client, user = _operacao_client(db)
        today = date.today()
        order = OrderFactory(created_by=user, order_date=today)
        DailyClosingFactory(date=today)
        response = client.get(reverse("order-detail", kwargs={"pk": order.pk}))
        assert response.context["can_edit"] is False

    def test_can_cancel_false_for_operacao(self, db):
        client, user = _operacao_client(db)
        order = OrderFactory(created_by=user)
        response = client.get(reverse("order-detail", kwargs={"pk": order.pk}))
        assert response.context["can_cancel"] is False

    def test_can_cancel_true_for_superuser(self, db):
        client = _superuser_client(db)
        user = UserFactory()
        order = OrderFactory(created_by=user)
        response = client.get(reverse("order-detail", kwargs={"pk": order.pk}))
        assert response.context["can_cancel"] is True


# ============================================================================
# ORDER UPDATE VIEW — Fase 5
# ============================================================================


@pytest.mark.django_db
class TestOrderUpdateView:
    def test_forbidden_for_regular_user(self, db, authenticated_client):
        user = UserFactory()
        order = OrderFactory(created_by=user)
        response = authenticated_client.get(reverse("order-update", kwargs={"pk": order.pk}))
        assert response.status_code == 403

    def test_allowed_for_operacao_when_day_open(self, db):
        client, user = _operacao_client(db)
        order = OrderFactory(created_by=user)
        response = client.get(reverse("order-update", kwargs={"pk": order.pk}))
        assert response.status_code == 200

    def test_forbidden_for_operacao_when_day_closed(self, db):
        client, user = _operacao_client(db)
        today = date.today()
        order = OrderFactory(created_by=user, order_date=today)
        DailyClosingFactory(date=today)
        response = client.get(reverse("order-update", kwargs={"pk": order.pk}))
        assert response.status_code == 403

    def test_allowed_for_superuser_even_when_day_closed(self, db):
        client = _superuser_client(db)
        user = UserFactory()
        today = date.today()
        order = OrderFactory(created_by=user, order_date=today)
        DailyClosingFactory(date=today)
        response = client.get(reverse("order-update", kwargs={"pk": order.pk}))
        assert response.status_code == 200

    def test_forbidden_for_cancelled_order(self, db):
        client, user = _operacao_client(db)
        order = OrderFactory(created_by=user, status=Order.Status.CANCELLED)
        response = client.get(reverse("order-update", kwargs={"pk": order.pk}))
        assert response.status_code == 403

    def test_post_updates_header_fields(self, db):
        client, user = _operacao_client(db)
        order = OrderFactory(created_by=user, comanda_number="5", payment_method="PIX")
        response = client.post(
            reverse("order-update", kwargs={"pk": order.pk}),
            {
                "comanda_number": "10",
                "order_time": "18:00",
                "payment_method": "CASH",
                "notes": "Sem granola",
            },
        )
        assert response.status_code == 302
        order.refresh_from_db()
        assert order.comanda_number == "10"
        assert order.payment_method == "CASH"
        assert order.notes == "Sem granola"

    def test_post_missing_comanda_shows_error(self, db):
        client, user = _operacao_client(db)
        order = OrderFactory(created_by=user)
        response = client.post(
            reverse("order-update", kwargs={"pk": order.pk}),
            {
                "comanda_number": "",
                "order_time": "18:00",
                "payment_method": "PIX",
            },
        )
        assert response.status_code == 200

    def test_post_clears_informed_total_when_empty(self, db):
        client, user = _operacao_client(db)
        from decimal import Decimal

        order = OrderFactory(created_by=user, informed_total=Decimal("30.00"))
        client.post(
            reverse("order-update", kwargs={"pk": order.pk}),
            {
                "comanda_number": order.comanda_number,
                "order_time": "14:00",
                "payment_method": order.payment_method,
                "informed_total": "",
            },
        )
        order.refresh_from_db()
        assert order.informed_total is None

    def test_redirects_to_detail_on_success(self, db):
        client, user = _operacao_client(db)
        order = OrderFactory(created_by=user)
        response = client.post(
            reverse("order-update", kwargs={"pk": order.pk}),
            {
                "comanda_number": order.comanda_number,
                "order_time": "15:00",
                "payment_method": order.payment_method,
            },
        )
        assert response.status_code == 302
        assert response["Location"] == reverse("order-detail", kwargs={"pk": order.pk})


# ============================================================================
# ORDER CANCEL VIEW — Fase 5
# ============================================================================


@pytest.mark.django_db
class TestOrderCancelView:
    def test_forbidden_for_operacao_user(self, db):
        client, user = _operacao_client(db)
        order = OrderFactory(created_by=user)
        response = client.get(reverse("order-cancel", kwargs={"pk": order.pk}))
        assert response.status_code == 403

    def test_forbidden_for_regular_user(self, db, authenticated_client):
        user = UserFactory()
        order = OrderFactory(created_by=user)
        response = authenticated_client.get(reverse("order-cancel", kwargs={"pk": order.pk}))
        assert response.status_code == 403

    def test_get_shows_confirmation_form_for_superuser(self, db):
        client = _superuser_client(db)
        user = UserFactory()
        order = OrderFactory(created_by=user)
        response = client.get(reverse("order-cancel", kwargs={"pk": order.pk}))
        assert response.status_code == 200
        assert "orders/order_cancel_confirm.html" in [t.name for t in response.templates]

    def test_already_cancelled_redirects(self, db):
        client = _superuser_client(db)
        user = UserFactory()
        order = OrderFactory(created_by=user, status=Order.Status.CANCELLED)
        response = client.get(reverse("order-cancel", kwargs={"pk": order.pk}))
        assert response.status_code == 302

    def test_post_without_reason_shows_error(self, db):
        client = _superuser_client(db)
        user = UserFactory()
        order = OrderFactory(created_by=user)
        response = client.post(
            reverse("order-cancel", kwargs={"pk": order.pk}), {"cancel_reason": ""}
        )
        assert response.status_code == 200
        order.refresh_from_db()
        assert order.status == Order.Status.ACTIVE

    def test_post_with_reason_cancels_order(self, db):
        client = _superuser_client(db)
        user = UserFactory()
        order = OrderFactory(created_by=user)
        response = client.post(
            reverse("order-cancel", kwargs={"pk": order.pk}), {"cancel_reason": "Pedido duplicado"}
        )
        assert response.status_code == 302
        order.refresh_from_db()
        assert order.status == Order.Status.CANCELLED
        assert order.cancel_reason == "Pedido duplicado"
        assert order.cancelled_by is not None
        assert order.cancelled_at is not None

    def test_cancel_redirects_to_order_list(self, db):
        client = _superuser_client(db)
        user = UserFactory()
        today = date.today()
        order = OrderFactory(created_by=user, order_date=today)
        response = client.post(
            reverse("order-cancel", kwargs={"pk": order.pk}),
            {"cancel_reason": "Erro no lançamento"},
        )
        assert response.status_code == 302
        assert response["Location"] == reverse(
            "order-list-date", kwargs={"order_date": today.isoformat()}
        )
