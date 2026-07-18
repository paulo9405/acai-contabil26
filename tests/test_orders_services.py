"""
Testes dos models e services de pedidos — Fase 3.
"""

from datetime import date, time
from decimal import Decimal

import pytest

from orders.models import Order, Product, ProductCategory
from orders.selectors import get_order_detail, get_orders_by_date
from orders.services import cancel_order, create_order, update_order
from tests.conftest import (
    AddonFactory,
    ProductCategoryFactory,
    ProductFactory,
    ProductVariantFactory,
    SizeFactory,
    UserFactory,
)

# ---------------------------------------------------------------------------
# Fixtures locais
# ---------------------------------------------------------------------------


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def superuser(db):
    return UserFactory(is_superuser=True, is_staff=True)


@pytest.fixture
def size_300(db):
    return SizeFactory(name="300 ml", volume_ml=300, sort_order=1)


@pytest.fixture
def size_500(db):
    return SizeFactory(name="500 ml", volume_ml=500, sort_order=2)


@pytest.fixture
def cat_standard(db):
    return ProductCategoryFactory(kind=ProductCategory.Kind.STANDARD)


@pytest.fixture
def cat_build(db):
    return ProductCategoryFactory(kind=ProductCategory.Kind.BUILD_YOUR_OWN)


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
    )


@pytest.fixture
def product_build(db, cat_build):
    return ProductFactory(
        category=cat_build,
        product_type=Product.ProductType.BUILD_YOUR_OWN,
        name="Monte seu Açaí",
    )


@pytest.fixture
def variant_build_300(db, product_build, size_300):
    return ProductVariantFactory(
        product=product_build,
        size=size_300,
        price=Decimal("18.00"),
        included_addons_limit=2,
    )


@pytest.fixture
def addon_free1(db):
    return AddonFactory(name="Granola", price=Decimal("3.00"), is_free_option=True)


@pytest.fixture
def addon_free2(db):
    return AddonFactory(name="Banana", price=Decimal("3.00"), is_free_option=True)


@pytest.fixture
def addon_paid(db):
    return AddonFactory(name="Nutella", price=Decimal("7.50"), is_free_option=False)


def _base_order_kwargs(user):
    return dict(
        comanda_number="10",
        order_date=date(2026, 7, 15),
        order_time=time(16, 30),
        payment_method=Order.PaymentMethod.PIX,
        created_by=user,
    )


# ---------------------------------------------------------------------------
# Model: Order
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestOrderModel:
    def test_str(self, user):
        from tests.conftest import OrderFactory

        order = OrderFactory(created_by=user, comanda_number="5", order_date=date(2026, 7, 15))
        assert "Comanda 5" in str(order)
        assert "15/07/2026" in str(order)

    def test_has_total_divergence_none(self, user):
        from tests.conftest import OrderFactory

        order = OrderFactory(created_by=user, total=Decimal("30.00"), informed_total=None)
        assert order.has_total_divergence is False

    def test_has_total_divergence_equal(self, user):
        from tests.conftest import OrderFactory

        order = OrderFactory(
            created_by=user, total=Decimal("30.00"), informed_total=Decimal("30.00")
        )
        assert order.has_total_divergence is False

    def test_has_total_divergence_different(self, user):
        from tests.conftest import OrderFactory

        order = OrderFactory(
            created_by=user, total=Decimal("30.00"), informed_total=Decimal("28.00")
        )
        assert order.has_total_divergence is True

    def test_comanda_repetida_mesmo_dia_permitida(self, user):
        from tests.conftest import OrderFactory

        o1 = OrderFactory(created_by=user, comanda_number="1", order_date=date(2026, 7, 15))
        o2 = OrderFactory(created_by=user, comanda_number="1", order_date=date(2026, 7, 15))
        assert o1.pk != o2.pk
        assert Order.objects.filter(comanda_number="1", order_date=date(2026, 7, 15)).count() == 2

    def test_status_default_active(self, user):
        from tests.conftest import OrderFactory

        order = OrderFactory(created_by=user)
        assert order.status == Order.Status.ACTIVE


# ---------------------------------------------------------------------------
# Model: OrderItem e OrderItemAddon
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestOrderItemModel:
    def test_str(self, user):
        from tests.conftest import OrderItemFactory

        item = OrderItemFactory(product_name="Açaí Oreo", quantity=2, line_total=Decimal("52.00"))
        assert "Açaí Oreo" in str(item)
        assert "2" in str(item)

    def test_orderitemaddon_str_gratis(self, user):
        from tests.conftest import OrderItemAddonFactory

        addon = OrderItemAddonFactory(name="Granola", is_included=True, unit_price=Decimal("0.00"))
        assert "grátis" in str(addon)

    def test_orderitemaddon_str_pago(self, user):
        from tests.conftest import OrderItemAddonFactory

        addon = OrderItemAddonFactory(name="Nutella", is_included=False, unit_price=Decimal("7.50"))
        assert "R$ 7.50" in str(addon)


