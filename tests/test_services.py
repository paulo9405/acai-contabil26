"""
Testes para os services da aplicação finance.
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from finance import services
from tests.conftest import DailyClosingFactory, ExpenseCategoryFactory

# ============================================================================
# TESTS - Calculation Functions
# ============================================================================


@pytest.mark.django_db
class TestCalculationServices:
    """Testes para funções de cálculo."""

    def test_calculate_total_sales(self):
        """Testa cálculo de total de vendas."""
        closing = DailyClosingFactory(
            cash_sales=Decimal("100.00"), pix_sales=Decimal("200.00"), card_sales=Decimal("300.00")
        )
        total = services.calculate_total_sales(closing=closing)
        assert total == Decimal("600.00")

    def test_calculate_average_ticket(self):
        """Testa cálculo de ticket médio."""
        closing = DailyClosingFactory(
            order_count=10,
            cash_sales=Decimal("200.00"),
            pix_sales=Decimal("300.00"),
            card_sales=Decimal("500.00"),
        )
        avg = services.calculate_average_ticket(closing=closing)
        assert avg == Decimal("100.00")

    def test_calculate_average_ticket_zero_orders(self):
        """Testa ticket médio com zero pedidos."""
        closing = DailyClosingFactory(order_count=0)
        avg = services.calculate_average_ticket(closing=closing)
        assert avg == Decimal("0.00")

    def test_calculate_period_sales(self, multiple_closings):
        """Testa cálculo de vendas por período."""
        start_date = multiple_closings[-1].date
        end_date = multiple_closings[0].date

        total = services.calculate_period_sales(start_date=start_date, end_date=end_date)
        # Soma de todos os fechamentos
        expected = sum(c.total_sales for c in multiple_closings)
        assert total == expected

    def test_calculate_period_expenses(self, multiple_expenses):
        """Testa cálculo de despesas por período."""
        start_date = multiple_expenses[-1].date
        end_date = multiple_expenses[0].date

        total = services.calculate_period_expenses(start_date=start_date, end_date=end_date)
        expected = sum(e.amount for e in multiple_expenses)
        assert total == expected

    def test_calculate_period_profit(self, multiple_closings, multiple_expenses):
        """Testa cálculo de lucro por período."""
        start_date = multiple_closings[-1].date
        end_date = multiple_closings[0].date

        profit = services.calculate_period_profit(start_date=start_date, end_date=end_date)
        sales = sum(c.total_sales for c in multiple_closings)
        expenses = sum(e.amount for e in multiple_expenses)
        expected = sales - expenses
        assert profit == expected

    def test_calculate_period_orders(self, multiple_closings):
        """Testa cálculo de pedidos por período."""
        start_date = multiple_closings[-1].date
        end_date = multiple_closings[0].date

        total = services.calculate_period_orders(start_date=start_date, end_date=end_date)
        expected = sum(c.order_count for c in multiple_closings)
        assert total == expected

    def test_calculate_period_average_ticket(self, multiple_closings):
        """Testa cálculo de ticket médio por período."""
        start_date = multiple_closings[-1].date
        end_date = multiple_closings[0].date

        avg = services.calculate_period_average_ticket(start_date=start_date, end_date=end_date)
        total_sales = sum(c.total_sales for c in multiple_closings)
        total_orders = sum(c.order_count for c in multiple_closings)
        expected = total_sales / total_orders if total_orders > 0 else Decimal("0.00")
        assert avg == expected


# ============================================================================
# TESTS - Metrics Functions
# ============================================================================


@pytest.mark.django_db
class TestMetricsServices:
    """Testes para funções de métricas."""

    def test_get_daily_metrics_with_closing(self, daily_closing, expense):
        """Testa métricas diárias com fechamento existente."""
        # Garantir que expense é do mesmo dia
        expense.date = daily_closing.date
        expense.save()

        metrics = services.get_daily_metrics(target_date=daily_closing.date)

        assert metrics["date"] == daily_closing.date
        assert metrics["orders"] == daily_closing.order_count
        assert metrics["sales"] == daily_closing.total_sales
        assert metrics["expenses"] == expense.amount
        assert metrics["profit"] == daily_closing.total_sales - expense.amount
        assert metrics["average_ticket"] == daily_closing.average_ticket

    def test_get_daily_metrics_without_closing(self):
        """Testa métricas diárias sem fechamento."""
        date = timezone.now().date()
        metrics = services.get_daily_metrics(target_date=date)

        assert metrics["date"] == date
        assert metrics["orders"] == 0
        assert metrics["sales"] == Decimal("0.00")
        assert metrics["average_ticket"] == Decimal("0.00")

    def test_get_monthly_metrics(self, multiple_closings, multiple_expenses):
        """Testa métricas mensais."""
        # Usar mês e ano atual
        today = timezone.now().date()

        metrics = services.get_monthly_metrics(year=today.year, month=today.month)

        assert "orders" in metrics
        assert "sales" in metrics
        assert "expenses" in metrics
        assert "profit" in metrics
        assert "average_ticket" in metrics
        assert "days_with_closing" in metrics


# ============================================================================
# TESTS - CRUD Functions
# ============================================================================


@pytest.mark.django_db
class TestCRUDServices:
    """Testes para funções CRUD."""

    def test_create_daily_closing(self):
        """Testa criação de fechamento diário."""
        date = timezone.now().date()
        closing = services.create_daily_closing(
            date=date,
            order_count=20,
            cash_sales=Decimal("100.00"),
            pix_sales=Decimal("200.00"),
            card_sales=Decimal("300.00"),
            notes="Teste",
        )

        assert closing.date == date
        assert closing.order_count == 20
        assert closing.cash_sales == Decimal("100.00")
        assert closing.notes == "Teste"

    def test_create_daily_closing_duplicate(self):
        """Testa que não é possível criar fechamento duplicado."""
        date = timezone.now().date()
        services.create_daily_closing(
            date=date,
            order_count=10,
            cash_sales=Decimal("100.00"),
            pix_sales=Decimal("100.00"),
            card_sales=Decimal("100.00"),
        )

        with pytest.raises(ValidationError):
            services.create_daily_closing(
                date=date,
                order_count=20,
                cash_sales=Decimal("200.00"),
                pix_sales=Decimal("200.00"),
                card_sales=Decimal("200.00"),
            )

    def test_create_daily_closing_future_date(self):
        """Testa que não é possível criar fechamento com data futura."""
        future_date = timezone.now().date() + timedelta(days=1)

        with pytest.raises(ValidationError):
            services.create_daily_closing(
                date=future_date,
                order_count=10,
                cash_sales=Decimal("100.00"),
                pix_sales=Decimal("100.00"),
                card_sales=Decimal("100.00"),
            )

    def test_update_daily_closing(self, daily_closing):
        """Testa atualização de fechamento."""
        updated = services.update_daily_closing(
            closing=daily_closing,
            order_count=30,
            cash_sales=Decimal("150.00"),
            pix_sales=Decimal("250.00"),
            card_sales=Decimal("350.00"),
            notes="Atualizado",
        )

        assert updated.order_count == 30
        assert updated.cash_sales == Decimal("150.00")
        assert updated.notes == "Atualizado"

    def test_create_expense(self, expense_category):
        """Testa criação de despesa."""
        date = timezone.now().date()
        expense = services.create_expense(
            date=date,
            category=expense_category,
            amount=Decimal("75.50"),
            description="Teste de despesa",
        )

        assert expense.date == date
        assert expense.category == expense_category
        assert expense.amount == Decimal("75.50")
        assert expense.description == "Teste de despesa"

    def test_create_expense_valid_date(self, expense_category):
        """Testa criação de despesa com data válida."""
        today = timezone.now().date()

        expense = services.create_expense(
            date=today, category=expense_category, amount=Decimal("50.00")
        )
        assert expense.date == today

    def test_create_expense_negative_amount(self, expense_category):
        """Testa que não é possível criar despesa com valor negativo."""
        with pytest.raises(ValidationError):
            services.create_expense(
                date=timezone.now().date(), category=expense_category, amount=Decimal("-50.00")
            )

    def test_update_expense(self, expense, expense_category):
        """Testa atualização de despesa."""
        new_category = ExpenseCategoryFactory()
        updated = services.update_expense(
            expense=expense,
            date=expense.date,
            category=new_category,
            amount=Decimal("100.00"),
            description="Atualizado",
        )

        assert updated.category == new_category
        assert updated.amount == Decimal("100.00")
        assert updated.description == "Atualizado"

    def test_create_expense_category(self):
        """Testa criação de categoria de despesa."""
        category = services.create_expense_category(name="Nova Categoria")

        assert category.name == "Nova Categoria"
        assert category.active is True


# ============================================================================
# TESTS - Dashboard Metrics
# ============================================================================


@pytest.mark.django_db
class TestDashboardMetrics:
    """Testes para métricas do dashboard."""

    def test_get_dashboard_metrics(self, multiple_closings, multiple_expenses):
        """Testa obtenção de métricas do dashboard."""
        metrics = services.get_dashboard_metrics()

        assert "today" in metrics
        assert "month" in metrics
        assert "orders" in metrics["today"]
        assert "sales" in metrics["today"]
        assert "expenses" in metrics["today"]
        assert "profit" in metrics["today"]
        assert "average_ticket" in metrics["today"]
