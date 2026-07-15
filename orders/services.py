"""
Services for the orders app — business logic and writes.

Convenções:
- Funções keyword-only (*)
- Escrita e regras de negócio aqui; leitura em selectors.py
- Sem signals: recalcular explicitamente
"""

from decimal import Decimal
from django.db import transaction
from django.utils import timezone

from orders.models import Order, OrderItem, OrderItemAddon, Product

_UNSET = object()  # sentinel para distinguir "não passou" de None em update_order


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

def create_order(*, comanda_number, order_date, order_time, payment_method, items, created_by, notes='', informed_total=None):
    """
    Cria um pedido completo com itens e adicionais em transaction.atomic.

    Parâmetro `items`: lista de dicts com:
        - 'variant': ProductVariant
        - 'quantity': int (>= 1)
        - 'addons': list[Addon] (opcional, default [])

    Retorna o Order criado.
    """
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
        )

        order_total = Decimal('0.00')

        for item_data in items:
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

            order_total += line_total

        order.total = order_total
        order.save(update_fields=['total', 'updated_at'])

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
