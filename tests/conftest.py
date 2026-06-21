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
