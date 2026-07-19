"""
Testes de acréscimos pagos em produtos STANDARD (Açaís Prontos, Sorvetes, etc.).

Contexto: o service já suportava adicionais em qualquer produto de catálogo,
mas a UI escondia a seção de adicionais para tudo que não fosse BUILD_YOUR_OWN.
Estes testes fixam o comportamento do backend (nenhuma alteração de backend foi
necessária) e servem como rede de segurança para a correção da UI.
"""

from datetime import date, time
from decimal import Decimal

import pytest

from orders.models import Order, OrderItem, OrderItemAddon, Product, ProductCategory
from orders.services import create_order
from tests.conftest import (
    AddonFactory,
    ProductCategoryFactory,
    ProductFactory,
    ProductVariantFactory,
    SizeFactory,
    UserFactory,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def size_500(db):
    return SizeFactory(name="500 ml", volume_ml=500, sort_order=2)


@pytest.fixture
def cat_standard(db):
    return ProductCategoryFactory(
        name="Açaís Prontos", kind=ProductCategory.Kind.STANDARD
    )


@pytest.fixture
def product_standard(db, cat_standard):
    return ProductFactory(
        category=cat_standard,
        product_type=Product.ProductType.STANDARD,
        name="Açaí Nutella",
    )


@pytest.fixture
def variant_standard(db, product_standard, size_500):
    return ProductVariantFactory(
        product=product_standard,
        size=size_500,
        price=Decimal("30.00"),
        included_addons_limit=0,
    )


@pytest.fixture
def addon_nutella(db):
    return AddonFactory(name="Nutella", price=Decimal("7.50"), is_free_option=False)


@pytest.fixture
def addon_pacoca(db):
    return AddonFactory(name="Paçoca", price=Decimal("3.00"), is_free_option=False)


@pytest.fixture
def addon_free(db):
    return AddonFactory(name="Granola", price=Decimal("3.00"), is_free_option=True)


def _base_kwargs(user):
    return dict(
        comanda_number="5",
        order_date=date(2026, 7, 15),
        order_time=time(16, 30),
        payment_method=Order.PaymentMethod.PIX,
        created_by=user,
    )


# ---------------------------------------------------------------------------
# Testes de service: acréscimos pagos em produto STANDARD
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestPaidAddonsOnStandardProduct:
    def test_addon_pago_no_produto_standard(self, user, variant_standard, addon_nutella):
        """Acréscimo em produto STANDARD é cobrado (nenhum é grátis)."""
        order = create_order(
            **_base_kwargs(user),
            items=[{"variant": variant_standard, "quantity": 1, "addons": [addon_nutella]}],
        )

        item = order.items.first()
        assert item.addons_total == Decimal("7.50")
        assert item.line_total == Decimal("37.50")  # 30 + 7.50
        assert order.total == Decimal("37.50")

    def test_addon_pago_cria_orderitemaddon(self, user, variant_standard, addon_nutella):
        """OrderItemAddon é criado com is_included=False e line_total = preço."""
        order = create_order(
            **_base_kwargs(user),
            items=[{"variant": variant_standard, "quantity": 1, "addons": [addon_nutella]}],
        )

        item = order.items.first()
        addon_record = item.addons.get()
        assert addon_record.is_included is False
        assert addon_record.unit_price == Decimal("7.50")
        assert addon_record.line_total == Decimal("7.50")
        assert addon_record.name == "Nutella"

    def test_multiplos_addons_pagos(self, user, variant_standard, addon_nutella, addon_pacoca):
        """Múltiplos acréscimos pagos somam corretamente."""
        order = create_order(
            **_base_kwargs(user),
            items=[
                {
                    "variant": variant_standard,
                    "quantity": 1,
                    "addons": [addon_nutella, addon_pacoca],
                }
            ],
        )

        item = order.items.first()
        # 7.50 + 3.00 = 10.50
        assert item.addons_total == Decimal("10.50")
        assert item.line_total == Decimal("40.50")  # 30 + 10.50
        assert order.total == Decimal("40.50")
        assert item.addons.count() == 2

    def test_addon_free_option_em_standard_vira_pago(self, user, variant_standard, addon_free):
        """Adicional marcado como free_option em produto STANDARD ainda é cobrado
        (nenhum limite gratuito)."""
        order = create_order(
            **_base_kwargs(user),
            items=[{"variant": variant_standard, "quantity": 1, "addons": [addon_free]}],
        )

        item = order.items.first()
        addon_record = item.addons.get()
        assert addon_record.is_included is False
        assert addon_record.line_total == Decimal("3.00")
        assert item.addons_total == Decimal("3.00")

    def test_produto_standard_sem_addons_mantém_total(self, user, variant_standard):
        """Produto STANDARD sem acréscimos continua com total original."""
        order = create_order(
            **_base_kwargs(user),
            items=[{"variant": variant_standard, "quantity": 1, "addons": []}],
        )

        item = order.items.first()
        assert item.addons_total == Decimal("0.00")
        assert item.line_total == Decimal("30.00")
        assert order.total == Decimal("30.00")

    def test_multiplicidade_com_addon(self, user, variant_standard, addon_nutella):
        """Quantidade > 1 com acréscimo: (unit_price + addons_total) × qty."""
        order = create_order(
            **_base_kwargs(user),
            items=[{"variant": variant_standard, "quantity": 2, "addons": [addon_nutella]}],
        )

        item = order.items.first()
        # (30 + 7.50) × 2 = 75.00
        assert item.line_total == Decimal("75.00")
        assert order.total == Decimal("75.00")


# ---------------------------------------------------------------------------
# Testes de view: POST com addon em item STANDARD
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestOrderCreateViewPaidAddon:
    def _post_with_addon(self, client, variant, addon):
        """Helper: POST que cria um pedido com 1 item CATALOG + 1 addon."""
        from django.contrib.auth.models import Group

        user = UserFactory(username="func_paid_test")
        user.set_password("testpass")
        user.save()
        group, _ = Group.objects.get_or_create(name="Operacao")
        user.groups.add(group)
        client.force_login(user)

        return client.post(
            "/pedidos/novo/",
            {
                "comanda_number": "7",
                "order_date": "2026-07-15",
                "order_time": "15:00",
                "payment_method": "PIX",
                "item_type[]": ["CATALOG"],
                "item_variant_id[]": [str(variant.pk)],
                "item_quantity[]": ["1"],
                "item_addon_ids[]": [str(addon.pk)],
                "item_manual_description[]": [""],
                "item_manual_unit_price[]": [""],
            },
        )

    def test_view_cria_pedido_com_addon_pago(self, client, variant_standard, addon_nutella):
        from django.test import Client

        c = Client()
        response = self._post_with_addon(c, variant_standard, addon_nutella)

        # Redireciona para o detalhe → pedido criado
        assert response.status_code == 302
        order = Order.objects.latest("created_at")
        assert order.total == Decimal("37.50")

    def test_view_addon_pago_registrado_no_item(self, client, variant_standard, addon_nutella):
        from django.test import Client

        c = Client()
        self._post_with_addon(c, variant_standard, addon_nutella)

        order = Order.objects.latest("created_at")
        item = order.items.first()
        addon_record = item.addons.get()
        assert addon_record.is_included is False
        assert addon_record.name == "Nutella"
