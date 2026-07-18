"""
Views da aplicação finance.
"""

from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db import models, transaction
from django.db.models import DecimalField, OuterRef, Subquery
from django.db.models.functions import Coalesce
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    ListView,
    RedirectView,
    TemplateView,
    UpdateView,
)

from finance.forms import DailyClosingForm, ExpenseFilterForm, ExpenseForm, ReportFilterForm
from finance.models import DailyClosing, Expense, ExpenseCategory
from finance.services import (
    calculate_period_average_ticket,
    calculate_period_expenses,
    calculate_period_orders,
    calculate_period_profit,
    calculate_period_sales,
    create_daily_closing,
    create_expense,
    get_dashboard_metrics,
    update_daily_closing,
    update_expense,
)

# ============================================================================
# MIXIN DE SUPERUSUÁRIO
# ============================================================================


class SuperuserRequiredMixin(LoginRequiredMixin):
    """Bloqueia acesso a usuários que não são superusuários."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_superuser:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


# ============================================================================
# DASHBOARD VIEW
# ============================================================================


class DashboardView(SuperuserRequiredMixin, TemplateView):
    """
    Dashboard principal do sistema.
    Exibe métricas do dia, do mês e últimos 7 dias.
    """

    template_name = "finance/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        today = timezone.now().date()

        context["today_has_closing"] = DailyClosing.objects.filter(date=today).exists()
        context["today_date_str"] = today.isoformat()

        # Métricas do dia e do mês (via service)
        dashboard_data = get_dashboard_metrics()
        context["today"] = dashboard_data["today"]
        context["month"] = dashboard_data["month"]

        # Últimos 7 dias para gráfico de tendência
        start_date = today - timedelta(days=6)
        closings_7d = DailyClosing.objects.filter(date__gte=start_date, date__lte=today).order_by(
            "date"
        )

        last_7_days = []
        for i in range(7):
            day = start_date + timedelta(days=i)
            try:
                closing = closings_7d.get(date=day)
                sales = closing.total_sales
            except DailyClosing.DoesNotExist:
                sales = 0

            expenses = (
                Expense.objects.filter(date=day).aggregate(total=models.Sum("amount"))["total"] or 0
            )

            last_7_days.append(
                {
                    "date": day,
                    "date_str": day.strftime("%d/%m"),
                    "url_date": day.isoformat(),
                    "sales": sales,
                    "expenses": expenses,
                    "profit": sales - expenses,
                }
            )

        context["last_7_days"] = last_7_days

        # Despesas por categoria do mês
        first_day_month = today.replace(day=1)
        context["expenses_by_category"] = (
            Expense.objects.filter(date__gte=first_day_month, date__lte=today)
            .values("category__name")
            .annotate(total=models.Sum("amount"))
            .order_by("-total")[:8]
        )

        # Últimos fechamentos com totais de despesas
        expense_subquery = (
            Expense.objects.filter(date=OuterRef("date"))
            .values("date")
            .annotate(total=models.Sum("amount"))
            .values("total")
        )

        recent_qs = DailyClosing.objects.annotate(
            expense_total=Coalesce(
                Subquery(
                    expense_subquery, output_field=DecimalField(max_digits=10, decimal_places=2)
                ),
                Decimal("0.00"),
                output_field=DecimalField(max_digits=10, decimal_places=2),
            )
        ).order_by("-date")[:5]

        context["recent_closings"] = [
            {
                "closing": c,
                "expense_total": c.expense_total,
                "result": c.total_sales - c.expense_total,
                "date_str": c.date.isoformat(),
                "is_today": c.date == today,
            }
            for c in recent_qs
        ]

        return context


# ============================================================================
# REPORT VIEW
# ============================================================================


class ReportView(SuperuserRequiredMixin, TemplateView):
    """
    Relatórios financeiros com filtros por período.
    Exibe resumo de vendas, despesas, lucro e listagem detalhada.
    """

    template_name = "finance/report.html"

    def get_context_data(self, **kwargs):
        """
        Processa filtros e retorna dados do relatório.
        """
        context = super().get_context_data(**kwargs)

        # Processar formulário de filtro
        form = ReportFilterForm(self.request.GET or {"period": "this_month"})
        context["form"] = form

        if form.is_valid():
            # Calcular datas baseado no período
            start_date, end_date = self._calculate_period_dates(
                form.cleaned_data["period"],
                form.cleaned_data.get("start_date"),
                form.cleaned_data.get("end_date"),
            )

            context["start_date"] = start_date
            context["end_date"] = end_date
            context["period_label"] = dict(form.fields["period"].choices)[
                form.cleaned_data["period"]
            ]

            # Calcular métricas usando services
            context["total_sales"] = calculate_period_sales(
                start_date=start_date, end_date=end_date
            )
            context["total_expenses"] = calculate_period_expenses(
                start_date=start_date, end_date=end_date
            )
            context["total_profit"] = calculate_period_profit(
                start_date=start_date, end_date=end_date
            )
            context["total_orders"] = calculate_period_orders(
                start_date=start_date, end_date=end_date
            )
            context["average_ticket"] = calculate_period_average_ticket(
                start_date=start_date, end_date=end_date
            )

            # Buscar fechamentos do período
            closings = DailyClosing.objects.filter(
                date__gte=start_date, date__lte=end_date
            ).order_by("-date")
            context["closings"] = closings

            # Buscar despesas do período
            expenses = (
                Expense.objects.filter(date__gte=start_date, date__lte=end_date)
                .select_related("category")
                .order_by("-date", "-id")
            )
            context["expenses"] = expenses

            # Despesas por categoria
            expenses_by_category = (
                Expense.objects.filter(date__gte=start_date, date__lte=end_date)
                .values("category__name")
                .annotate(total=models.Sum("amount"))
                .order_by("-total")
            )
            context["expenses_by_category"] = expenses_by_category

            # Dados diários para gráficos (limitado a 31 dias para performance)
            days_diff = (end_date - start_date).days + 1
            if days_diff <= 31:
                daily_data = []
                current_date = start_date
                while current_date <= end_date:
                    # Vendas do dia
                    try:
                        closing = DailyClosing.objects.get(date=current_date)
                        sales = closing.total_sales
                    except DailyClosing.DoesNotExist:
                        sales = 0

                    # Despesas do dia
                    expenses_sum = (
                        Expense.objects.filter(date=current_date).aggregate(
                            total=models.Sum("amount")
                        )["total"]
                        or 0
                    )

                    daily_data.append(
                        {
                            "date": current_date,
                            "date_str": current_date.strftime("%d/%m"),
                            "sales": float(sales),
                            "expenses": float(expenses_sum),
                            "profit": float(sales - expenses_sum),
                        }
                    )

                    current_date += timedelta(days=1)

                context["daily_data"] = daily_data

        return context

    def _calculate_period_dates(self, period, custom_start, custom_end):
        """
        Calcula as datas de início e fim baseado no período selecionado.
        """
        today = timezone.now().date()

        if period == "today":
            return today, today

        elif period == "yesterday":
            yesterday = today - timedelta(days=1)
            return yesterday, yesterday

        elif period == "last_7_days":
            start = today - timedelta(days=6)
            return start, today

        elif period == "last_30_days":
            start = today - timedelta(days=29)
            return start, today

        elif period == "this_month":
            start = today.replace(day=1)
            return start, today

        elif period == "last_month":
            # Primeiro dia do mês passado
            first_this_month = today.replace(day=1)
            last_day_last_month = first_this_month - timedelta(days=1)
            first_last_month = last_day_last_month.replace(day=1)
            return first_last_month, last_day_last_month

        elif period == "custom":
            return custom_start, custom_end

        # Default: este mês
        start = today.replace(day=1)
        return start, today


# ============================================================================
# EXPENSE VIEWS
# ============================================================================


class ExpenseListView(SuperuserRequiredMixin, ListView):
    """
    Lista todas as despesas com filtros e paginação.
    """

    model = Expense
    template_name = "finance/expense_list.html"
    context_object_name = "expenses"
    paginate_by = 20

    def get_queryset(self):
        """
        Retorna queryset com filtros aplicados e otimizações.
        """
        queryset = Expense.objects.select_related("category").all()

        # Aplicar filtros do formulário
        date_from = self.request.GET.get("date_from")
        date_to = self.request.GET.get("date_to")
        category = self.request.GET.get("category")

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
        context["filter_form"] = ExpenseFilterForm(self.request.GET or None)

        # Total de despesas filtradas
        total = sum(expense.amount for expense in context["expenses"])
        context["total_expenses"] = total

        return context


class ExpenseCreateView(SuperuserRequiredMixin, CreateView):
    """
    Cria uma nova despesa.
    """

    model = Expense
    form_class = ExpenseForm
    template_name = "finance/expense_form.html"
    success_url = reverse_lazy("expense-list")

    def form_valid(self, form):
        """
        Processa formulário válido e delega criação para service.
        """
        try:
            # Delegar criação para service
            expense = create_expense(
                date=form.cleaned_data["date"],
                category=form.cleaned_data["category"],
                amount=form.cleaned_data["amount"],
                description=form.cleaned_data.get("description", ""),
            )

            messages.success(
                self.request, f"Despesa de R$ {expense.amount} registrada com sucesso!"
            )
            return redirect(self.success_url)

        except Exception as e:
            messages.error(self.request, f"Erro ao criar despesa: {e}")
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        """
        Adiciona informações extras ao contexto.
        """
        context = super().get_context_data(**kwargs)
        context["title"] = "Nova Despesa"
        context["button_text"] = "Salvar Despesa"
        return context


class ExpenseUpdateView(SuperuserRequiredMixin, UpdateView):
    """
    Edita uma despesa existente.
    """

    model = Expense
    form_class = ExpenseForm
    template_name = "finance/expense_form.html"
    success_url = reverse_lazy("expense-list")

    def form_valid(self, form):
        """
        Processa formulário válido e delega atualização para service.
        """
        try:
            # Delegar atualização para service
            expense = update_expense(
                expense=self.object,
                date=form.cleaned_data["date"],
                category=form.cleaned_data["category"],
                amount=form.cleaned_data["amount"],
                description=form.cleaned_data.get("description", ""),
            )

            messages.success(
                self.request, f"Despesa de R$ {expense.amount} atualizada com sucesso!"
            )
            return redirect(self.success_url)

        except Exception as e:
            messages.error(self.request, f"Erro ao atualizar despesa: {e}")
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        """
        Adiciona informações extras ao contexto.
        """
        context = super().get_context_data(**kwargs)
        context["title"] = "Editar Despesa"
        context["button_text"] = "Atualizar Despesa"
        return context


class ExpenseDeleteView(SuperuserRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Exclui uma despesa.
    Apenas superusuários podem excluir.
    """

    model = Expense
    template_name = "finance/expense_confirm_delete.html"

    def get_success_url(self):
        return reverse("daily-closing", kwargs={"closing_date": self.object.date.isoformat()})

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

        messages.success(request, f"Despesa de R$ {amount} excluída com sucesso!")

        return super().delete(request, *args, **kwargs)


