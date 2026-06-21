"""
Testes para os formulários da aplicação finance.
"""

import pytest
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

from finance.forms import (
    ExpenseForm,
    ExpenseFilterForm,
    DailyClosingForm,
    ReportFilterForm
)
from finance.models import ExpenseCategory, DailyClosing
from tests.conftest import ExpenseCategoryFactory, DailyClosingFactory


# ============================================================================
# TESTS - ExpenseForm
# ============================================================================

@pytest.mark.django_db
class TestExpenseForm:
    """Testes para ExpenseForm."""

    def test_form_valid_data(self, expense_category):
        """Testa formulário com dados válidos."""
        form = ExpenseForm(data={
            'date': timezone.now().date(),
            'category': expense_category.id,
            'amount': '50.00',
            'description': 'Teste'
        })
        assert form.is_valid()

    def test_form_invalid_future_date(self, expense_category):
        """Testa que data futura é inválida."""
        future_date = timezone.now().date() + timedelta(days=1)
        form = ExpenseForm(data={
            'date': future_date,
            'category': expense_category.id,
            'amount': '50.00'
        })
        assert not form.is_valid()
        assert 'date' in form.errors

    def test_form_invalid_negative_amount(self, expense_category):
        """Testa que valor negativo é inválido."""
        form = ExpenseForm(data={
            'date': timezone.now().date(),
            'category': expense_category.id,
            'amount': '-50.00'
        })
        assert not form.is_valid()
        assert 'amount' in form.errors

    def test_form_invalid_zero_amount(self, expense_category):
        """Testa que valor zero é inválido."""
        form = ExpenseForm(data={
            'date': timezone.now().date(),
            'category': expense_category.id,
            'amount': '0.00'
        })
        assert not form.is_valid()
        assert 'amount' in form.errors

    def test_form_only_active_categories(self):
        """Testa que apenas categorias ativas aparecem no formulário."""
        active = ExpenseCategoryFactory(active=True)
        inactive = ExpenseCategoryFactory(active=False)

        form = ExpenseForm()
        category_ids = [c.id for c in form.fields['category'].queryset]

        assert active.id in category_ids
        assert inactive.id not in category_ids

    def test_form_optional_description(self, expense_category):
        """Testa que descrição é opcional."""
        form = ExpenseForm(data={
            'date': timezone.now().date(),
            'category': expense_category.id,
            'amount': '50.00',
            'description': ''  # Vazio
        })
        assert form.is_valid()


# ============================================================================
# TESTS - ExpenseFilterForm
# ============================================================================

@pytest.mark.django_db
class TestExpenseFilterForm:
    """Testes para ExpenseFilterForm."""

    def test_form_all_fields_optional(self):
        """Testa que todos os campos são opcionais."""
        form = ExpenseFilterForm(data={})
        assert form.is_valid()

    def test_form_valid_date_range(self):
        """Testa range de datas válido."""
        today = timezone.now().date()
        form = ExpenseFilterForm(data={
            'date_from': today - timedelta(days=7),
            'date_to': today
        })
        assert form.is_valid()

    def test_form_invalid_date_range(self):
        """Testa que data_from > date_to é inválido."""
        today = timezone.now().date()
        form = ExpenseFilterForm(data={
            'date_from': today,
            'date_to': today - timedelta(days=7)
        })
        assert not form.is_valid()
        assert form.non_field_errors()

    def test_form_with_category(self, expense_category):
        """Testa filtro por categoria."""
        form = ExpenseFilterForm(data={
            'category': expense_category.id
        })
        assert form.is_valid()


# ============================================================================
# TESTS - DailyClosingForm
# ============================================================================

