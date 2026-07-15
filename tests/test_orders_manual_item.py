"""
Testes do adendo P-13 / DA-20 / DA-21 — Item avulso (MANUAL) no OrderItem.

Cobre:
- Model: clean() para CATALOG e MANUAL
- Service: create_order com itens MANUAL, pedidos mistos CATALOG+MANUAL
- Cálculo de totais
"""
import pytest
from decimal import Decimal
from datetime import date, time

from django.core.exceptions import ValidationError

from orders.models import Order, OrderItem, OrderItemAddon
from orders.services import create_order
from tests.conftest import (
    UserFactory,
    ProductCategoryFactory,
    SizeFactory,
    ProductFactory,
    ProductVariantFactory,
    OrderFactory,
    ManualOrderItemFactory,
)
from orders.models import Product, ProductCategory


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def variant(db):
    cat = ProductCategoryFactory(kind=ProductCategory.Kind.STANDARD)
    prod = ProductFactory(category=cat, product_type=Product.ProductType.STANDARD)
    size = SizeFactory(name='500 ml', volume_ml=500)
    return ProductVariantFactory(product=prod, size=size, price=Decimal('24.00'))


@pytest.fixture
def order_date():
    return date(2025, 1, 10)


@pytest.fixture
def order_time():
    return time(14, 30)


# ---------------------------------------------------------------------------
# Model clean() — item MANUAL
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestOrderItemCleanManual:

    def test_manual_item_valid(self, db):
        item = ManualOrderItemFactory.build(
            order=OrderFactory(),
            product=None,
            variant=None,
            product_name='Copo descartável',
            unit_price=Decimal('1.00'),
            quantity=1,
            addons_total=Decimal('0.00'),
            line_total=Decimal('1.00'),
        )
        item.clean()  # não deve levantar

    def test_manual_rejects_product_set(self, db, variant):
        order = OrderFactory()
        item = ManualOrderItemFactory.build(
            order=order,
            product=variant.product,
            variant=None,
        )
        with pytest.raises(ValidationError) as exc_info:
            item.clean()
        assert 'product' in exc_info.value.message_dict

    def test_manual_rejects_variant_set(self, db, variant):
        order = OrderFactory()
        item = ManualOrderItemFactory.build(
            order=order,
            product=None,
            variant=variant,
        )
        with pytest.raises(ValidationError) as exc_info:
            item.clean()
        assert 'variant' in exc_info.value.message_dict

    def test_manual_rejects_empty_description(self, db):
        order = OrderFactory()
        item = ManualOrderItemFactory.build(order=order, product_name='')
        with pytest.raises(ValidationError) as exc_info:
            item.clean()
        assert 'product_name' in exc_info.value.message_dict

    def test_manual_rejects_blank_description(self, db):
        order = OrderFactory()
        item = ManualOrderItemFactory.build(order=order, product_name='   ')
        with pytest.raises(ValidationError) as exc_info:
            item.clean()
        assert 'product_name' in exc_info.value.message_dict

    def test_manual_rejects_zero_unit_price(self, db):
        order = OrderFactory()
        item = ManualOrderItemFactory.build(order=order, unit_price=Decimal('0.00'))
        with pytest.raises(ValidationError) as exc_info:
            item.clean()
        assert 'unit_price' in exc_info.value.message_dict

    def test_manual_rejects_negative_unit_price(self, db):
        order = OrderFactory()
        item = ManualOrderItemFactory.build(order=order, unit_price=Decimal('-1.00'))
        with pytest.raises(ValidationError) as exc_info:
            item.clean()
        assert 'unit_price' in exc_info.value.message_dict


# ---------------------------------------------------------------------------
# Model clean() — item CATALOG
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestOrderItemCleanCatalog:

    def test_catalog_rejects_null_product(self, db, variant):
        order = OrderFactory()
        item = OrderItem(
            order=order,
            item_type=OrderItem.ItemType.CATALOG,
            product=None,
            variant=variant,
            quantity=1,
            product_name='Açaí',
            variant_name='500 ml',
            size_name='500 ml',
            unit_price=Decimal('24.00'),
            addons_total=Decimal('0.00'),
            line_total=Decimal('24.00'),
        )
        with pytest.raises(ValidationError) as exc_info:
            item.clean()
        assert 'product' in exc_info.value.message_dict

    def test_catalog_rejects_null_variant(self, db, variant):
        order = OrderFactory()
        item = OrderItem(
            order=order,
            item_type=OrderItem.ItemType.CATALOG,
            product=variant.product,
            variant=None,
            quantity=1,
            product_name='Açaí',
            variant_name='',
            size_name='',
            unit_price=Decimal('24.00'),
            addons_total=Decimal('0.00'),
            line_total=Decimal('24.00'),
        )
        with pytest.raises(ValidationError) as exc_info:
            item.clean()
        assert 'variant' in exc_info.value.message_dict

    def test_catalog_valid_with_product_and_variant(self, db, variant):
        order = OrderFactory()
        item = OrderItem(
            order=order,
            item_type=OrderItem.ItemType.CATALOG,
            product=variant.product,
            variant=variant,
            quantity=1,
            product_name=variant.product.name,
            variant_name=variant.size.name,
            size_name=variant.size.name,
            unit_price=variant.price,
            addons_total=Decimal('0.00'),
            line_total=variant.price,
        )
        item.clean()  # não deve levantar