# ============================================================================
# DAILY CLOSING VIEWS
# ============================================================================


class DailyClosingListView(SuperuserRequiredMixin, ListView):
    """
    Lista todos os fechamentos diários com paginação.
    """

    model = DailyClosing
    template_name = "finance/daily_closing_list.html"
    context_object_name = "closings"
    paginate_by = 20

    def get_queryset(self):
        expense_subquery = (
            Expense.objects.filter(date=OuterRef("date"))
            .values("date")
            .annotate(total=models.Sum("amount"))
            .values("total")
        )

        return DailyClosing.objects.annotate(
            expense_total=Coalesce(
                Subquery(
                    expense_subquery, output_field=DecimalField(max_digits=10, decimal_places=2)
                ),
                Decimal("0.00"),
                output_field=DecimalField(max_digits=10, decimal_places=2),
            )
        ).order_by("-date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        enriched = []
        for closing in context["closings"]:
            expense_total = closing.expense_total
            enriched.append(
                {
                    "closing": closing,
                    "expense_total": expense_total,
                    "result": closing.total_sales - expense_total,
                    "date_str": closing.date.isoformat(),
                    "is_today": closing.date == today,
                }
            )
        context["enriched_closings"] = enriched
        return context


class DailyClosingCreateView(SuperuserRequiredMixin, CreateView):
    """
    Cria um novo fechamento diário.
    """

    model = DailyClosing
    form_class = DailyClosingForm
    template_name = "finance/daily_closing_form.html"
    success_url = reverse_lazy("closing-list")

    def form_valid(self, form):
        """
        Processa formulário válido e delega criação para service.
        """
        try:
            # Delegar criação para service
            closing = create_daily_closing(
                date=form.cleaned_data["date"],
                order_count=form.cleaned_data["order_count"],
                cash_sales=form.cleaned_data["cash_sales"],
                pix_sales=form.cleaned_data["pix_sales"],
                card_sales=form.cleaned_data["card_sales"],
                notes=form.cleaned_data.get("notes", ""),
            )

            messages.success(
                self.request,
                f"Fechamento de {closing.date.strftime('%d/%m/%Y')} registrado com sucesso!",
            )
            return redirect(self.success_url)

        except Exception as e:
            messages.error(self.request, f"Erro ao criar fechamento: {e}")
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        """
        Adiciona informações extras ao contexto.
        """
        context = super().get_context_data(**kwargs)
        context["title"] = "Novo Fechamento Diário"
        context["button_text"] = "Salvar Fechamento"
        return context


class DailyClosingUpdateView(SuperuserRequiredMixin, UpdateView):
    """
    Edita um fechamento diário existente.
    """

    model = DailyClosing
    form_class = DailyClosingForm
    template_name = "finance/daily_closing_form.html"
    success_url = reverse_lazy("closing-list")

    def form_valid(self, form):
        """
        Processa formulário válido e delega atualização para service.
        """
        try:
            # Delegar atualização para service
            closing = update_daily_closing(
                closing=self.object,
                order_count=form.cleaned_data["order_count"],
                cash_sales=form.cleaned_data["cash_sales"],
                pix_sales=form.cleaned_data["pix_sales"],
                card_sales=form.cleaned_data["card_sales"],
                notes=form.cleaned_data.get("notes", ""),
            )

            messages.success(
                self.request,
                f"Fechamento de {closing.date.strftime('%d/%m/%Y')} atualizado com sucesso!",
            )
            return redirect(self.success_url)

        except Exception as e:
            messages.error(self.request, f"Erro ao atualizar fechamento: {e}")
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        """
        Adiciona informações extras ao contexto.
        """
        context = super().get_context_data(**kwargs)
        context["title"] = "Editar Fechamento Diário"
        context["button_text"] = "Atualizar Fechamento"
        return context


class DailyClosingDeleteView(SuperuserRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Exclui um fechamento diário.
    Apenas superusuários podem excluir.
    """

    model = DailyClosing
    template_name = "finance/daily_closing_confirm_delete.html"
    success_url = reverse_lazy("closing-list")

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
            request, f"Fechamento de {date.strftime('%d/%m/%Y')} excluído com sucesso!"
        )

        return super().delete(request, *args, **kwargs)


# ============================================================================
# FECHAMENTO DO DIA — TELA UNIFICADA (nova arquitetura)
# ============================================================================


class DailyClosingTodayRedirectView(SuperuserRequiredMixin, RedirectView):
    """
    Redireciona /fechamento/ para a data de hoje.
    Permite que o menu sempre aponte para um link fixo.
    """

    def get_redirect_url(self, *args, **kwargs):
        today = timezone.now().date()
        return reverse("daily-closing", kwargs={"closing_date": today.isoformat()})


class DailyClosingUnifiedView(SuperuserRequiredMixin, TemplateView):
    """
    Tela unificada de Fechamento do Dia.

    Exibe vendas e despesas do dia em uma única tela.
    Detecta automaticamente se é criação ou edição pela data.
    Fase 2: apenas interface — lógica de salvar implementada na Fase 4.
    """

    template_name = "finance/daily_closing_unified.html"

    def _get_closing_date(self):
        closing_date_str = self.kwargs.get("closing_date", "")
        try:
            return datetime.strptime(closing_date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return timezone.now().date()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        closing_date = self._get_closing_date()

        # Não permitir datas futuras — redireciona para hoje silenciosamente
        if closing_date > today:
            closing_date = today

        try:
            closing = DailyClosing.objects.get(date=closing_date)
            is_edit = True
        except DailyClosing.DoesNotExist:
            closing = None
            is_edit = False

        expenses = (
            Expense.objects.filter(date=closing_date)
            .select_related("category")
            .order_by("created_at")
        )

        categories = ExpenseCategory.objects.filter(active=True)

        total_expenses = Expense.objects.filter(date=closing_date).aggregate(
            total=models.Sum("amount")
        )["total"] or Decimal("0.00")

        total_sales = closing.total_sales if closing else Decimal("0.00")
        average_ticket = closing.average_ticket if closing else Decimal("0.00")
        result = total_sales - total_expenses

        # URL template para navegação de data via JS (usa PLACEHOLDER como sentinela)
        fechamento_url_template = reverse("daily-closing", kwargs={"closing_date": "PLACEHOLDER"})

        closing_is_orders_source = (
            closing is not None and closing.source == DailyClosing.ClosingSource.ORDERS
        )

        context.update(
            {
                "closing_date": closing_date,
                "today": today,
                "closing": closing,
                "is_edit": is_edit,
                "expenses": expenses,
                "categories": categories,
                "total_expenses": total_expenses,
                "total_sales": total_sales,
                "average_ticket": average_ticket,
                "result": result,
                "prev_date_str": (closing_date - timedelta(1)).isoformat(),
                "next_date_str": (closing_date + timedelta(1)).isoformat()
                if closing_date < today
                else None,
                "fechamento_url_template": fechamento_url_template,
                "closing_is_orders_source": closing_is_orders_source,
            }
        )
        return context

    def post(self, request, closing_date):
        closing_date = self._get_closing_date()
        today = timezone.now().date()
        if closing_date > today:
            closing_date = today

        def safe_decimal(value):
            try:
                v = Decimal(str(value).replace(",", ".").strip())
                return v if v >= 0 else Decimal("0.00")
            except Exception:
                return Decimal("0.00")

        def safe_int(value):
            try:
                return max(0, int(str(value).strip()))
            except Exception:
                return 0

        order_count = safe_int(request.POST.get("order_count", "0"))
        cash_sales = safe_decimal(request.POST.get("cash_sales", "0"))
        pix_sales = safe_decimal(request.POST.get("pix_sales", "0"))
        card_sales = safe_decimal(request.POST.get("card_sales", "0"))
        notes = request.POST.get("notes", "").strip()

        expense_ids = request.POST.getlist("expense_id[]")
        expense_cats = request.POST.getlist("expense_category[]")
        expense_descs = request.POST.getlist("expense_description[]")
        expense_amts = request.POST.getlist("expense_amount[]")

        expense_rows = []
        for i in range(len(expense_cats)):
            cat_id = expense_cats[i] if i < len(expense_cats) else ""
            amt_str = expense_amts[i] if i < len(expense_amts) else ""
            desc = expense_descs[i] if i < len(expense_descs) else ""
            exp_id = expense_ids[i] if i < len(expense_ids) else ""

            if not cat_id or not amt_str:
                continue
            amt = safe_decimal(amt_str)
            if amt <= 0:
                continue

            expense_rows.append(
                {
                    "id": exp_id,
                    "category_id": cat_id,
                    "description": desc.strip(),
                    "amount": amt,
                }
            )

        try:
            with transaction.atomic():
                # 1. Criar ou atualizar DailyClosing
                try:
                    existing = DailyClosing.objects.get(date=closing_date)
                    if existing.source == DailyClosing.ClosingSource.ORDERS:
                        # Fechamento derivado de pedidos: só atualiza observações
                        update_daily_closing(closing=existing, notes=notes)
                    else:
                        update_daily_closing(
                            closing=existing,
                            order_count=order_count,
                            cash_sales=cash_sales,
                            pix_sales=pix_sales,
                            card_sales=card_sales,
                            notes=notes,
                        )
                except DailyClosing.DoesNotExist:
                    create_daily_closing(
                        date=closing_date,
                        order_count=order_count,
                        cash_sales=cash_sales,
                        pix_sales=pix_sales,
                        card_sales=card_sales,
                        notes=notes,
                    )

                # 2. Processar despesas
                cat_cache = {str(c.id): c for c in ExpenseCategory.objects.filter(active=True)}
                kept_ids = set()

                for row in expense_rows:
                    category = cat_cache.get(str(row["category_id"]))
                    if not category:
                        continue

                    if row["id"]:
                        try:
                            expense = Expense.objects.get(id=int(row["id"]), date=closing_date)
                            update_expense(
                                expense=expense,
                                category=category,
                                amount=row["amount"],
                                description=row["description"],
                            )
                            kept_ids.add(expense.id)
                        except (Expense.DoesNotExist, ValueError):
                            pass
                    else:
                        expense = create_expense(
                            date=closing_date,
                            category=category,
                            amount=row["amount"],
                            description=row["description"],
                        )
                        kept_ids.add(expense.id)

                # 3. Remover despesas desta data que o usuário excluiu
                Expense.objects.filter(date=closing_date).exclude(id__in=kept_ids).delete()

            messages.success(request, "Fechamento salvo com sucesso!")

            # Recalcular a partir dos pedidos se o fechamento é derivado de orders
            existing_after = DailyClosing.objects.filter(date=closing_date).first()
            if existing_after and existing_after.source == DailyClosing.ClosingSource.ORDERS:
                from orders.services import recalculate_closing_from_orders

                recalculate_closing_from_orders(date=closing_date)

        except Exception as e:
            messages.error(request, f"Erro ao salvar o fechamento: {e}")

        return redirect("daily-closing", closing_date=closing_date.isoformat())
