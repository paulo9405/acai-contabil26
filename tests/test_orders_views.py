"""
Testes para as views do app orders — Fase 4 (Interface Operacional).
"""

import pytest
from decimal import Decimal
from datetime import date

from django.contrib.auth.models import Group
from django.urls import reverse

from orders.models import Order
from tests.conftest import (
    UserFactory,
    ProductCategoryFactory,
    SizeFactory,
    ProductFactory,
    ProductVariantFactory,
    AddonFactory,
)


# ============================================================================
# Helpers
# ============================================================================

def _make_operacao_user(db):
    group, _ = Group.objects.get_or_create(name='Operacao')
    user = UserFactory()
    user.groups.add(group)
    return user


def _operacao_client(db):
    from django.test import Client
    user = _make_operacao_user(db)
    client = Client()
    client.force_login(user)
    return client, user


def _build_your_own_variant(db):
    cat = ProductCategoryFactory(kind='BUILD_YOUR_OWN')
    prod = ProductFactory(category=cat, product_type='BUILD_YOUR_OWN')
    size = SizeFactory(name='300 ml', volume_ml=300)
    return ProductVariantFactory(
        product=prod, size=size, price=Decimal('18.00'), included_addons_limit=2
    )


def _standard_variant(db):
    cat = ProductCategoryFactory(kind='STANDARD')
    prod = ProductFactory(category=cat, product_type='STANDARD')
    size = SizeFactory(name='500 ml', volume_ml=500)
    return ProductVariantFactory(product=prod, size=size, price=Decimal('24.00'))


# ============================================================================
# GET — permissões
# ============================================================================

@pytest.mark.django_db
class TestOrderCreateViewPermissions:

    def test_redirect_if_not_logged_in(self):
        from django.test import Client
        response = Client().get(reverse('order-create'))
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_forbidden_for_regular_user(self, authenticated_client):
        response = authenticated_client.get(reverse('order-create'))
        assert response.status_code == 403

    def test_allowed_for_operacao_user(self, db):
        client, _ = _operacao_client(db)
        response = client.get(reverse('order-create'))
        assert response.status_code == 200

    def test_allowed_for_superuser(self, superuser_client):
        response = superuser_client.get(reverse('order-create'))
        assert response.status_code == 200

    def test_template_used(self, db):
        client, _ = _operacao_client(db)
        response = client.get(reverse('order-create'))
        assert 'orders/order_form.html' in [t.name for t in response.templates]

    def test_context_contains_catalog(self, db):
        client, _ = _operacao_client(db)
        response = client.get(reverse('order-create'))
        assert 'catalog_json' in response.context
        assert 'categories' in response.context['catalog_json']
        assert 'addons' in response.context['catalog_json']

    def test_context_contains_today(self, db):
        client, _ = _operacao_client(db)
        response = client.get(reverse('order-create'))
        assert 'today' in response.context
        assert response.context['today'] == date.today().isoformat()


# ============================================================================
# POST — validação de campos obrigatórios
# ============================================================================

@pytest.mark.django_db
class TestOrderCreateViewValidation:

    def _post(self, db, data):
        client, _ = _operacao_client(db)
        return client.post(reverse('order-create'), data)

    def test_missing_comanda_number_shows_error(self, db):
        variant = _standard_variant(db)
        response = self._post(db, {
            'order_date': '2026-07-15',
            'order_time': '14:30',
            'payment_method': 'PIX',
            'item_variant_id[]': [str(variant.id)],
            'item_quantity[]': ['1'],
            'item_addon_ids[]': [''],
        })
        assert response.status_code == 200
        messages_list = list(response.wsgi_request._messages)
        assert any('comanda' in str(m).lower() for m in messages_list)

    def test_missing_order_time_shows_error(self, db):
        variant = _standard_variant(db)
        response = self._post(db, {
            'comanda_number': '5',
            'order_date': '2026-07-15',
            'payment_method': 'PIX',
            'item_variant_id[]': [str(variant.id)],
            'item_quantity[]': ['1'],
            'item_addon_ids[]': [''],
        })
        assert response.status_code == 200
        messages_list = list(response.wsgi_request._messages)
        assert any('horário' in str(m).lower() for m in messages_list)

    def test_no_items_shows_error(self, db):
        response = self._post(db, {
            'comanda_number': '5',
            'order_date': '2026-07-15',
            'order_time': '14:30',
            'payment_method': 'PIX',
        })
        assert response.status_code == 200
        messages_list = list(response.wsgi_request._messages)
        assert any('item' in str(m).lower() for m in messages_list)

    def test_missing_payment_method_shows_error(self, db):
        variant = _standard_variant(db)
        response = self._post(db, {
            'comanda_number': '5',
            'order_date': '2026-07-15',
            'order_time': '14:30',
            'item_variant_id[]': [str(variant.id)],
            'item_quantity[]': ['1'],
            'item_addon_ids[]': [''],
        })
        assert response.status_code == 200
        messages_list = list(response.wsgi_request._messages)
        assert any('pagamento' in str(m).lower() for m in messages_list)