# ---------------------------------------------------------------------------
# Service: create_order
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestCreateOrder:
    def test_pedido_simples_sem_adicionais(self, user, variant_standard):
        order = create_order(
            items=[{"variant": variant_standard, "quantity": 1, "addons": []}],
            **_base_order_kwargs(user),
        )
        assert order.pk is not None
        assert order.total == Decimal("30.00")
        assert order.items.count() == 1

    def test_pedido_com_quantidade(self, user, variant_standard):
        order = create_order(
            items=[{"variant": variant_standard, "quantity": 2, "addons": []}],
            **_base_order_kwargs(user),
        )
        assert order.total == Decimal("60.00")
        item = order.items.first()
        assert item.line_total == Decimal("60.00")
        assert item.quantity == 2

    def test_multiplos_itens(self, user, variant_standard, variant_build_300):
        order = create_order(
            items=[
                {"variant": variant_standard, "quantity": 1, "addons": []},
                {"variant": variant_build_300, "quantity": 2, "addons": []},
            ],
            **_base_order_kwargs(user),
        )
        # 30.00 + (18.00 * 2) = 66.00
        assert order.total == Decimal("66.00")
        assert order.items.count() == 2

    def test_snapshot_product_name(self, user, variant_standard):
        order = create_order(
            items=[{"variant": variant_standard, "quantity": 1, "addons": []}],
            **_base_order_kwargs(user),
        )
        item = order.items.first()
        assert item.product_name == "Açaí Nutella"

    def test_snapshot_size_name(self, user, variant_standard):
        order = create_order(
            items=[{"variant": variant_standard, "quantity": 1, "addons": []}],
            **_base_order_kwargs(user),
        )
        item = order.items.first()
        assert item.size_name == "500 ml"

    def test_snapshot_unit_price(self, user, variant_standard):
        order = create_order(
            items=[{"variant": variant_standard, "quantity": 1, "addons": []}],
            **_base_order_kwargs(user),
        )
        item = order.items.first()
        assert item.unit_price == Decimal("30.00")

    def test_preco_historico_isolado(self, user, variant_standard):
        """Alterar o preço do catálogo não afeta pedidos já lançados."""
        order = create_order(
            items=[{"variant": variant_standard, "quantity": 1, "addons": []}],
            **_base_order_kwargs(user),
        )
        variant_standard.price = Decimal("99.00")
        variant_standard.save()

        item = order.items.first()
        item.refresh_from_db()
        assert item.unit_price == Decimal("30.00")

    def test_adicional_incluido_gratis(self, user, variant_build_300, addon_free1):
        """Adicional dentro do limite → is_included=True, line_total=0."""
        order = create_order(
            items=[{"variant": variant_build_300, "quantity": 1, "addons": [addon_free1]}],
            **_base_order_kwargs(user),
        )
        item = order.items.first()
        addon_item = item.addons.get(name="Granola")
        assert addon_item.is_included is True
        assert addon_item.line_total == Decimal("0.00")
        assert item.addons_total == Decimal("0.00")
        assert order.total == Decimal("18.00")

    def test_dois_adicionais_dentro_limite(self, user, variant_build_300, addon_free1, addon_free2):
        """limit=2: dois adicionais grátis → addons_total=0."""
        order = create_order(
            items=[
                {"variant": variant_build_300, "quantity": 1, "addons": [addon_free1, addon_free2]}
            ],
            **_base_order_kwargs(user),
        )
        item = order.items.first()
        assert item.addons.filter(is_included=True).count() == 2
        assert item.addons_total == Decimal("0.00")
        assert order.total == Decimal("18.00")

    def test_excedente_vira_pago_automaticamente(
        self, user, variant_build_300, addon_free1, addon_free2, addon_free3=None
    ):
        """limit=2: terceiro adicional elegível → vira pago sem bloquear."""
        addon_free3 = AddonFactory(name="Paçoca", price=Decimal("3.00"), is_free_option=True)
        order = create_order(
            items=[
                {
                    "variant": variant_build_300,
                    "quantity": 1,
                    "addons": [addon_free1, addon_free2, addon_free3],
                }
            ],
            **_base_order_kwargs(user),
        )
        item = order.items.first()
        assert item.addons.filter(is_included=True).count() == 2
        assert item.addons.filter(is_included=False).count() == 1
        excedente = item.addons.get(name="Paçoca")
        assert excedente.is_included is False
        assert excedente.unit_price == Decimal("3.00")
        assert item.addons_total == Decimal("3.00")
        assert order.total == Decimal("21.00")

    def test_adicional_nao_free_sempre_pago(self, user, variant_build_300, addon_paid):
        """Adicional não elegível como grátis → sempre pago, mesmo dentro do limite."""
        order = create_order(
            items=[{"variant": variant_build_300, "quantity": 1, "addons": [addon_paid]}],
            **_base_order_kwargs(user),
        )
        item = order.items.first()
        addon_item = item.addons.get(name="Nutella")
        assert addon_item.is_included is False
        assert addon_item.unit_price == Decimal("7.50")
        assert item.addons_total == Decimal("7.50")

    def test_adicionais_em_produto_standard_sempre_pagos(self, user, variant_standard, addon_free1):
        """Produto STANDARD: adicionais são sempre pagos (sem limite grátis)."""
        order = create_order(
            items=[{"variant": variant_standard, "quantity": 1, "addons": [addon_free1]}],
            **_base_order_kwargs(user),
        )
        item = order.items.first()
        addon_item = item.addons.first()
        assert addon_item.is_included is False
        assert addon_item.unit_price == Decimal("3.00")

    def test_informed_total_divergencia_nao_bloqueia(self, user, variant_standard):
        """Divergência entre informed_total e total é permitida — apenas um aviso."""
        order = create_order(
            items=[{"variant": variant_standard, "quantity": 1, "addons": []}],
            informed_total=Decimal("28.00"),
            **_base_order_kwargs(user),
        )
        assert order.total == Decimal("30.00")
        assert order.informed_total == Decimal("28.00")
        assert order.has_total_divergence is True

    def test_status_active_apos_criacao(self, user, variant_standard):
        order = create_order(
            items=[{"variant": variant_standard, "quantity": 1, "addons": []}],
            **_base_order_kwargs(user),
        )
        assert order.status == Order.Status.ACTIVE

    def test_comanda_repetida_permitida(self, user, variant_standard, size_300, cat_standard):
        """Duas comandas com o mesmo número no mesmo dia — ambas devem ser salvas."""
        product2 = ProductFactory(category=cat_standard, product_type=Product.ProductType.STANDARD)
        variant2 = ProductVariantFactory(product=product2, size=size_300, price=Decimal("18.00"))

        o1 = create_order(
            comanda_number="1",
            order_date=date(2026, 7, 15),
            order_time=time(14, 0),
            payment_method=Order.PaymentMethod.PIX,
            created_by=user,
            items=[{"variant": variant_standard, "quantity": 1, "addons": []}],
        )
        o2 = create_order(
            comanda_number="1",
            order_date=date(2026, 7, 15),
            order_time=time(16, 0),
            payment_method=Order.PaymentMethod.CASH,
            created_by=user,
            items=[{"variant": variant2, "quantity": 1, "addons": []}],
        )
        assert o1.pk != o2.pk
        assert Order.objects.filter(comanda_number="1", order_date=date(2026, 7, 15)).count() == 2

    def test_atomicidade_rollback(self, user):
        """Se algo falhar durante a criação, nenhum registro deve ser salvo."""

        class BrokenVariant:
            product = None
            size = None
            price = Decimal("10.00")
            included_addons_limit = 0

        before = Order.objects.count()
        with pytest.raises(Exception):
            create_order(
                items=[{"variant": BrokenVariant(), "quantity": 1, "addons": []}],
                **_base_order_kwargs(user),
            )
        assert Order.objects.count() == before