# ---------------------------------------------------------------------------
# service create_order — item MANUAL
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCreateOrderManualItem:

    def test_manual_item_created_with_correct_fields(self, user, order_date, order_time):
        order = create_order(
            comanda_number='5',
            order_date=order_date,
            order_time=order_time,
            payment_method=Order.PaymentMethod.CASH,
            items=[{
                'item_type': OrderItem.ItemType.MANUAL,
                'description': 'Copo descartável',
                'unit_price': Decimal('1.00'),
                'quantity': 1,
            }],
            created_by=user,
        )

        assert order.pk is not None
        assert order.total == Decimal('1.00')

        item = order.items.first()
        assert item.item_type == OrderItem.ItemType.MANUAL
        assert item.product is None
        assert item.variant is None
        assert item.product_name == 'Copo descartável'
        assert item.unit_price == Decimal('1.00')
        assert item.quantity == 1
        assert item.addons_total == Decimal('0.00')
        assert item.line_total == Decimal('1.00')
        assert item.variant_name == ''
        assert item.size_name == ''

    def test_manual_item_no_addons_created(self, user, order_date, order_time):
        order = create_order(
            comanda_number='6',
            order_date=order_date,
            order_time=order_time,
            payment_method=Order.PaymentMethod.PIX,
            items=[{
                'item_type': OrderItem.ItemType.MANUAL,
                'description': 'Taxa de entrega',
                'unit_price': Decimal('5.00'),
                'quantity': 1,
            }],
            created_by=user,
        )
        item = order.items.first()
        assert item.addons.count() == 0

    def test_manual_item_quantity_multiplies_total(self, user, order_date, order_time):
        order = create_order(
            comanda_number='7',
            order_date=order_date,
            order_time=order_time,
            payment_method=Order.PaymentMethod.CARD,
            items=[{
                'item_type': OrderItem.ItemType.MANUAL,
                'description': 'Embalagem',
                'unit_price': Decimal('2.50'),
                'quantity': 3,
            }],
            created_by=user,
        )
        item = order.items.first()
        assert item.line_total == Decimal('7.50')
        assert order.total == Decimal('7.50')

    def test_manual_item_raises_on_empty_description(self, user, order_date, order_time):
        with pytest.raises(ValueError, match='Descrição'):
            create_order(
                comanda_number='8',
                order_date=order_date,
                order_time=order_time,
                payment_method=Order.PaymentMethod.PIX,
                items=[{
                    'item_type': OrderItem.ItemType.MANUAL,
                    'description': '',
                    'unit_price': Decimal('1.00'),
                    'quantity': 1,
                }],
                created_by=user,
            )

    def test_manual_item_raises_on_blank_description(self, user, order_date, order_time):
        with pytest.raises(ValueError, match='Descrição'):
            create_order(
                comanda_number='9',
                order_date=order_date,
                order_time=order_time,
                payment_method=Order.PaymentMethod.PIX,
                items=[{
                    'item_type': OrderItem.ItemType.MANUAL,
                    'description': '   ',
                    'unit_price': Decimal('1.00'),
                    'quantity': 1,
                }],
                created_by=user,
            )

    def test_manual_item_raises_on_zero_price(self, user, order_date, order_time):
        with pytest.raises(ValueError, match='Valor unitário'):
            create_order(
                comanda_number='10',
                order_date=order_date,
                order_time=order_time,
                payment_method=Order.PaymentMethod.PIX,
                items=[{
                    'item_type': OrderItem.ItemType.MANUAL,
                    'description': 'Item inválido',
                    'unit_price': Decimal('0.00'),
                    'quantity': 1,
                }],
                created_by=user,
            )

    def test_manual_item_raises_on_none_price(self, user, order_date, order_time):
        with pytest.raises(ValueError, match='Valor unitário'):
            create_order(
                comanda_number='11',
                order_date=order_date,
                order_time=order_time,
                payment_method=Order.PaymentMethod.PIX,
                items=[{
                    'item_type': OrderItem.ItemType.MANUAL,
                    'description': 'Item inválido',
                    'unit_price': None,
                    'quantity': 1,
                }],
                created_by=user,
            )

    def test_manual_item_description_stripped(self, user, order_date, order_time):
        order = create_order(
            comanda_number='12',
            order_date=order_date,
            order_time=order_time,
            payment_method=Order.PaymentMethod.PIX,
            items=[{
                'item_type': OrderItem.ItemType.MANUAL,
                'description': '  Venda avulsa  ',
                'unit_price': Decimal('8.00'),
                'quantity': 1,
            }],
            created_by=user,
        )
        item = order.items.first()
        assert item.product_name == 'Venda avulsa'