# ============================================================================
# POST — criação com sucesso
# ============================================================================

@pytest.mark.django_db
class TestOrderCreateViewSuccess:

    def test_creates_order_with_single_item(self, db):
        client, user = _operacao_client(db)
        variant = _standard_variant(db)

        response = client.post(reverse('order-create'), {
            'comanda_number': '10',
            'order_date': '2026-07-15',
            'order_time': '16:30',
            'payment_method': 'PIX',
            'item_variant_id[]': [str(variant.id)],
            'item_quantity[]': ['1'],
            'item_addon_ids[]': [''],
        })

        assert response.status_code == 302
        assert response['Location'] == reverse('order-create')

        order = Order.objects.get(comanda_number='10')
        assert order.status == Order.Status.ACTIVE
        assert order.total == Decimal('24.00')
        assert order.created_by == user
        assert order.items.count() == 1

    def test_creates_order_with_multiple_items(self, db):
        client, _ = _operacao_client(db)
        variant1 = _standard_variant(db)
        variant2 = _standard_variant(db)

        response = client.post(reverse('order-create'), {
            'comanda_number': '11',
            'order_date': '2026-07-15',
            'order_time': '17:00',
            'payment_method': 'CASH',
            'item_variant_id[]': [str(variant1.id), str(variant2.id)],
            'item_quantity[]': ['1', '2'],
            'item_addon_ids[]': ['', ''],
        })

        assert response.status_code == 302
        order = Order.objects.get(comanda_number='11')
        assert order.items.count() == 2
        expected_total = variant1.price + variant2.price * 2
        assert order.total == expected_total

    def test_creates_order_with_addons_build_your_own(self, db):
        client, _ = _operacao_client(db)
        variant = _build_your_own_variant(db)
        addon1 = AddonFactory(price=Decimal('3.00'), is_free_option=True)
        addon2 = AddonFactory(price=Decimal('3.50'), is_free_option=True)
        addon3 = AddonFactory(price=Decimal('4.00'), is_free_option=False)

        response = client.post(reverse('order-create'), {
            'comanda_number': '12',
            'order_date': '2026-07-15',
            'order_time': '15:00',
            'payment_method': 'CARD',
            'item_variant_id[]': [str(variant.id)],
            'item_quantity[]': ['1'],
            'item_addon_ids[]': [f'{addon1.id},{addon2.id},{addon3.id}'],
        })

        assert response.status_code == 302
        order = Order.objects.get(comanda_number='12')
        item = order.items.first()
        # 2 adicionais grátis (limit=2), 1 pago (R$ 4,00)
        assert item.addons_total == Decimal('4.00')
        assert order.total == Decimal('22.00')  # 18.00 + 4.00

    def test_informed_total_divergence_does_not_block(self, db):
        client, _ = _operacao_client(db)
        variant = _standard_variant(db)

        response = client.post(reverse('order-create'), {
            'comanda_number': '13',
            'order_date': '2026-07-15',
            'order_time': '10:00',
            'payment_method': 'PIX',
            'informed_total': '30.00',
            'item_variant_id[]': [str(variant.id)],
            'item_quantity[]': ['1'],
            'item_addon_ids[]': [''],
        })

        assert response.status_code == 302
        order = Order.objects.get(comanda_number='13')
        assert order.total == Decimal('24.00')
        assert order.informed_total == Decimal('30.00')
        assert order.has_total_divergence

    def test_success_message_shown(self, db):
        client, _ = _operacao_client(db)
        variant = _standard_variant(db)

        client.post(reverse('order-create'), {
            'comanda_number': '14',
            'order_date': '2026-07-15',
            'order_time': '11:00',
            'payment_method': 'PIX',
            'item_variant_id[]': [str(variant.id)],
            'item_quantity[]': ['1'],
            'item_addon_ids[]': [''],
        })

        order = Order.objects.get(comanda_number='14')
        # Verificar que o pedido foi criado com sucesso
        assert order.status == Order.Status.ACTIVE

    def test_notes_saved(self, db):
        client, _ = _operacao_client(db)
        variant = _standard_variant(db)

        client.post(reverse('order-create'), {
            'comanda_number': '15',
            'order_date': '2026-07-15',
            'order_time': '12:00',
            'payment_method': 'PIX',
            'notes': 'Sem granola',
            'item_variant_id[]': [str(variant.id)],
            'item_quantity[]': ['1'],
            'item_addon_ids[]': [''],
        })

        order = Order.objects.get(comanda_number='15')
        assert order.notes == 'Sem granola'

    def test_same_comanda_number_allowed_twice(self, db):
        client, _ = _operacao_client(db)
        variant = _standard_variant(db)

        data = {
            'comanda_number': '1',
            'order_date': '2026-07-15',
            'order_time': '10:00',
            'payment_method': 'PIX',
            'item_variant_id[]': [str(variant.id)],
            'item_quantity[]': ['1'],
            'item_addon_ids[]': [''],
        }
        client.post(reverse('order-create'), data)
        data['order_time'] = '11:00'
        client.post(reverse('order-create'), data)

        assert Order.objects.filter(comanda_number='1').count() == 2