# ---------------------------------------------------------------------------
# Service: cancel_order
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestCancelOrder:
    def _create_simple_order(self, user, variant_standard):
        return create_order(
            items=[{"variant": variant_standard, "quantity": 1, "addons": []}],
            **_base_order_kwargs(user),
        )

    def test_cancela_com_motivo(self, user, superuser, variant_standard):
        order = self._create_simple_order(user, variant_standard)
        cancelled = cancel_order(order=order, cancelled_by=superuser, reason="Erro no lançamento")
        assert cancelled.status == Order.Status.CANCELLED
        assert cancelled.cancel_reason == "Erro no lançamento"
        assert cancelled.cancelled_by == superuser
        assert cancelled.cancelled_at is not None

    def test_sem_motivo_levanta_erro(self, user, superuser, variant_standard):
        order = self._create_simple_order(user, variant_standard)
        with pytest.raises(ValueError, match="obrigatório"):
            cancel_order(order=order, cancelled_by=superuser, reason="")

    def test_motivo_so_espacos_levanta_erro(self, user, superuser, variant_standard):
        order = self._create_simple_order(user, variant_standard)
        with pytest.raises(ValueError):
            cancel_order(order=order, cancelled_by=superuser, reason="   ")

    def test_cancelar_ja_cancelado_levanta_erro(self, user, superuser, variant_standard):
        order = self._create_simple_order(user, variant_standard)
        cancel_order(order=order, cancelled_by=superuser, reason="Motivo 1")
        with pytest.raises(ValueError, match="já está cancelado"):
            cancel_order(order=order, cancelled_by=superuser, reason="Motivo 2")

    def test_pedido_continua_no_banco(self, user, superuser, variant_standard):
        """Cancelamento não faz delete físico."""
        order = self._create_simple_order(user, variant_standard)
        pk = order.pk
        cancel_order(order=order, cancelled_by=superuser, reason="Teste")
        assert Order.objects.filter(pk=pk).exists()
        assert Order.objects.get(pk=pk).status == Order.Status.CANCELLED


