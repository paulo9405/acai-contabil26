"""
Services for the orders app — business logic and writes.

Convenções:
- Funções keyword-only (*)
- Escrita e regras de negócio aqui; leitura em selectors.py
- Sem signals: recalcular explicitamente
"""

from decimal import Decimal
from django.db import transaction
from django.db.models import Sum, Q
from django.utils import timezone

from orders.models import Order, OrderItem, OrderItemAddon, Product

_UNSET = object()  # sentinel para distinguir "não passou" de None em update_order


# ---------------------------------------------------------------------------
# recalculate_closing_from_orders
# ---------------------------------------------------------------------------

def recalculate_closing_from_orders(*, date):
    """
    Cria ou atualiza o DailyClosing do dia com base nos pedidos ACTIVE.

    Regras:
    - Se não existe fechamento: cria com source='ORDERS'.
    - Se existe com source='ORDERS': atualiza valores.
    - Se existe com source='MANUAL': não toca (fonte manual tem precedência).

    Retorna o DailyClosing resultante (ou None se existia MANUAL e não foi alterado).
    """
    from finance.models import DailyClosing
    from finance.services import create_daily_closing, update_daily_closing

    agg = Order.objects.filter(
        order_date=date,
        status=Order.Status.ACTIVE,
    ).aggregate(
        total_count=Sum('id', default=0),  # Count via Sum trick — usamos Count abaixo
        cash=Sum('total', filter=Q(payment_method=Order.PaymentMethod.CASH)),
        pix=Sum('total', filter=Q(payment_method=Order.PaymentMethod.PIX)),
        card=Sum('total', filter=Q(payment_method=Order.PaymentMethod.CARD)),
    )

    # Contar separadamente (mais legível)
    order_count = Order.objects.filter(order_date=date, status=Order.Status.ACTIVE).count()
    cash_sales = agg['cash'] or Decimal('0.00')
    pix_sales = agg['pix'] or Decimal('0.00')
    card_sales = agg['card'] or Decimal('0.00')

    try:
        closing = DailyClosing.objects.get(date=date)
        if closing.source != DailyClosing.ClosingSource.ORDERS:
            # Fechamento manual — não sobrescrever
            return closing
        update_daily_closing(
            closing=closing,
            order_count=order_count,
            cash_sales=cash_sales,
            pix_sales=pix_sales,
            card_sales=card_sales,
        )
        return closing
    except DailyClosing.DoesNotExist:
        return create_daily_closing(
            date=date,
            order_count=order_count,
            cash_sales=cash_sales,
            pix_sales=pix_sales,
            card_sales=card_sales,
            source=DailyClosing.ClosingSource.ORDERS,
        )


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _resolve_addon_assignments(variant, addons):
    """
    Distribui adicionais entre incluídos (grátis) e pagos.

    Para produtos BUILD_YOUR_OWN: os primeiros N adicionais com is_free_option=True
    entram como incluídos (is_included=True, line_total=0). Os demais são pagos.
    Para outros tipos de produto: todos os adicionais são pagos.

    Retorna (addons_total, lista de dicts prontos para OrderItemAddon.create).
    """
    is_build_your_own = variant.product.product_type == Product.ProductType.BUILD_YOUR_OWN
    limit = variant.included_addons_limit if is_build_your_own else 0
    included_count = 0

    addons_total = Decimal('0.00')
    assignments = []

    for addon in addons:
        can_be_free = is_build_your_own and addon.is_free_option and included_count < limit

        if can_be_free:
            is_included = True
            unit_price = Decimal('0.00')
            line_total = Decimal('0.00')
            included_count += 1
        else:
            is_included = False
            unit_price = addon.price
            line_total = addon.price  # quantity sempre 1 na v1
            addons_total += line_total

        assignments.append({
            'addon': addon,
            'name': addon.name,
            'unit_price': unit_price,
            'is_included': is_included,
            'line_total': line_total,
        })

    return addons_total, assignments


# ---------------------------------------------------------------------------
# create_order
# ---------------------------------------------------------------------------

def _create_catalog_item(*, order, item_data):
    """Cria um OrderItem de catálogo e retorna o line_total."""
    variant = item_data['variant']
    quantity = item_data['quantity']
    addons = item_data.get('addons', [])

    product = variant.product
    size = variant.size

    addons_total, addon_assignments = _resolve_addon_assignments(variant, addons)

    unit_price = variant.price
    line_total = (unit_price + addons_total) * quantity

    order_item = OrderItem.objects.create(
        order=order,
        item_type=OrderItem.ItemType.CATALOG,
        product=product,
        variant=variant,
        quantity=quantity,
        product_name=product.name,
        variant_name=size.name if size else '',
        size_name=size.name if size else '',
        unit_price=unit_price,
        addons_total=addons_total,
        line_total=line_total,
    )

    for a in addon_assignments:
        OrderItemAddon.objects.create(
            order_item=order_item,
            addon=a['addon'],
            name=a['name'],
            unit_price=a['unit_price'],
            quantity=1,
            is_included=a['is_included'],
            line_total=a['line_total'],
        )

    return line_total


