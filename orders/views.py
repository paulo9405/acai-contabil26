import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from django.utils import timezone

from finance.forms import ReportFilterForm
from finance.models import DailyClosing
from orders.models import Order, OrderItem, ProductVariant, Addon
from orders.selectors import (
    get_catalog_json,
    get_daily_order_totals,
    get_divergences,
    get_liters_sold,
    get_order_detail,
    get_orders_by_date_with_items,
    get_orders_summary,
    get_peak_hours,
    get_sales_by_payment_method,
    get_top_addons,
    get_top_products,
    get_top_sizes,
)
from orders.services import create_order, update_order, cancel_order


def _has_order_permission(user):
    return user.is_superuser or user.groups.filter(name='Operacao').exists()


def _calculate_period_dates(period, custom_start, custom_end):
    today = timezone.localdate()
    if period == 'today':
        return today, today
    elif period == 'yesterday':
        yesterday = today - timedelta(1)
        return yesterday, yesterday
    elif period == 'last_7_days':
        return today - timedelta(6), today
    elif period == 'last_30_days':
        return today - timedelta(29), today
    elif period == 'this_month':
        return today.replace(day=1), today
    elif period == 'last_month':
        first_this = today.replace(day=1)
        last_prev = first_this - timedelta(1)
        return last_prev.replace(day=1), last_prev
    elif period == 'custom':
        return custom_start, custom_end
    return today.replace(day=1), today


