"""
Testes da funcionalidade de Brindes/cortesias (Fase 2 — relatório).

Itens da categoria de brindes (GIFT_CATEGORY_NAME) são lançados a R$ 0:
- não entram no faturamento nem nos rankings de venda;
- aparecem no relatório de brindes com valor estimado;
- os acréscimos cortesia aparecem também no ranking de adicionais.
"""

from datetime import date, time
from decimal import Decimal

import pytest

from orders.models import GIFT_CATEGORY_NAME, Order, Product, ProductCategory
from orders.selectors import (
    get_gifts_report,
    get_liters_sold,
    get_top_addons,
    get_top_products,
)
from orders.services import create_order
from tests.conftest import (
    AddonFactory,
    ProductCategoryFactory,
    ProductFactory,
    ProductVariantFactory,
    SizeFactory,
    UserFactory,
)

START = date(2026, 7, 1)
END = date(2026, 7, 31)


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def size_500(db):
    return SizeFactory(name="500 ml", volume_ml=500, sort_order=2)


@pytest.fixture
def gift_category(db):
    return ProductCategoryFactory(name=GIFT_CATEGORY_NAME, kind=ProductCategory.Kind.OTHER)


@pytest.fixture
def gift_acai(db, gift_category, size_500):
    """Açaí grátis do cartão fidelidade — 500 ml a R$ 0."""
    prod = ProductFactory(
        category=gift_category,
        product_type=Product.ProductType.STANDARD,
        name="Açaí Ninho (brinde)",
    )
    return ProductVariantFactory(product=prod, size=size_500, price=Decimal("0.00"))


@pytest.fixture
def gift_pacoca(db, gift_category):
    """Acréscimo cortesia Paçoca — sem tamanho, R$ 0."""
    prod = ProductFactory(
        category=gift_category,
        product_type=Product.ProductType.STANDARD,
        name="Paçoca",
    )
    return ProductVariantFactory(product=prod, size=None, price=Decimal("0.00"))


@pytest.fixture
def paid_ninho(db, size_500):
    """Açaí Ninho pago (referência de preço para valorizar o brinde)."""
    cat = ProductCategoryFactory(name="Açaís Prontos", kind=ProductCategory.Kind.STANDARD)
    prod = ProductFactory(
        category=cat, product_type=Product.ProductType.STANDARD, name="04 Açaí Ninho"
    )
    return ProductVariantFactory(product=prod, size=size_500, price=Decimal("22.00"))


@pytest.fixture
def addon_pacoca(db):
    return AddonFactory(name="Paçoca", price=Decimal("3.00"), is_free_option=True)


def _make_order(user, items):
    return create_order(
        comanda_number="1",
        order_date=date(2026, 7, 15),
        order_time=time(16, 0),
        payment_method=Order.PaymentMethod.PIX,
        created_by=user,
        items=items,
    )


@pytest.mark.django_db
class TestGiftsReport:
    def test_brinde_nao_entra_no_total_do_pedido(self, user, paid_ninho, gift_acai, gift_pacoca):
        order = _make_order(
            user,
            [
                {"variant": paid_ninho, "quantity": 1},
                {"variant": gift_acai, "quantity": 1},
                {"variant": gift_pacoca, "quantity": 1},
            ],
        )
        assert order.total == Decimal("22.00")

    def test_relatorio_conta_e_valoriza(
        self, user, paid_ninho, gift_acai, gift_pacoca, addon_pacoca
    ):
        _make_order(
            user,
            [
                {"variant": gift_acai, "quantity": 2},
                {"variant": gift_pacoca, "quantity": 3},
            ],
        )
        report = get_gifts_report(start_date=START, end_date=END)

        assert report["total_quantity"] == 5
        # açaí: 2 × 22,00 (preço do Ninho pago) + paçoca: 3 × 3,00 (preço do adicional)
        assert report["total_value"] == Decimal("53.00")

        by_name = {i["name"]: i for i in report["items"]}
        assert by_name["Açaí Ninho (brinde)"]["quantity"] == 2
        assert by_name["Açaí Ninho (brinde)"]["unit_price"] == Decimal("22.00")
        assert by_name["Paçoca"]["quantity"] == 3
        assert by_name["Paçoca"]["unit_price"] == Decimal("3.00")

    def test_brinde_fora_dos_mais_vendidos(self, user, paid_ninho, gift_acai, gift_pacoca):
        _make_order(
            user,
            [
                {"variant": paid_ninho, "quantity": 1},
                {"variant": gift_acai, "quantity": 1},
                {"variant": gift_pacoca, "quantity": 1},
            ],
        )
        names = {row["product_name"] for row in get_top_products(start_date=START, end_date=END)}
        assert "04 Açaí Ninho" in names
        assert "Açaí Ninho (brinde)" not in names
        assert "Paçoca" not in names

    def test_acrescimo_cortesia_no_ranking_de_adicionais(self, user, gift_pacoca, addon_pacoca):
        _make_order(user, [{"variant": gift_pacoca, "quantity": 1}])
        _make_order(user, [{"variant": gift_pacoca, "quantity": 1}])
        addons = {
            row["name"]: row["count"] for row in get_top_addons(start_date=START, end_date=END)
        }
        assert addons.get("Paçoca") == 2

    def test_brinde_fora_dos_litros_vendidos(self, user, gift_acai):
        _make_order(user, [{"variant": gift_acai, "quantity": 3}])
        assert get_liters_sold(start_date=START, end_date=END) == Decimal("0")

    def test_relatorio_vazio_sem_brindes(self, user, paid_ninho):
        _make_order(user, [{"variant": paid_ninho, "quantity": 1}])
        report = get_gifts_report(start_date=START, end_date=END)
        assert report["items"] == []
        assert report["total_quantity"] == 0
        assert report["total_value"] == Decimal("0.00")
