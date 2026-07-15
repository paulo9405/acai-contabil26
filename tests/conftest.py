"""
Configurações e fixtures compartilhadas para testes.
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.contrib.auth.models import User
from django.utils import timezone
import factory
from factory.django import DjangoModelFactory

from finance.models import ExpenseCategory, DailyClosing, Expense
from orders.models import ProductCategory, Size, Product, ProductVariant, Addon, Order, OrderItem, OrderItemAddon


# ============================================================================
# FACTORIES
# ============================================================================

class UserFactory(DjangoModelFactory):
    """Factory para criar usuários de teste."""
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    is_active = True
    is_staff = False
    is_superuser = False

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        if extracted:
            self.set_password(extracted)
        else:
            self.set_password('testpass123')


class ExpenseCategoryFactory(DjangoModelFactory):
    """Factory para criar categorias de despesa."""
    class Meta:
        model = ExpenseCategory

    name = factory.Sequence(lambda n: f'Categoria {n}')
    active = True


class DailyClosingFactory(DjangoModelFactory):
    """Factory para criar fechamentos diários."""
    class Meta:
        model = DailyClosing

    date = factory.LazyFunction(lambda: timezone.now().date())
    order_count = factory.Faker('random_int', min=10, max=50)
    cash_sales = factory.Faker('pydecimal', left_digits=4, right_digits=2, positive=True)
    pix_sales = factory.Faker('pydecimal', left_digits=4, right_digits=2, positive=True)
    card_sales = factory.Faker('pydecimal', left_digits=4, right_digits=2, positive=True)
    notes = factory.Faker('sentence')


class ExpenseFactory(DjangoModelFactory):
    """Factory para criar despesas."""
    class Meta:
        model = Expense

    date = factory.LazyFunction(lambda: timezone.now().date())
    category = factory.SubFactory(ExpenseCategoryFactory)
    amount = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True)
    description = factory.Faker('sentence')


class ProductCategoryFactory(DjangoModelFactory):
    """Factory para criar categorias de produto."""
    class Meta:
        model = ProductCategory

    name = factory.Sequence(lambda n: f'Categoria {n}')
    kind = ProductCategory.Kind.STANDARD
    sort_order = factory.Sequence(lambda n: n)
    active = True


class SizeFactory(DjangoModelFactory):
    """Factory para criar tamanhos."""
    class Meta:
        model = Size

    name = factory.Sequence(lambda n: f'{(n + 1) * 300} ml')
    volume_ml = factory.Sequence(lambda n: (n + 1) * 300)
    sort_order = factory.Sequence(lambda n: n)
    active = True


class ProductFactory(DjangoModelFactory):
    """Factory para criar produtos."""
    class Meta:
        model = Product

    category = factory.SubFactory(ProductCategoryFactory)
    name = factory.Sequence(lambda n: f'Produto {n}')
    description = ''
    product_type = Product.ProductType.STANDARD
    sort_order = factory.Sequence(lambda n: n)
    active = True


class ProductVariantFactory(DjangoModelFactory):
    """Factory para criar variações de produto."""
    class Meta:
        model = ProductVariant

    product = factory.SubFactory(ProductFactory)
    size = factory.SubFactory(SizeFactory)
    price = Decimal('18.00')
    included_addons_limit = 0
    active = True


class AddonFactory(DjangoModelFactory):
    """Factory para criar adicionais."""
    class Meta:
        model = Addon

    name = factory.Sequence(lambda n: f'Adicional {n}')
    price = Decimal('3.00')
    is_free_option = False
    sort_order = factory.Sequence(lambda n: n)
    active = True


class OrderFactory(DjangoModelFactory):
    """Factory para criar pedidos."""
    class Meta:
        model = Order

    comanda_number = factory.Sequence(lambda n: str(n + 1))
    order_date = factory.LazyFunction(lambda: timezone.now().date())
    order_time = factory.LazyFunction(lambda: timezone.now().time().replace(second=0, microsecond=0))
    payment_method = Order.PaymentMethod.PIX
    total = Decimal('18.00')
    informed_total = None
    status = Order.Status.ACTIVE
    notes = ''
    created_by = factory.SubFactory(UserFactory)


class OrderItemFactory(DjangoModelFactory):
    """Factory para criar itens de pedido do tipo CATALOG."""
    class Meta:
        model = OrderItem

    order = factory.SubFactory(OrderFactory)
    item_type = OrderItem.ItemType.CATALOG
    product = factory.SubFactory(ProductFactory)
    variant = factory.SubFactory(ProductVariantFactory)
    quantity = 1
    product_name = 'Produto Teste'
    variant_name = '300 ml'
    size_name = '300 ml'
    unit_price = Decimal('18.00')
    addons_total = Decimal('0.00')
    line_total = Decimal('18.00')


class ManualOrderItemFactory(DjangoModelFactory):
    """Factory para criar itens de pedido do tipo MANUAL (avulso)."""
    class Meta:
        model = OrderItem

    order = factory.SubFactory(OrderFactory)
    item_type = OrderItem.ItemType.MANUAL
    product = None
    variant = None
    quantity = 1
    product_name = 'Copo descartável'
    variant_name = ''
    size_name = ''
    unit_price = Decimal('1.00')
    addons_total = Decimal('0.00')
    line_total = Decimal('1.00')


class OrderItemAddonFactory(DjangoModelFactory):
    """Factory para criar adicionais de item de pedido."""
    class Meta:
        model = OrderItemAddon

    order_item = factory.SubFactory(OrderItemFactory)
    addon = factory.SubFactory(AddonFactory)
    name = 'Adicional Teste'
    unit_price = Decimal('3.00')
    quantity = 1
    is_included = False
    line_total = Decimal('3.00')


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def user(db):
    """Cria um usuário comum."""
    return UserFactory()


@pytest.fixture
def superuser(db):
    """Cria um superusuário."""
    return UserFactory(is_superuser=True, is_staff=True)


@pytest.fixture
def expense_category(db):
    """Cria uma categoria de despesa ativa."""
    return ExpenseCategoryFactory()


@pytest.fixture
def inactive_expense_category(db):
    """Cria uma categoria de despesa inativa."""
    return ExpenseCategoryFactory(active=False)


@pytest.fixture
def daily_closing(db):
    """Cria um fechamento diário."""
    return DailyClosingFactory()


@pytest.fixture
def expense(db, expense_category):
    """Cria uma despesa."""
    return ExpenseFactory(category=expense_category)


@pytest.fixture
def multiple_closings(db):
    """Cria múltiplos fechamentos para os últimos 7 dias."""
    today = timezone.now().date()
    closings = []
    for i in range(7):
        day = today - timedelta(days=i)
        closing = DailyClosingFactory(
            date=day,
            order_count=10 + i,
            cash_sales=Decimal('100.00') + Decimal(i * 10),
            pix_sales=Decimal('150.00') + Decimal(i * 10),
            card_sales=Decimal('200.00') + Decimal(i * 10)
        )
        closings.append(closing)
    return closings


@pytest.fixture
def multiple_expenses(db, expense_category):
    """Cria múltiplas despesas para os últimos 7 dias."""
    today = timezone.now().date()
    expenses = []
    for i in range(7):
        day = today - timedelta(days=i)
        expense = ExpenseFactory(
            date=day,
            category=expense_category,
            amount=Decimal('50.00') + Decimal(i * 5)
        )
        expenses.append(expense)
    return expenses


@pytest.fixture
def product_category(db):
    """Cria uma categoria de produto padrão."""
    return ProductCategoryFactory()


@pytest.fixture
def size(db):
    """Cria um tamanho padrão (300 ml)."""
    return SizeFactory(name='300 ml', volume_ml=300, sort_order=0)


@pytest.fixture
def product(db, product_category):
    """Cria um produto padrão."""
    return ProductFactory(category=product_category)


@pytest.fixture
def product_variant(db, product, size):
    """Cria uma variação de produto padrão."""
    return ProductVariantFactory(product=product, size=size)


@pytest.fixture
def addon(db):
    """Cria um adicional padrão."""
    return AddonFactory()


@pytest.fixture
def order(db, user):
    """Cria um pedido ativo."""
    return OrderFactory(created_by=user)


@pytest.fixture
def api_client():
    """Cliente Django para testes de views."""
    from django.test import Client
    return Client()


@pytest.fixture
def authenticated_client(user):
    """Cliente autenticado para testes de views."""
    from django.test import Client
    client = Client()
    client.force_login(user)
    return client


@pytest.fixture
def superuser_client(superuser):
    """Cliente autenticado como superuser."""
    from django.test import Client
    client = Client()
    client.force_login(superuser)
    return client