class OrderCreateView(LoginRequiredMixin, View):
    template_name = 'orders/order_form.html'

    def _context(self, post_data=None, form_errors=None):
        return {
            'catalog_json': get_catalog_json(),
            'today': date.today().isoformat(),
            'payment_choices': Order.PaymentMethod.choices,
            'post_data': post_data or {},
            'form_errors': form_errors or [],
        }

    def get(self, request):
        if not _has_order_permission(request.user):
            raise PermissionDenied
        ctx = self._context()
        ctx['idempotency_key'] = str(uuid.uuid4())
        return render(request, self.template_name, ctx)

    def post(self, request):
        if not _has_order_permission(request.user):
            raise PermissionDenied

        def safe_decimal(val):
            try:
                v = Decimal(str(val).replace(',', '.').strip())
                return v if v >= Decimal('0') else None
            except (InvalidOperation, AttributeError):
                return None

        idempotency_key = request.POST.get('idempotency_key', '').strip() or None

        comanda_number = request.POST.get('comanda_number', '').strip()
        order_date_str = request.POST.get('order_date', '').strip()
        order_time_str = request.POST.get('order_time', '').strip()
        payment_method = request.POST.get('payment_method', '').strip()
        informed_total_str = request.POST.get('informed_total', '').strip()
        notes = request.POST.get('notes', '').strip()

        item_types = request.POST.getlist('item_type[]')
        variant_ids = request.POST.getlist('item_variant_id[]')
        quantities = request.POST.getlist('item_quantity[]')
        addon_id_lists = request.POST.getlist('item_addon_ids[]')
        manual_descriptions = request.POST.getlist('item_manual_description[]')
        manual_unit_prices = request.POST.getlist('item_manual_unit_price[]')

        # Compat: se item_type[] não vier (testes antigos), usa variant_ids como driver
        n_items = len(item_types) if item_types else len(variant_ids)

        errors = []

        if not comanda_number:
            errors.append('Número da comanda é obrigatório.')
        if not order_date_str:
            errors.append('Data é obrigatória.')
        if not order_time_str:
            errors.append('Horário é obrigatório.')
        if not payment_method:
            errors.append('Forma de pagamento é obrigatória.')
        if n_items == 0:
            errors.append('Adicione pelo menos um item ao pedido.')

        order_date = None
        order_time = None
        try:
            order_date = datetime.strptime(order_date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            if order_date_str:
                errors.append('Data inválida.')

        try:
            order_time = datetime.strptime(order_time_str, '%H:%M').time()
        except (ValueError, TypeError):
            if order_time_str:
                errors.append('Horário inválido (use HH:MM).')

        informed_total = None
        if informed_total_str:
            informed_total = safe_decimal(informed_total_str)
            if informed_total is None:
                errors.append('Valor informado na comanda inválido.')

        if errors:
            ctx = self._context(post_data=request.POST, form_errors=errors)
            ctx['idempotency_key'] = idempotency_key or str(uuid.uuid4())
            return render(request, self.template_name, ctx)

        items = []
        for i in range(n_items):
            itype = item_types[i] if i < len(item_types) else OrderItem.ItemType.CATALOG

            try:
                qty = max(1, int(quantities[i]) if i < len(quantities) else 1)
            except (ValueError, TypeError):
                qty = 1

            if itype == OrderItem.ItemType.MANUAL:
                desc = (manual_descriptions[i] if i < len(manual_descriptions) else '').strip()
                price_str = manual_unit_prices[i] if i < len(manual_unit_prices) else ''
                price = safe_decimal(price_str)
                if not desc:
                    errors.append(f'Descrição obrigatória no item avulso {i + 1}.')
                    continue
                if price is None or price <= Decimal('0'):
                    errors.append(f'Valor inválido no item avulso {i + 1}.')
                    continue
                items.append({
                    'item_type': OrderItem.ItemType.MANUAL,
                    'description': desc,
                    'unit_price': price,
                    'quantity': qty,
                })
            else:
                vid = variant_ids[i] if i < len(variant_ids) else ''
                try:
                    variant = ProductVariant.objects.select_related('product', 'size').get(pk=vid, active=True)
                except (ProductVariant.DoesNotExist, ValueError):
                    errors.append(f'Produto inválido no item {i + 1}.')
                    continue
                addon_ids_str = addon_id_lists[i] if i < len(addon_id_lists) else ''
                addons = []
                if addon_ids_str:
                    for aid in addon_ids_str.split(','):
                        aid = aid.strip()
                        if aid:
                            try:
                                addons.append(Addon.objects.get(pk=int(aid), active=True))
                            except (Addon.DoesNotExist, ValueError):
                                pass
                items.append({'variant': variant, 'quantity': qty, 'addons': addons})

        if errors:
            ctx = self._context(post_data=request.POST, form_errors=errors)
            ctx['idempotency_key'] = idempotency_key or str(uuid.uuid4())
            return render(request, self.template_name, ctx)

        try:
            order = create_order(
                comanda_number=comanda_number,
                order_date=order_date,
                order_time=order_time,
                payment_method=payment_method,
                items=items,
                created_by=request.user,
                notes=notes,
                informed_total=informed_total,
                idempotency_key=idempotency_key,
            )
            messages.success(
                request,
                f'Pedido #{order.pk} lançado com sucesso! Total: R$ {order.total}'
            )
            return redirect('order-detail', pk=order.pk)
        except Exception as exc:
            messages.error(request, f'Erro ao lançar pedido: {exc}')
            return render(request, self.template_name, self._context(post_data=request.POST))


# ---------------------------------------------------------------------------
# OrderListView
# ---------------------------------------------------------------------------

class OrderListView(LoginRequiredMixin, View):
    template_name = 'orders/order_list.html'

    def get(self, request, order_date=None):
        if not _has_order_permission(request.user):
            raise PermissionDenied

        today = date.today()
        if order_date is None:
            list_date = today
        else:
            try:
                list_date = date.fromisoformat(order_date)
            except ValueError:
                list_date = today

        if list_date > today:
            list_date = today

        orders = get_orders_by_date_with_items(date=list_date)
        day_is_closed = DailyClosing.objects.filter(date=list_date).exists()

        active_orders = [o for o in orders if o.status == Order.Status.ACTIVE]
        total_active = sum(o.total for o in active_orders)

        context = {
            'orders': orders,
            'order_date': list_date,
            'today': today,
            'prev_date_str': (list_date - timedelta(1)).isoformat(),
            'next_date_str': (list_date + timedelta(1)).isoformat() if list_date < today else None,
            'day_is_closed': day_is_closed,
            'total_active': total_active,
            'count_active': len(active_orders),
            'can_cancel': request.user.is_superuser,
            'can_edit': request.user.is_superuser or not day_is_closed,
            'list_url_template': '/pedidos/PLACEHOLDER/',
        }
        return render(request, self.template_name, context)


# ---------------------------------------------------------------------------
# OrderDetailView
# ---------------------------------------------------------------------------

class OrderDetailView(LoginRequiredMixin, View):
    template_name = 'orders/order_detail.html'

    def get(self, request, pk):
        if not _has_order_permission(request.user):
            raise PermissionDenied

        order = get_object_or_404(Order, pk=pk)
        day_is_closed = DailyClosing.objects.filter(date=order.order_date).exists()

        context = {
            'order': get_order_detail(order_id=pk),
            'day_is_closed': day_is_closed,
            'can_edit': (
                order.status == Order.Status.ACTIVE
                and (request.user.is_superuser or not day_is_closed)
            ),
            'can_cancel': request.user.is_superuser and order.status == Order.Status.ACTIVE,
        }
        return render(request, self.template_name, context)


# ---------------------------------------------------------------------------
# OrderUpdateView
# ---------------------------------------------------------------------------

class OrderUpdateView(LoginRequiredMixin, View):
    template_name = 'orders/order_form_edit.html'

    def _get_editable_order(self, pk, user):
        order = get_object_or_404(Order, pk=pk)
        if not _has_order_permission(user):
            raise PermissionDenied
        if order.status == Order.Status.CANCELLED:
            raise PermissionDenied
        if not user.is_superuser:
            if DailyClosing.objects.filter(date=order.order_date).exists():
                raise PermissionDenied
        return order

    def _render_form(self, request, order, post_data=None):
        return render(request, self.template_name, {
            'order': order,
            'payment_choices': Order.PaymentMethod.choices,
            'post_data': post_data or {},
        })

    def get(self, request, pk):
        order = self._get_editable_order(pk, request.user)
        return self._render_form(request, order)

    def post(self, request, pk):
        order = self._get_editable_order(pk, request.user)

        def safe_decimal(val):
            try:
                v = Decimal(str(val).replace(',', '.').strip())
                return v if v >= Decimal('0') else None
            except (InvalidOperation, AttributeError):
                return None

        comanda_number = request.POST.get('comanda_number', '').strip()
        order_time_str = request.POST.get('order_time', '').strip()
        payment_method = request.POST.get('payment_method', '').strip()
        informed_total_str = request.POST.get('informed_total', '').strip()
        notes = request.POST.get('notes', '').strip()

        errors = []
        if not comanda_number:
            errors.append('Número da comanda é obrigatório.')
        if not order_time_str:
            errors.append('Horário é obrigatório.')
        if not payment_method:
            errors.append('Forma de pagamento é obrigatória.')

        order_time = None
        try:
            order_time = datetime.strptime(order_time_str, '%H:%M').time()
        except (ValueError, TypeError):
            if order_time_str:
                errors.append('Horário inválido (use HH:MM).')

        informed_total = None
        if informed_total_str:
            informed_total = safe_decimal(informed_total_str)
            if informed_total is None:
                errors.append('Valor informado inválido.')

        if errors:
            for msg in errors:
                messages.error(request, msg)
            return self._render_form(request, order, post_data=request.POST)

        try:
            update_order(
                order=order,
                updated_by=request.user,
                comanda_number=comanda_number,
                order_time=order_time,
                payment_method=payment_method,
                notes=notes,
                informed_total=informed_total,
            )
            messages.success(request, f'Pedido #{order.pk} atualizado com sucesso.')
            return redirect('order-detail', pk=order.pk)
        except PermissionError as exc:
            messages.error(request, str(exc))
            return redirect('order-detail', pk=order.pk)


# ---------------------------------------------------------------------------
# OrderCancelView
# ---------------------------------------------------------------------------

class OrderCancelView(LoginRequiredMixin, View):
    template_name = 'orders/order_cancel_confirm.html'

    def _get_cancellable_order(self, pk, user):
        if not user.is_superuser:
            raise PermissionDenied
        order = get_object_or_404(Order, pk=pk)
        return order

    def get(self, request, pk):
        order = self._get_cancellable_order(pk, request.user)
        if order.status == Order.Status.CANCELLED:
            messages.warning(request, 'Este pedido já está cancelado.')
            return redirect('order-detail', pk=pk)
        return render(request, self.template_name, {'order': order})

    def post(self, request, pk):
        order = self._get_cancellable_order(pk, request.user)
        if order.status == Order.Status.CANCELLED:
            messages.warning(request, 'Este pedido já está cancelado.')
            return redirect('order-detail', pk=pk)

        reason = request.POST.get('cancel_reason', '').strip()
        if not reason:
            messages.error(request, 'Motivo de cancelamento é obrigatório.')
            return render(request, self.template_name, {
                'order': order, 'post_data': request.POST,
            })

        try:
            cancel_order(order=order, cancelled_by=request.user, reason=reason)
            messages.success(request, f'Pedido #{order.pk} cancelado.')
            return redirect('order-list-date', order_date=order.order_date.isoformat())
        except ValueError as exc:
            messages.error(request, str(exc))
            return render(request, self.template_name, {'order': order})


# ---------------------------------------------------------------------------
# OrderReportView
# ---------------------------------------------------------------------------

_PAYMENT_LABELS = {
    Order.PaymentMethod.PIX: 'Pix',
    Order.PaymentMethod.CASH: 'Dinheiro',
    Order.PaymentMethod.CARD: 'Cartão',
}


class OrderReportView(LoginRequiredMixin, View):
    template_name = 'orders/order_report.html'

    def get(self, request):
        if not request.user.is_superuser:
            raise PermissionDenied

        form = ReportFilterForm(request.GET or {'period': 'this_month'})
        context = {'form': form}

        if form.is_valid():
            start_date, end_date = _calculate_period_dates(
                form.cleaned_data['period'],
                form.cleaned_data.get('start_date'),
                form.cleaned_data.get('end_date'),
            )
            context['start_date'] = start_date
            context['end_date'] = end_date
            context['period_label'] = dict(form.fields['period'].choices)[form.cleaned_data['period']]

            summary = get_orders_summary(start_date=start_date, end_date=end_date)
            context.update(summary)
            context['liters_sold'] = get_liters_sold(start_date=start_date, end_date=end_date)

            raw_payment = get_sales_by_payment_method(start_date=start_date, end_date=end_date)
            context['sales_by_payment'] = [
                {**row, 'label': _PAYMENT_LABELS.get(row['payment_method'], row['payment_method'])}
                for row in raw_payment
            ]

            context['top_products'] = get_top_products(start_date=start_date, end_date=end_date)
            context['top_sizes'] = get_top_sizes(start_date=start_date, end_date=end_date)
            context['top_addons'] = get_top_addons(start_date=start_date, end_date=end_date)
            context['peak_hours'] = get_peak_hours(start_date=start_date, end_date=end_date)
            context['divergences'] = get_divergences(start_date=start_date, end_date=end_date)
            context['daily_totals'] = get_daily_order_totals(start_date=start_date, end_date=end_date)

        return render(request, self.template_name, context)