# ---------------------------------------------------------------------------
# Pedido misto: CATALOG + MANUAL
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestMixedOrder:

    def test_mixed_order_total_sums_both_types(self, user, variant, order_date, order_time):
        order = create_order(
            comanda_number='20',
            order_date=order_date,
            order_time=order_time,
            payment_method=Order.PaymentMethod.PIX,
            items=[
                {
                    'variant': variant,
                    'quantity': 1,
                    'addons': [],
                },
                {
                    'item_type': OrderItem.ItemType.MANUAL,
                    'description': 'Copo descartável',
                    'unit_price': Decimal('1.00'),
                    'quantity': 1,
                },
            ],
            created_by=user,
        )
        # CATALOG: 24.00, MANUAL: 1.00 → total = 25.00
        assert order.total == Decimal('25.00')
        assert order.items.count() == 2

    def test_mixed_order_catalog_item_has_correct_type(self, user, variant, order_date, order_time):
        order = create_order(
            comanda_number='21',
            order_date=order_date,
            order_time=order_time,
            payment_method=Order.PaymentMethod.CASH,
            items=[
                {'variant': variant, 'quantity': 1, 'addons': []},
                {
                    'item_type': OrderItem.ItemType.MANUAL,
                    'description': 'Embalagem',
                    'unit_price': Decimal('2.00'),
                    'quantity': 1,
                },
            ],
            created_by=user,
        )
        types = set(order.items.values_list('item_type', flat=True))
        assert OrderItem.ItemType.CATALOG in types
        assert OrderItem.ItemType.MANUAL in types

    def test_mixed_order_catalog_item_has_addons_manual_does_not(self, user, variant, order_date, order_time):
        from tests.conftest import AddonFactory
        addon = AddonFactory(price=Decimal('3.00'), is_free_option=False)

        order = create_order(
            comanda_number='22',
            order_date=order_date,
            order_time=order_time,
            payment_method=Order.PaymentMethod.PIX,
            items=[
                {'variant': variant, 'quantity': 1, 'addons': [addon]},
                {
                    'item_type': OrderItem.ItemType.MANUAL,
                    'description': 'Taxa',
                    'unit_price': Decimal('5.00'),
                    'quantity': 1,
                },
            ],
            created_by=user,
        )
        catalog_item = order.items.get(item_type=OrderItem.ItemType.CATALOG)
        manual_item = order.items.get(item_type=OrderItem.ItemType.MANUAL)

        assert catalog_item.addons.count() == 1
        assert manual_item.addons.count() == 0
        assert manual_item.addons_total == Decimal('0.00')

    def test_order_with_multiple_manual_items(self, user, order_date, order_time):
        order = create_order(
            comanda_number='23',
            order_date=order_date,
            order_time=order_time,
            payment_method=Order.PaymentMethod.CASH,
            items=[
                {
                    'item_type': OrderItem.ItemType.MANUAL,
                    'description': 'Copo descartável',
                    'unit_price': Decimal('1.00'),
                    'quantity': 2,
                },
                {
                    'item_type': OrderItem.ItemType.MANUAL,
                    'description': 'Promoção especial',
                    'unit_price': Decimal('15.00'),
                    'quantity': 1,
                },
            ],
            created_by=user,
        )
        # 1.00*2 + 15.00*1 = 17.00
        assert order.total == Decimal('17.00')
        assert order.items.count() == 2
        assert order.items.filter(item_type=OrderItem.ItemType.MANUAL).count() == 2


# ---------------------------------------------------------------------------
# item_type default
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestItemTypeDefault:

    def test_catalog_is_default_when_item_type_not_specified(self, user, variant, order_date, order_time):
        """item_type omitido no dict → cria como CATALOG."""
        order = create_order(
            comanda_number='30',
            order_date=order_date,
            order_time=order_time,
            payment_method=Order.PaymentMethod.PIX,
            items=[{'variant': variant, 'quantity': 1, 'addons': []}],
            created_by=user,
        )
        item = order.items.first()
        assert item.item_type == OrderItem.ItemType.CATALOG

    def test_existing_catalog_orders_unaffected(self, user, variant, order_date, order_time):
        """Compatibilidade retroativa: pedidos CATALOG existentes continuam funcionando."""
        order = create_order(
            comanda_number='31',
            order_date=order_date,
            order_time=order_time,
            payment_method=Order.PaymentMethod.CARD,
            items=[
                {'variant': variant, 'quantity': 2, 'addons': []},
            ],
            created_by=user,
        )
        assert order.total == Decimal('48.00')  # 24.00 × 2
        item = order.items.first()
        assert item.item_type == OrderItem.ItemType.CATALOG
        assert item.product is not None
        assert item.variant is not None