# ---------------------------------------------------------------------------
# Service: update_order
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestUpdateOrder:
    # Usa data passada para que create_order não dispare recalculate_closing_from_orders
    # (que só atua em pedidos com order_date == today).
    _PAST_DATE = date(2026, 7, 10)

    def _create_simple_order(self, user, variant_standard):
        return create_order(
            comanda_number="10",
            order_date=self._PAST_DATE,
            order_time=time(16, 30),
            payment_method=Order.PaymentMethod.PIX,
            created_by=user,
            items=[{"variant": variant_standard, "quantity": 1, "addons": []}],
        )

    def test_funcionario_edita_sem_fechamento(self, user, variant_standard):
        order = self._create_simple_order(user, variant_standard)
        updated = update_order(order=order, updated_by=user, comanda_number="99")
        assert updated.comanda_number == "99"

    def test_funcionario_bloqueado_apos_fechamento(self, user, variant_standard, db):
        from tests.conftest import DailyClosingFactory

        order = self._create_simple_order(user, variant_standard)
        DailyClosingFactory(date=order.order_date)

        with pytest.raises(PermissionError):
            update_order(order=order, updated_by=user, comanda_number="99")

    def test_superuser_edita_mesmo_apos_fechamento(self, superuser, variant_standard, user, db):
        from tests.conftest import DailyClosingFactory

        order = self._create_simple_order(user, variant_standard)
        DailyClosingFactory(date=order.order_date)

        updated = update_order(order=order, updated_by=superuser, comanda_number="77")
        assert updated.comanda_number == "77"

    def test_atualiza_payment_method(self, user, variant_standard):
        order = self._create_simple_order(user, variant_standard)
        updated = update_order(
            order=order, updated_by=user, payment_method=Order.PaymentMethod.CASH
        )
        assert updated.payment_method == Order.PaymentMethod.CASH

    def test_atualiza_informed_total_para_none(self, user, variant_standard):
        order = self._create_simple_order(user, variant_standard)
        order.informed_total = Decimal("30.00")
        order.save(update_fields=["informed_total"])

        updated = update_order(order=order, updated_by=user, informed_total=None)
        assert updated.informed_total is None

    def test_omitir_informed_total_nao_altera(self, user, variant_standard):
        order = self._create_simple_order(user, variant_standard)
        order.informed_total = Decimal("30.00")
        order.save(update_fields=["informed_total"])

        updated = update_order(order=order, updated_by=user, comanda_number="5")
        assert updated.informed_total == Decimal("30.00")


# ---------------------------------------------------------------------------
# Selectors
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestSelectors:
    def test_get_orders_by_date(self, user, variant_standard):
        d = date(2026, 7, 15)
        o1 = create_order(
            comanda_number="1",
            order_date=d,
            order_time=time(14, 0),
            payment_method=Order.PaymentMethod.PIX,
            created_by=user,
            items=[{"variant": variant_standard, "quantity": 1, "addons": []}],
        )
        o2 = create_order(
            comanda_number="2",
            order_date=d,
            order_time=time(16, 0),
            payment_method=Order.PaymentMethod.CASH,
            created_by=user,
            items=[{"variant": variant_standard, "quantity": 1, "addons": []}],
        )
        # Pedido de outro dia — não deve aparecer
        create_order(
            comanda_number="3",
            order_date=date(2026, 7, 14),
            order_time=time(10, 0),
            payment_method=Order.PaymentMethod.PIX,
            created_by=user,
            items=[{"variant": variant_standard, "quantity": 1, "addons": []}],
        )

        qs = get_orders_by_date(date=d)
        pks = list(qs.values_list("pk", flat=True))
        assert o1.pk in pks
        assert o2.pk in pks
        assert len(pks) == 2

    def test_get_order_detail(self, user, variant_build_300, addon_free1):
        order = create_order(
            items=[{"variant": variant_build_300, "quantity": 1, "addons": [addon_free1]}],
            **_base_order_kwargs(user),
        )
        detail = get_order_detail(order_id=order.pk)
        assert detail.pk == order.pk
        items = list(detail.items.all())
        assert len(items) == 1
        addons = list(items[0].addons.all())
        assert len(addons) == 1
