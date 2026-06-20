"""
Views da aplicação finance.
"""

from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.db import models
from django.utils import timezone
from datetime import timedelta

from finance.models import Expense, ExpenseCategory, DailyClosing
from finance.forms import ExpenseForm, ExpenseFilterForm, DailyClosingForm
from finance.services import (
    create_expense, update_expense, create_daily_closing, update_daily_closing,
    get_dashboard_metrics, calculate_period_sales, calculate_period_expenses,
    calculate_period_profit
)


# ============================================================================
# DASHBOARD VIEW
# ============================================================================

class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Dashboard principal do sistema.
    Exibe métricas do dia, do mês e últimos 7 dias.
    """
    template_name = 'finance/dashboard.html'

    def get_context_data(self, **kwargs):
        """
        Adiciona métricas ao contexto.
        """
        context = super().get_context_data(**kwargs)

        # Métricas do dia e do mês (via service)
        dashboard_data = get_dashboard_metrics()
        context['today'] = dashboard_data['today']
        context['month'] = dashboard_data['month']

        # Últimos 7 dias para visualização
        today = timezone.now().date()
        start_date = today - timedelta(days=6)  # 7 dias incluindo hoje

        # Buscar fechamentos dos últimos 7 dias
        closings = DailyClosing.objects.filter(
            date__gte=start_date,
            date__lte=today
        ).order_by('date')

        # Preparar dados para os últimos 7 dias
        last_7_days = []
        for i in range(7):
            day = start_date + timedelta(days=i)

            # Buscar fechamento do dia
            try:
                closing = closings.get(date=day)
                sales = closing.total_sales
            except DailyClosing.DoesNotExist:
                sales = 0

            # Buscar despesas do dia
            expenses = Expense.objects.filter(date=day).aggregate(
                total=models.Sum('amount')
            )['total'] or 0

            profit = sales - expenses

            last_7_days.append({
                'date': day,
                'date_str': day.strftime('%d/%m'),
                'sales': sales,
                'expenses': expenses,
                'profit': profit,
            })

        context['last_7_days'] = last_7_days

        # Totais dos últimos 7 dias
        context['last_7_days_sales'] = calculate_period_sales(
            start_date=start_date,
            end_date=today
        )
        context['last_7_days_expenses'] = calculate_period_expenses(
            start_date=start_date,
            end_date=today
        )
        context['last_7_days_profit'] = calculate_period_profit(
            start_date=start_date,
            end_date=today
        )

        return context


# ============================================================================
# EXPENSE VIEWS
# ============================================================================

class ExpenseListView(LoginRequiredMixin, ListView):
    """
    Lista todas as despesas com filtros e paginação.
    """
    model = Expense
    template_name = 'finance/expense_list.html'
    context_object_name = 'expenses'
    paginate_by = 20

    def get_queryset(self):
        """
        Retorna queryset com filtros aplicados e otimizações.
        """
        queryset = Expense.objects.select_related('category').all()

        # Aplicar filtros do formulário
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        category = self.request.GET.get('category')

        if date_from:
            queryset = queryset.filter(date__gte=date_from)

        if date_to:
            queryset = queryset.filter(date__lte=date_to)

        if category:
            queryset = queryset.filter(category_id=category)

        return queryset

    def get_context_data(self, **kwargs):
        """
        Adiciona formulário de filtro ao contexto.
        """
        context = super().get_context_data(**kwargs)

        # Formulário de filtro com valores preenchidos
        context['filter_form'] = ExpenseFilterForm(self.request.GET or None)

        # Total de despesas filtradas
        total = sum(expense.amount for expense in context['expenses'])
        context['total_expenses'] = total

        return context


class ExpenseCreateView(LoginRequiredMixin, CreateView):
    """
    Cria uma nova despesa.
    """
    model = Expense
    form_class = ExpenseForm
    template_name = 'finance/expense_form.html'
    success_url = reverse_lazy('expense-list')

    def form_valid(self, form):
        """
        Processa formulário válido e delega criação para service.
        """
        try:
            # Delegar criação para service
            expense = create_expense(
                date=form.cleaned_data['date'],
                category=form.cleaned_data['category'],
                amount=form.cleaned_data['amount'],
                description=form.cleaned_data.get('description', '')
            )

            messages.success(
                self.request,
                f'Despesa de R$ {expense.amount} registrada com sucesso!'
            )
            return redirect(self.success_url)

        except Exception as e:
            messages.error(self.request, f'Erro ao criar despesa: {e}')
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        """
        Adiciona informações extras ao contexto.
        """
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nova Despesa'
        context['button_text'] = 'Salvar Despesa'
        return context


class ExpenseUpdateView(LoginRequiredMixin, UpdateView):
    """
    Edita uma despesa existente.
    """
    model = Expense
    form_class = ExpenseForm
    template_name = 'finance/expense_form.html'
    success_url = reverse_lazy('expense-list')

    def form_valid(self, form):
        """
        Processa formulário válido e delega atualização para service.
        """
        try:
            # Delegar atualização para service
            expense = update_expense(
                expense=self.object,
                date=form.cleaned_data['date'],
                category=form.cleaned_data['category'],
                amount=form.cleaned_data['amount'],
                description=form.cleaned_data.get('description', '')
            )

            messages.success(
                self.request,
                f'Despesa de R$ {expense.amount} atualizada com sucesso!'
            )
            return redirect(self.success_url)

        except Exception as e:
            messages.error(self.request, f'Erro ao atualizar despesa: {e}')
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        """
        Adiciona informações extras ao contexto.
        """
        context = super().get_context_data(**kwargs)
        context['title'] = 'Editar Despesa'
        context['button_text'] = 'Atualizar Despesa'
        return context


class ExpenseDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Exclui uma despesa.
    Apenas superusuários podem excluir.
    """
    model = Expense
    template_name = 'finance/expense_confirm_delete.html'
    success_url = reverse_lazy('expense-list')

    def test_func(self):
        """
        Testa se o usuário tem permissão para excluir.
        """
        return self.request.user.is_superuser

    def delete(self, request, *args, **kwargs):
        """
        Processa exclusão e exibe mensagem.
        """
        expense = self.get_object()
        amount = expense.amount

        messages.success(
            request,
            f'Despesa de R$ {amount} excluída com sucesso!'
        )

        return super().delete(request, *args, **kwargs)