@pytest.mark.django_db
class TestDailyClosingForm:
    """Testes para DailyClosingForm."""

    def test_form_valid_data(self):
        """Testa formulário com dados válidos."""
        form = DailyClosingForm(data={
            'date': timezone.now().date(),
            'order_count': 20,
            'cash_sales': '100.00',
            'pix_sales': '200.00',
            'card_sales': '300.00',
            'notes': 'Teste'
        })
        assert form.is_valid()

    def test_form_invalid_future_date(self):
        """Testa que data futura é inválida."""
        future_date = timezone.now().date() + timedelta(days=1)
        form = DailyClosingForm(data={
            'date': future_date,
            'order_count': 20,
            'cash_sales': '100.00',
            'pix_sales': '200.00',
            'card_sales': '300.00'
        })
        assert not form.is_valid()
        assert 'date' in form.errors

    def test_form_duplicate_date_create(self, daily_closing):
        """Testa que não é possível criar fechamento duplicado."""
        form = DailyClosingForm(data={
            'date': daily_closing.date,
            'order_count': 20,
            'cash_sales': '100.00',
            'pix_sales': '200.00',
            'card_sales': '300.00'
        })
        assert not form.is_valid()
        assert 'date' in form.errors

    def test_form_duplicate_date_update(self, daily_closing):
        """Testa que é possível atualizar fechamento existente."""
        # Ao passar instance, não deve dar erro de duplicação
        form = DailyClosingForm(
            instance=daily_closing,
            data={
                'date': daily_closing.date,
                'order_count': 30,
                'cash_sales': '150.00',
                'pix_sales': '250.00',
                'card_sales': '350.00'
            }
        )
        assert form.is_valid()

    def test_form_optional_notes(self):
        """Testa que observações são opcionais."""
        form = DailyClosingForm(data={
            'date': timezone.now().date(),
            'order_count': 20,
            'cash_sales': '100.00',
            'pix_sales': '200.00',
            'card_sales': '300.00',
            'notes': ''  # Vazio
        })
        assert form.is_valid()


# ============================================================================
# TESTS - ReportFilterForm
# ============================================================================

@pytest.mark.django_db
class TestReportFilterForm:
    """Testes para ReportFilterForm."""

    def test_form_valid_predefined_period(self):
        """Testa período pré-definido."""
        form = ReportFilterForm(data={
            'period': 'this_month'
        })
        assert form.is_valid()

    def test_form_valid_custom_period(self):
        """Testa período customizado com datas."""
        today = timezone.now().date()
        form = ReportFilterForm(data={
            'period': 'custom',
            'start_date': today - timedelta(days=7),
            'end_date': today
        })
        assert form.is_valid()

    def test_form_invalid_custom_without_start_date(self):
        """Testa custom sem data inicial."""
        form = ReportFilterForm(data={
            'period': 'custom',
            'end_date': timezone.now().date()
        })
        assert not form.is_valid()
        assert 'start_date' in form.errors

    def test_form_invalid_custom_without_end_date(self):
        """Testa custom sem data final."""
        form = ReportFilterForm(data={
            'period': 'custom',
            'start_date': timezone.now().date()
        })
        assert not form.is_valid()
        assert 'end_date' in form.errors

    def test_form_invalid_custom_date_range(self):
        """Testa custom com range inválido."""
        today = timezone.now().date()
        form = ReportFilterForm(data={
            'period': 'custom',
            'start_date': today,
            'end_date': today - timedelta(days=7)
        })
        assert not form.is_valid()

    def test_form_default_period(self):
        """Testa período padrão."""
        form = ReportFilterForm()
        assert form.fields['period'].initial == 'this_month'

    def test_form_all_period_choices(self):
        """Testa todas as opções de período."""
        periods = ['today', 'yesterday', 'last_7_days', 'last_30_days',
                   'this_month', 'last_month', 'custom']

        for period in periods:
            if period == 'custom':
                data = {
                    'period': period,
                    'start_date': timezone.now().date() - timedelta(days=7),
                    'end_date': timezone.now().date()
                }
            else:
                data = {'period': period}

            form = ReportFilterForm(data=data)
            assert form.is_valid(), f"Period {period} should be valid"
