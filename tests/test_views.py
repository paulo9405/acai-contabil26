"""
Testes para as views da aplicação finance.
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from finance.models import DailyClosing, Expense

# ============================================================================
# TESTS - Dashboard View
# ============================================================================


@pytest.mark.django_db
class TestDashboardView:
    """Testes para DashboardView."""

    def test_dashboard_requires_login(self, api_client):
        """Testa que dashboard requer autenticação."""
        url = reverse("dashboard")
        response = api_client.get(url)
        assert response.status_code == 302  # Redirect to login

    def test_dashboard_authenticated(self, superuser_client):
        """Testa acesso ao dashboard autenticado."""
        url = reverse("dashboard")
        response = superuser_client.get(url)
        assert response.status_code == 200
        assert "today" in response.context
        assert "month" in response.context

    def test_dashboard_with_data(self, superuser_client, multiple_closings, multiple_expenses):
        """Testa dashboard com dados."""
        url = reverse("dashboard")
        response = superuser_client.get(url)

        assert response.status_code == 200
        assert "last_7_days" in response.context
        assert len(response.context["last_7_days"]) == 7


# ============================================================================
# TESTS - DailyClosing Views
# ============================================================================


@pytest.mark.django_db
class TestDailyClosingViews:
    """Testes para views de fechamento diário."""

    def test_closing_list_requires_login(self, api_client):
        """Testa que lista requer autenticação."""
        url = reverse("closing-list")
        response = api_client.get(url)
        assert response.status_code == 302

    def test_closing_list_authenticated(self, superuser_client):
        """Testa acesso à lista autenticado."""
        url = reverse("closing-list")
        response = superuser_client.get(url)
        assert response.status_code == 200

    def test_closing_list_with_data(self, superuser_client, multiple_closings):
        """Testa lista com fechamentos."""
        url = reverse("closing-list")
        response = superuser_client.get(url)

        assert response.status_code == 200
        assert "closings" in response.context
        assert len(response.context["closings"]) == len(multiple_closings)

    def test_closing_create_get(self, superuser_client):
        """Testa GET do formulário de criação."""
        url = reverse("closing-create")
        response = superuser_client.get(url)

        assert response.status_code == 200
        assert "form" in response.context

    def test_closing_create_post_valid(self, superuser_client):
        """Testa POST com dados válidos."""
        url = reverse("closing-create")
        data = {
            "date": timezone.now().date(),
            "order_count": 20,
            "cash_sales": "100.00",
            "pix_sales": "200.00",
            "card_sales": "300.00",
            "notes": "Teste",
        }
        response = superuser_client.post(url, data)

        assert response.status_code == 302  # Redirect
        assert DailyClosing.objects.filter(date=data["date"]).exists()

    def test_closing_create_post_invalid(self, superuser_client):
        """Testa POST com dados inválidos."""
        url = reverse("closing-create")
        data = {
            "date": timezone.now().date() + timedelta(days=1),  # Futura
            "order_count": 20,
            "cash_sales": "100.00",
            "pix_sales": "200.00",
            "card_sales": "300.00",
        }
        response = superuser_client.post(url, data)

        assert response.status_code == 200  # Permanece na página
        assert "form" in response.context
        assert response.context["form"].errors

    def test_closing_update_get(self, superuser_client, daily_closing):
        """Testa GET do formulário de edição."""
        url = reverse("closing-edit", kwargs={"pk": daily_closing.pk})
        response = superuser_client.get(url)

        assert response.status_code == 200
        assert "form" in response.context

    def test_closing_update_post(self, superuser_client, daily_closing):
        """Testa POST de atualização."""
        url = reverse("closing-edit", kwargs={"pk": daily_closing.pk})
        data = {
            "date": daily_closing.date,
            "order_count": 30,  # Alterado
            "cash_sales": "150.00",
            "pix_sales": "250.00",
            "card_sales": "350.00",
            "notes": "Atualizado",
        }
        response = superuser_client.post(url, data)

        assert response.status_code == 302
        daily_closing.refresh_from_db()
        assert daily_closing.order_count == 30

    def test_closing_delete_requires_superuser(self, authenticated_client, daily_closing):
        """Testa que exclusão requer superuser."""
        url = reverse("closing-delete", kwargs={"pk": daily_closing.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 403  # Forbidden

    def test_closing_delete_superuser(self, superuser_client, daily_closing):
        """Testa exclusão por superuser."""
        url = reverse("closing-delete", kwargs={"pk": daily_closing.pk})
        response = superuser_client.get(url)
        assert response.status_code == 200

        response = superuser_client.post(url)
        assert response.status_code == 302
        assert not DailyClosing.objects.filter(pk=daily_closing.pk).exists()


# ============================================================================
# TESTS - Expense Views
# ============================================================================


@pytest.mark.django_db
class TestExpenseViews:
    """Testes para views de despesas."""

    def test_expense_list_requires_login(self, api_client):
        """Testa que lista requer autenticação."""
        url = reverse("expense-list")
        response = api_client.get(url)
        assert response.status_code == 302

    def test_expense_list_authenticated(self, superuser_client):
        """Testa acesso à lista autenticado."""
        url = reverse("expense-list")
        response = superuser_client.get(url)
        assert response.status_code == 200

    def test_expense_list_with_filters(self, superuser_client, expense):
        """Testa lista com filtros."""
        url = reverse("expense-list")
        response = superuser_client.get(url, {"date_from": expense.date, "date_to": expense.date})

        assert response.status_code == 200
        assert "expenses" in response.context

    def test_expense_create_get(self, superuser_client):
        """Testa GET do formulário de criação."""
        url = reverse("expense-create")
        response = superuser_client.get(url)

        assert response.status_code == 200
        assert "form" in response.context

    def test_expense_create_post_valid(self, superuser_client, expense_category):
        """Testa POST com dados válidos."""
        url = reverse("expense-create")
        data = {
            "date": timezone.now().date(),
            "category": expense_category.id,
            "amount": "75.50",
            "description": "Teste",
        }
        response = superuser_client.post(url, data)

        assert response.status_code == 302
        assert Expense.objects.filter(amount=Decimal("75.50")).exists()

    def test_expense_update_get(self, superuser_client, expense):
        """Testa GET do formulário de edição."""
        url = reverse("expense-edit", kwargs={"pk": expense.pk})
        response = superuser_client.get(url)

        assert response.status_code == 200
        assert "form" in response.context

    def test_expense_update_post(self, superuser_client, expense):
        """Testa POST de atualização."""
        url = reverse("expense-edit", kwargs={"pk": expense.pk})
        data = {
            "date": expense.date,
            "category": expense.category.id,
            "amount": "100.00",  # Alterado
            "description": "Atualizado",
        }
        response = superuser_client.post(url, data)

        assert response.status_code == 302
        expense.refresh_from_db()
        assert expense.amount == Decimal("100.00")

    def test_expense_delete_requires_superuser(self, authenticated_client, expense):
        """Testa que exclusão requer superuser."""
        url = reverse("expense-delete", kwargs={"pk": expense.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 403

    def test_expense_delete_superuser(self, superuser_client, expense):
        """Testa exclusão por superuser."""
        url = reverse("expense-delete", kwargs={"pk": expense.pk})
        response = superuser_client.get(url)
        assert response.status_code == 200

        response = superuser_client.post(url)
        assert response.status_code == 302
        assert not Expense.objects.filter(pk=expense.pk).exists()


# ============================================================================
# TESTS - Report View
# ============================================================================


@pytest.mark.django_db
class TestReportView:
    """Testes para ReportView."""

    def test_report_requires_login(self, api_client):
        """Testa que relatório requer autenticação."""
        url = reverse("reports")
        response = api_client.get(url)
        assert response.status_code == 302

    def test_report_authenticated(self, superuser_client):
        """Testa acesso ao relatório autenticado."""
        url = reverse("reports")
        response = superuser_client.get(url, {"period": "this_month"})
        assert response.status_code == 200

    def test_report_with_period(self, superuser_client, multiple_closings):
        """Testa relatório com período."""
        url = reverse("reports")
        response = superuser_client.get(url, {"period": "last_7_days"})

        assert response.status_code == 200
        assert "total_sales" in response.context
        assert "total_expenses" in response.context
        assert "total_profit" in response.context

    def test_report_custom_period(self, superuser_client):
        """Testa relatório com período customizado."""
        today = timezone.now().date()
        url = reverse("reports")
        response = superuser_client.get(
            url, {"period": "custom", "start_date": today - timedelta(days=7), "end_date": today}
        )

        assert response.status_code == 200
        assert "start_date" in response.context
        assert "end_date" in response.context