# ============================================================================
# DAILY CLOSING VIEWS
# ============================================================================

class DailyClosingListView(LoginRequiredMixin, ListView):
    """
    Lista todos os fechamentos diários com paginação.
    """
    model = DailyClosing
    template_name = 'finance/daily_closing_list.html'
    context_object_name = 'closings'
    paginate_by = 20

    def get_queryset(self):
        """
        Retorna queryset ordenado por data (mais recente primeiro).
        """
        return DailyClosing.objects.all()


class DailyClosingCreateView(LoginRequiredMixin, CreateView):
    """
    Cria um novo fechamento diário.
    """
    model = DailyClosing
    form_class = DailyClosingForm
    template_name = 'finance/daily_closing_form.html'
    success_url = reverse_lazy('closing-list')

    def form_valid(self, form):
        """
        Processa formulário válido e delega criação para service.
        """
        try:
            # Delegar criação para service
            closing = create_daily_closing(
                date=form.cleaned_data['date'],
                order_count=form.cleaned_data['order_count'],
                cash_sales=form.cleaned_data['cash_sales'],
                pix_sales=form.cleaned_data['pix_sales'],
                card_sales=form.cleaned_data['card_sales'],
                notes=form.cleaned_data.get('notes', '')
            )

            messages.success(
                self.request,
                f'Fechamento de {closing.date.strftime("%d/%m/%Y")} registrado com sucesso!'
            )
            return redirect(self.success_url)

        except Exception as e:
            messages.error(self.request, f'Erro ao criar fechamento: {e}')
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        """
        Adiciona informações extras ao contexto.
        """
        context = super().get_context_data(**kwargs)
        context['title'] = 'Novo Fechamento Diário'
        context['button_text'] = 'Salvar Fechamento'
        return context


class DailyClosingUpdateView(LoginRequiredMixin, UpdateView):
    """
    Edita um fechamento diário existente.
    """
    model = DailyClosing
    form_class = DailyClosingForm
    template_name = 'finance/daily_closing_form.html'
    success_url = reverse_lazy('closing-list')

    def form_valid(self, form):
        """
        Processa formulário válido e delega atualização para service.
        """
        try:
            # Delegar atualização para service
            closing = update_daily_closing(
                closing=self.object,
                order_count=form.cleaned_data['order_count'],
                cash_sales=form.cleaned_data['cash_sales'],
                pix_sales=form.cleaned_data['pix_sales'],
                card_sales=form.cleaned_data['card_sales'],
                notes=form.cleaned_data.get('notes', '')
            )

            messages.success(
                self.request,
                f'Fechamento de {closing.date.strftime("%d/%m/%Y")} atualizado com sucesso!'
            )
            return redirect(self.success_url)

        except Exception as e:
            messages.error(self.request, f'Erro ao atualizar fechamento: {e}')
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        """
        Adiciona informações extras ao contexto.
        """
        context = super().get_context_data(**kwargs)
        context['title'] = 'Editar Fechamento Diário'
        context['button_text'] = 'Atualizar Fechamento'
        return context


class DailyClosingDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Exclui um fechamento diário.
    Apenas superusuários podem excluir.
    """
    model = DailyClosing
    template_name = 'finance/daily_closing_confirm_delete.html'
    success_url = reverse_lazy('closing-list')

    def test_func(self):
        """
        Testa se o usuário tem permissão para excluir.
        """
        return self.request.user.is_superuser

    def delete(self, request, *args, **kwargs):
        """
        Processa exclusão e exibe mensagem.
        """
        closing = self.get_object()
        date = closing.date

        messages.success(
            request,
            f'Fechamento de {date.strftime("%d/%m/%Y")} excluído com sucesso!'
        )

        return super().delete(request, *args, **kwargs)
