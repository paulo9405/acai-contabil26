"""
Testes da Fase 6 — Integração entre Pedidos e Fechamento Diário.
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone
from unittest.mock import patch

from finance.models import DailyClosing
from orders.models import Order
from orders.services import recalculate_closing_from_orders

from tests.conftest import (
    DailyClosingFactory,
    OrderFactory,
    ProductVariantFactory,
    ProductFactory,
    ProductCategoryFactory,
    SizeFactory,
    UserFactory,
)


# ===========================================================================
# recalculate_closing_from_orders — comportamento direto
# ===========================================================================

@pytest.mark.django_db
def test_recalculate_creates_closing_when_none_exists():
    """Sem fechamento existente: cria um com source=ORDERS."""
    today = date.today()
    user = UserFactory()
    OrderFactory(
        order_date=today,
        payment_method=Order.PaymentMethod.PIX,
        total=Decimal('30.00'),
        status=Order.Status.ACTIVE,
        created_by=user,
    )
    OrderFactory(
        order_date=today,
        payment_method=Order.PaymentMethod.CASH,
        total=Decimal('20.00'),
        status=Order.Status.ACTIVE,
        created_by=user,
    )

    closing = recalculate_closing_from_orders(date=today)

    assert closing.source == DailyClosing.ClosingSource.ORDERS
    assert closing.order_count == 2
    assert closing.pix_sales == Decimal('30.00')
    assert closing.cash_sales == Decimal('20.00')
    assert closing.card_sales == Decimal('0.00')


@pytest.mark.django_db
def test_recalculate_updates_existing_orders_closing():
    """Fechamento existente com source=ORDERS: atualiza valores."""
    today = date.today()
    user = UserFactory()
    closing = DailyClosingFactory(
        date=today,
        order_count=1,
        cash_sales=Decimal('10.00'),
        pix_sales=Decimal('0.00'),
        card_sales=Decimal('0.00'),
        source=DailyClosing.ClosingSource.ORDERS,
    )
    OrderFactory(
        order_date=today,
        payment_method=Order.PaymentMethod.CARD,
        total=Decimal('50.00'),
        status=Order.Status.ACTIVE,
        created_by=user,
    )

    recalculate_closing_from_orders(date=today)
    closing.refresh_from_db()

    assert closing.order_count == 1
    assert closing.card_sales == Decimal('50.00')
    assert closing.pix_sales == Decimal('0.00')
    assert closing.cash_sales == Decimal('0.00')


@pytest.mark.django_db
def test_recalculate_does_not_touch_manual_closing():
    """Fechamento com source=MANUAL não é alterado pelo recalculate."""
    today = date.today()
    user = UserFactory()
    closing = DailyClosingFactory(
        date=today,
        order_count=99,
        cash_sales=Decimal('999.00'),
        pix_sales=Decimal('0.00'),
        card_sales=Decimal('0.00'),
        source=DailyClosing.ClosingSource.MANUAL,
    )
    OrderFactory(
        order_date=today,
        payment_method=Order.PaymentMethod.PIX,
        total=Decimal('30.00'),
        status=Order.Status.ACTIVE,
        created_by=user,
    )

    result = recalculate_closing_from_orders(date=today)
    closing.refresh_from_db()

    assert closing.order_count == 99
    assert closing.cash_sales == Decimal('999.00')
    assert closing.source == DailyClosing.ClosingSource.MANUAL
    assert result.pk == closing.pk


@pytest.mark.django_db
def test_recalculate_excludes_cancelled_orders():
    """Pedidos CANCELLED não contam no recalculate."""
    today = date.today()
    user = UserFactory()
    OrderFactory(
        order_date=today,
        payment_method=Order.PaymentMethod.PIX,
        total=Decimal('30.00'),
        status=Order.Status.ACTIVE,
        created_by=user,
    )
    OrderFactory(
        order_date=today,
        payment_method=Order.PaymentMethod.PIX,
        total=Decimal('50.00'),
        status=Order.Status.CANCELLED,
        created_by=user,
    )

    closing = recalculate_closing_from_orders(date=today)

    assert closing.order_count == 1
    assert closing.pix_sales == Decimal('30.00')


@pytest.mark.django_db
def test_recalculate_with_zero_active_orders_creates_closing():
    """Sem pedidos ativos: cria fechamento com zeros."""
    today = date.today()
    closing = recalculate_closing_from_orders(date=today)

    assert closing.order_count == 0
    assert closing.cash_sales == Decimal('0.00')
    assert closing.pix_sales == Decimal('0.00')
    assert closing.card_sales == Decimal('0.00')
    assert closing.source == DailyClosing.ClosingSource.ORDERS


@pytest.mark.django_db
def test_recalculate_aggregates_multiple_payment_methods():
    """Agrega corretamente pedidos por forma de pagamento."""
    today = date.today()
    user = UserFactory()
    for _ in range(2):
        OrderFactory(
            order_date=today,
            payment_method=Order.PaymentMethod.PIX,
            total=Decimal('10.00'),
            status=Order.Status.ACTIVE,
            created_by=user,
        )
    OrderFactory(
        order_date=today,
        payment_method=Order.PaymentMethod.CASH,
        total=Decimal('15.00'),
        status=Order.Status.ACTIVE,
        created_by=user,
    )
    OrderFactory(
        order_date=today,
        payment_method=Order.PaymentMethod.CARD,
        total=Decimal('25.00'),
        status=Order.Status.ACTIVE,
        created_by=user,
    )

    closing = recalculate_closing_from_orders(date=today)

    assert closing.order_count == 4
    assert closing.pix_sales == Decimal('20.00')
    assert closing.cash_sales == Decimal('15.00')
    assert closing.card_sales == Decimal('25.00')


# ===========================================================================
# create_order — dispara recalculate para hoje
# ===========================================================================

@pytest.mark.django_db
def test_create_order_today_triggers_recalculate():
    """Criar pedido de hoje deve criar/atualizar fechamento via recalculate."""
    from orders.services import create_order

    today = date.today()
    user = UserFactory()

    category = ProductCategoryFactory()
    size = SizeFactory()
    product = ProductFactory(category=category)
    variant = ProductVariantFactory(product=product, size=size, price=Decimal('24.00'))

    assert not DailyClosing.objects.filter(date=today).exists()

    create_order(
        comanda_number='1',
        order_date=today,
        order_time='14:00',
        payment_method=Order.PaymentMethod.PIX,
        items=[{'variant': variant, 'quantity': 1, 'addons': []}],
        created_by=user,
    )

    closing = DailyClosing.objects.get(date=today)
    assert closing.source == DailyClosing.ClosingSource.ORDERS
    assert closing.pix_sales == Decimal('24.00')
    assert closing.order_count == 1


@pytest.mark.django_db
def test_create_order_past_date_does_not_trigger_recalculate():
    """Criar pedido com data passada não cria/altera fechamento."""
    from orders.services import create_order

    past = date.today() - timedelta(days=1)
    user = UserFactory()

    category = ProductCategoryFactory()
    size = SizeFactory()
    product = ProductFactory(category=category)
    variant = ProductVariantFactory(product=product, size=size, price=Decimal('18.00'))

    create_order(
        comanda_number='1',
        order_date=past,
        order_time='12:00',
        payment_method=Order.PaymentMethod.CASH,
        items=[{'variant': variant, 'quantity': 1, 'addons': []}],
        created_by=user,
    )

    assert not DailyClosing.objects.filter(date=past).exists()


# ===========================================================================
# cancel_order — dispara recalculate para hoje
# ===========================================================================

@pytest.mark.django_db
def test_cancel_order_today_updates_closing():
    """Cancelar pedido de hoje atualiza o fechamento."""
    from orders.services import create_order, cancel_order

    today = date.today()
    user = UserFactory()

    category = ProductCategoryFactory()
    size = SizeFactory()
    product = ProductFactory(category=category)
    variant = ProductVariantFactory(product=product, size=size, price=Decimal('30.00'))

    order = create_order(
        comanda_number='2',
        order_date=today,
        order_time='15:00',
        payment_method=Order.PaymentMethod.CARD,
        items=[{'variant': variant, 'quantity': 1, 'addons': []}],
        created_by=user,
    )

    closing = DailyClosing.objects.get(date=today)
    assert closing.order_count == 1
    assert closing.card_sales == Decimal('30.00')

    cancel_order(order=order, cancelled_by=user, reason='Teste de cancelamento')

    closing.refresh_from_db()
    assert closing.order_count == 0
    assert closing.card_sales == Decimal('0.00')


@pytest.mark.django_db
def test_cancel_order_past_date_does_not_touch_manual_closing():
    """Cancelar pedido de data passada não toca fechamento MANUAL."""
    from orders.services import cancel_order

    past = date.today() - timedelta(days=2)
    user = UserFactory()
    order = OrderFactory(
        order_date=past,
        status=Order.Status.ACTIVE,
        payment_method=Order.PaymentMethod.PIX,
        total=Decimal('20.00'),
        created_by=user,
    )
    closing = DailyClosingFactory(
        date=past,
        cash_sales=Decimal('200.00'),
        pix_sales=Decimal('100.00'),
        card_sales=Decimal('50.00'),
        order_count=5,
        source=DailyClosing.ClosingSource.MANUAL,
    )

    cancel_order(order=order, cancelled_by=user, reason='Teste')

    closing.refresh_from_db()
    assert closing.cash_sales == Decimal('200.00')
    assert closing.order_count == 5


# ===========================================================================
# DailyClosing.source — campo e default
# ===========================================================================

@pytest.mark.django_db
def test_daily_closing_default_source_is_manual():
    """Fechamentos criados manualmente têm source=MANUAL por padrão."""
    closing = DailyClosingFactory(date=date.today() - timedelta(days=10))
    assert closing.source == DailyClosing.ClosingSource.MANUAL


# ===========================================================================
# View — context e POST com source=ORDERS
# ===========================================================================

@pytest.mark.django_db
def test_closing_view_context_has_orders_source_flag(superuser_client):
    """View passa closing_is_orders_source=True quando source=ORDERS."""
    today = date.today()
    DailyClosingFactory(
        date=today,
        order_count=3,
        cash_sales=Decimal('60.00'),
        pix_sales=Decimal('0.00'),
        card_sales=Decimal('0.00'),
        source=DailyClosing.ClosingSource.ORDERS,
    )

    response = superuser_client.get(f'/fechamento/{today.isoformat()}/')
    assert response.status_code == 200
    assert response.context['closing_is_orders_source'] is True


@pytest.mark.django_db
def test_closing_view_context_orders_source_false_for_manual(superuser_client):
    """View passa closing_is_orders_source=False quando source=MANUAL."""
    today = date.today()
    DailyClosingFactory(
        date=today,
        source=DailyClosing.ClosingSource.MANUAL,
    )

    response = superuser_client.get(f'/fechamento/{today.isoformat()}/')
    assert response.status_code == 200
    assert response.context['closing_is_orders_source'] is False


@pytest.mark.django_db
def test_closing_post_does_not_overwrite_orders_source_sales(superuser_client):
    """POST na tela de fechamento não sobrescreve valores quando source=ORDERS."""
    today = date.today()
    closing = DailyClosingFactory(
        date=today,
        order_count=5,
        cash_sales=Decimal('100.00'),
        pix_sales=Decimal('200.00'),
        card_sales=Decimal('50.00'),
        source=DailyClosing.ClosingSource.ORDERS,
    )

    # Usuário tenta enviar valores manuais diferentes (campos readonly, mas POST direto)
    superuser_client.post(f'/fechamento/{today.isoformat()}/', {
        'order_count': '999',
        'cash_sales': '999.00',
        'pix_sales': '999.00',
        'card_sales': '999.00',
        'notes': 'obs nova',
    })

    closing.refresh_from_db()
    # Valores de vendas preservados (recalculados a partir dos pedidos — nenhum pedido = zeros)
    assert closing.source == DailyClosing.ClosingSource.ORDERS
    assert closing.cash_sales != Decimal('999.00')
    assert closing.pix_sales != Decimal('999.00')
    assert closing.card_sales != Decimal('999.00')
    # Observação deve ter sido salva
    assert closing.notes == 'obs nova'
