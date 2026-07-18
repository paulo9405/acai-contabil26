"""
Testes para os models da aplicação finance.
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from finance.models import DailyClosing, Expense
from tests.conftest import DailyClosingFactory, ExpenseCategoryFactory, ExpenseFactory

# ============================================================================
# TESTS - ExpenseCategory
# ============================================================================


@pytest.mark.django_db
class TestExpenseCategory:
    """Testes para o modelo ExpenseCategory."""

    def test_create_category(self):
        """Testa criação de categoria."""
        category = ExpenseCategoryFactory(name="Aluguel")
        assert category.name == "Aluguel"
        assert category.active is True
        assert str(category) == "Aluguel"

    def test_category_unique_name(self):
        """Testa que nome da categoria é único."""
        ExpenseCategoryFactory(name="Salários")
        with pytest.raises(Exception):  # IntegrityError
            ExpenseCategoryFactory(name="Salários")

    def test_category_inactive(self):
        """Testa categoria inativa."""
        category = ExpenseCategoryFactory(active=False)
        assert category.active is False

    def test_category_str_method(self):
        """Testa método __str__."""
        category = ExpenseCategoryFactory(name="Energia")
        assert str(category) == "Energia"


# ============================================================================
# TESTS - DailyClosing
# ============================================================================


@pytest.mark.django_db
class TestDailyClosing:
    """Testes para o modelo DailyClosing."""

    def test_create_closing(self):
        """Testa criação de fechamento."""
        closing = DailyClosingFactory(
            date=timezone.now().date(),
            order_count=20,
            cash_sales=Decimal("100.00"),
            pix_sales=Decimal("150.00"),
            card_sales=Decimal("250.00"),
        )
        assert closing.order_count == 20
        assert closing.cash_sales == Decimal("100.00")
        assert closing.pix_sales == Decimal("150.00")
        assert closing.card_sales == Decimal("250.00")

    def test_closing_unique_date(self):
        """Testa que data do fechamento é única."""
        date = timezone.now().date()
        DailyClosingFactory(date=date)
        with pytest.raises(Exception):  # IntegrityError
            DailyClosingFactory(date=date)

    def test_closing_total_sales(self):
        """Testa cálculo de total de vendas."""
        closing = DailyClosingFactory(
            cash_sales=Decimal("100.00"), pix_sales=Decimal("200.00"), card_sales=Decimal("300.00")
        )
        assert closing.total_sales == Decimal("600.00")

    def test_closing_average_ticket(self):
        """Testa cálculo de ticket médio."""
        closing = DailyClosingFactory(
            order_count=10,
            cash_sales=Decimal("100.00"),
            pix_sales=Decimal("150.00"),
            card_sales=Decimal("250.00"),
        )
        # Total: 500, Pedidos: 10, Ticket: 50
        assert closing.average_ticket == Decimal("50.00")

    def test_closing_average_ticket_zero_orders(self):
        """Testa ticket médio quando não há pedidos."""
        closing = DailyClosingFactory(order_count=0)
        assert closing.average_ticket == Decimal("0.00")

    def test_closing_ordering(self):
        """Testa ordenação padrão por data decrescente."""
        today = timezone.now().date()
        closing1 = DailyClosingFactory(date=today)
        DailyClosingFactory(date=today - timedelta(days=1))

        closings = DailyClosing.objects.all()
        assert closings[0] == closing1  # Mais recente primeiro

    def test_closing_str_method(self):
        """Testa método __str__."""
        date = timezone.now().date()
        closing = DailyClosingFactory(date=date)
        expected = f"Fechamento {date.strftime('%d/%m/%Y')}"
        assert str(closing) == expected


# ============================================================================
# TESTS - Expense
# ============================================================================


@pytest.mark.django_db
class TestExpense:
    """Testes para o modelo Expense."""

    def test_create_expense(self, expense_category):
        """Testa criação de despesa."""
        expense = ExpenseFactory(
            category=expense_category, amount=Decimal("50.00"), description="Teste de despesa"
        )
        assert expense.category == expense_category
        assert expense.amount == Decimal("50.00")
        assert expense.description == "Teste de despesa"

    def test_expense_with_empty_description(self, expense_category):
        """Testa despesa com descrição vazia."""
        expense = ExpenseFactory(category=expense_category, description="")
        assert expense.description == ""

    def test_expense_ordering(self, expense_category):
        """Testa ordenação padrão por data decrescente."""
        today = timezone.now().date()
        expense1 = ExpenseFactory(date=today, category=expense_category)
        ExpenseFactory(date=today - timedelta(days=1), category=expense_category)

        expenses = Expense.objects.all()
        assert expenses[0] == expense1  # Mais recente primeiro

    def test_expense_str_method(self, expense_category):
        """Testa método __str__."""
        date = timezone.now().date()
        expense = ExpenseFactory(date=date, category=expense_category, amount=Decimal("75.50"))
        expected = f"{expense_category.name} - R$ 75.50 ({date.strftime('%d/%m/%Y')})"
        assert str(expense) == expected

    def test_expense_category_protect(self, expense_category):
        """Testa que não é possível deletar categoria com despesas."""
        ExpenseFactory(category=expense_category)
        with pytest.raises(Exception):  # ProtectedError
            expense_category.delete()


# ============================================================================
# TESTS - Model Validations
# ============================================================================


@pytest.mark.django_db
class TestModelValidations:
    """Testes para validações dos models."""

    def test_closing_positive_order_count(self):
        """Testa que order_count deve ser positivo."""
        # PositiveIntegerField já valida isso no banco
        closing = DailyClosingFactory(order_count=0)
        assert closing.order_count == 0  # Zero é permitido

    def test_closing_decimal_valid(self):
        """Testa campos decimais válidos."""
        closing = DailyClosingFactory(
            cash_sales=Decimal("123.45")  # 2 casas decimais
        )
        assert closing.cash_sales == Decimal("123.45")

    def test_expense_decimal_valid(self, expense_category):
        """Testa precisão do campo amount."""
        expense = ExpenseFactory(
            category=expense_category,
            amount=Decimal("99.99"),  # 2 casas decimais
        )
        assert expense.amount == Decimal("99.99")