def _create_manual_item(*, order, item_data):
    """Cria um OrderItem avulso (MANUAL) e retorna o line_total."""
    description = str(item_data.get('description', '')).strip()
    unit_price = item_data.get('unit_price')
    quantity = item_data.get('quantity', 1)

    if not description:
        raise ValueError('Descrição é obrigatória para item avulso.')
    if unit_price is None or unit_price <= Decimal('0.00'):
        raise ValueError('Valor unitário deve ser maior que zero para item avulso.')

    line_total = unit_price * quantity

    OrderItem.objects.create(
        order=order,
        item_type=OrderItem.ItemType.MANUAL,
        product=None,
        variant=None,
        quantity=quantity,
        product_name=description,
        variant_name='',
        size_name='',
        unit_price=unit_price,
        addons_total=Decimal('0.00'),
        line_total=line_total,
    )

    return line_total


def create_order(*, comanda_number, order_date, order_time, payment_method, items, created_by, notes='', informed_total=None, idempotency_key=None):
    """
    Cria um pedido completo com itens e adicionais em transaction.atomic.

    Se `idempotency_key` for fornecida e já existir um pedido com essa chave,
    retorna o pedido existente sem criar um novo (idempotência contra duplo submit).

    Parâmetro `items`: lista de dicts. Cada dict pode ser:

    Item de catálogo (padrão):
        - 'variant': ProductVariant
        - 'quantity': int (>= 1)
        - 'addons': list[Addon] (opcional, default [])
        - 'item_type': 'CATALOG' (opcional, inferido automaticamente)

    Item avulso (manual):
        - 'item_type': OrderItem.ItemType.MANUAL  (obrigatório para identificar)
        - 'description': str  (obrigatório — armazenado em product_name)
        - 'unit_price': Decimal  (obrigatório, > 0)
        - 'quantity': int (>= 1)

    Retorna o Order criado.
    """
    if idempotency_key:
        try:
            return Order.objects.get(idempotency_key=idempotency_key)
        except Order.DoesNotExist:
            pass

    with transaction.atomic():
        order = Order.objects.create(
            comanda_number=comanda_number,
            order_date=order_date,
            order_time=order_time,
            payment_method=payment_method,
            total=Decimal('0.00'),
            informed_total=informed_total,
            notes=notes,
            status=Order.Status.ACTIVE,
            created_by=created_by,
            idempotency_key=idempotency_key,
        )

        order_total = Decimal('0.00')

        for item_data in items:
            item_type = item_data.get('item_type', OrderItem.ItemType.CATALOG)
            if item_type == OrderItem.ItemType.MANUAL:
                order_total += _create_manual_item(order=order, item_data=item_data)
            else:
                order_total += _create_catalog_item(order=order, item_data=item_data)

        order.total = order_total
        order.save(update_fields=['total', 'updated_at'])

    today = timezone.localdate()
    if order_date == today:
        recalculate_closing_from_orders(date=order_date)

    return order


# ---------------------------------------------------------------------------
# cancel_order
# ---------------------------------------------------------------------------

def cancel_order(*, order, cancelled_by, reason):
    """
    Cancela um pedido com auditoria completa. `reason` é obrigatório.
    Não faz delete físico — apenas muda status para CANCELLED.
    """
    if not reason or not reason.strip():
        raise ValueError('Motivo de cancelamento é obrigatório.')

    if order.status == Order.Status.CANCELLED:
        raise ValueError('Este pedido já está cancelado.')

    order.status = Order.Status.CANCELLED
    order.cancelled_at = timezone.now()
    order.cancelled_by = cancelled_by
    order.cancel_reason = reason.strip()
    order.save(update_fields=['status', 'cancelled_at', 'cancelled_by', 'cancel_reason', 'updated_at'])

    today = timezone.localdate()
    if order.order_date == today:
        recalculate_closing_from_orders(date=order.order_date)

    return order


# ---------------------------------------------------------------------------
# update_order
# ---------------------------------------------------------------------------

def update_order(*, order, updated_by, comanda_number=None, order_time=None, payment_method=None, notes=None, informed_total=_UNSET):
    """
    Atualiza campos do cabeçalho do pedido, verificando a janela de edição (DA-17).

    Funcionários do grupo Operacao só podem editar enquanto não existir DailyClosing
    para a data do pedido. Superusuários podem editar sempre.

    Passa `informed_total=None` para limpar o campo.
    Omite o parâmetro para não alterar o campo.
    """
    from finance.models import DailyClosing

    if not updated_by.is_superuser:
        if DailyClosing.objects.filter(date=order.order_date).exists():
            raise PermissionError(
                'O dia já foi fechado. Apenas administradores podem alterar este pedido.'
            )

    update_fields = ['updated_at']

    if comanda_number is not None:
        order.comanda_number = comanda_number
        update_fields.append('comanda_number')

    if order_time is not None:
        order.order_time = order_time
        update_fields.append('order_time')

    if payment_method is not None:
        order.payment_method = payment_method
        update_fields.append('payment_method')

    if notes is not None:
        order.notes = notes
        update_fields.append('notes')

    if informed_total is not _UNSET:
        order.informed_total = informed_total
        update_fields.append('informed_total')

    order.save(update_fields=update_fields)
    return order
