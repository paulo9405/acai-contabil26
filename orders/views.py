from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.views import View

from orders.models import Order, ProductVariant, Addon
from orders.selectors import get_catalog_json
from orders.services import create_order


def _has_order_permission(user):
    return user.is_superuser or user.groups.filter(name='Operacao').exists()


class OrderCreateView(LoginRequiredMixin, View):
    template_name = 'orders/order_form.html'

    def _context(self, post_data=None):
        return {
            'catalog_json': get_catalog_json(),
            'today': date.today().isoformat(),
            'payment_choices': Order.PaymentMethod.choices,
            'post_data': post_data or {},
        }

    def get(self, request):
        if not _has_order_permission(request.user):
            raise PermissionDenied
        return render(request, self.template_name, self._context())

    def post(self, request):
        if not _has_order_permission(request.user):
            raise PermissionDenied

        def safe_decimal(val):
            try:
                v = Decimal(str(val).replace(',', '.').strip())
                return v if v >= Decimal('0') else None
            except (InvalidOperation, AttributeError):
                return None

        comanda_number = request.POST.get('comanda_number', '').strip()
        order_date_str = request.POST.get('order_date', '').strip()
        order_time_str = request.POST.get('order_time', '').strip()
        payment_method = request.POST.get('payment_method', '').strip()
        informed_total_str = request.POST.get('informed_total', '').strip()
        notes = request.POST.get('notes', '').strip()

        variant_ids = request.POST.getlist('item_variant_id[]')
        quantities = request.POST.getlist('item_quantity[]')
        addon_id_lists = request.POST.getlist('item_addon_ids[]')

        errors = []

        if not comanda_number:
            errors.append('Número da comanda é obrigatório.')
        if not order_date_str:
            errors.append('Data é obrigatória.')
        if not order_time_str:
            errors.append('Horário é obrigatório.')
        if not payment_method:
            errors.append('Forma de pagamento é obrigatória.')
        if not variant_ids:
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
            for msg in errors:
                messages.error(request, msg)
            return render(request, self.template_name, self._context(post_data=request.POST))

        items = []
        for i, vid in enumerate(variant_ids):
            try:
                variant = ProductVariant.objects.select_related('product', 'size').get(pk=vid, active=True)
            except (ProductVariant.DoesNotExist, ValueError):
                errors.append(f'Produto inválido no item {i + 1}.')
                continue

            try:
                qty = max(1, int(quantities[i]) if i < len(quantities) else 1)
            except (ValueError, TypeError):
                qty = 1

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
            for msg in errors:
                messages.error(request, msg)
            return render(request, self.template_name, self._context(post_data=request.POST))

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
            )
            messages.success(
                request,
                f'Pedido #{order.pk} lançado com sucesso! Total: R$ {order.total}'
            )
            return redirect('order-create')
        except Exception as exc:
            messages.error(request, f'Erro ao lançar pedido: {exc}')
            return render(request, self.template_name, self._context(post_data=request.POST))
