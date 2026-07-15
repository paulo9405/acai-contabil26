"""
Business logic and data manipulation functions.

All business rules, calculations, and data modifications should be placed here.
Views should remain thin and delegate complex operations to services.
"""

from decimal import Decimal
from datetime import date, timedelta
from typing import Dict, Any
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Sum
from finance.models import DailyClosing, Expense, ExpenseCategory


# ============================================================================
# CÁLCULOS BÁSICOS
# ============================================================================

def calculate_total_sales(*, closing: DailyClosing) -> Decimal:
    """
    Calcula o total de vendas de um fechamento diário.

    Args:
        closing: Instância de DailyClosing

    Returns:
        Total de vendas (soma de dinheiro, pix e cartão)
    """
    return closing.cash_sales + closing.pix_sales + closing.card_sales


def calculate_average_ticket(*, closing: DailyClosing) -> Decimal:
    """
    Calcula o ticket médio de um fechamento.

    Args:
        closing: Instância de DailyClosing

    Returns:
        Ticket médio (vendas / pedidos). Retorna 0 se não houver pedidos.
    """
    if closing.order_count == 0:
        return Decimal('0.00')

    total_sales = calculate_total_sales(closing=closing)
    return total_sales / closing.order_count


def calculate_total_expenses(*, date: date) -> Decimal:
    """
    Calcula o total de despesas de uma data específica.

    Args:
        date: Data para calcular as despesas

    Returns:
        Total de despesas da data
    """
    result = Expense.objects.filter(date=date).aggregate(
        total=Sum('amount')
    )
    return result['total'] or Decimal('0.00')


def calculate_daily_profit(*, date: date) -> Decimal:
    """
    Calcula o lucro de um dia específico.

    Args:
        date: Data para calcular o lucro

    Returns:
        Lucro do dia (vendas - despesas)
    """
    try:
        closing = DailyClosing.objects.get(date=date)
        total_sales = calculate_total_sales(closing=closing)
    except DailyClosing.DoesNotExist:
        total_sales = Decimal('0.00')

    total_expenses = calculate_total_expenses(date=date)
    return total_sales - total_expenses


def calculate_period_sales(*, start_date: date, end_date: date) -> Decimal:
    """
    Calcula o total de vendas em um período.

    Args:
        start_date: Data inicial
        end_date: Data final

    Returns:
        Total de vendas no período
    """
    closings = DailyClosing.objects.filter(
        date__gte=start_date,
        date__lte=end_date
    ).aggregate(
        cash=Sum('cash_sales'),
        pix=Sum('pix_sales'),
        card=Sum('card_sales')
    )

    total = Decimal('0.00')
    if closings['cash']:
        total += closings['cash']
    if closings['pix']:
        total += closings['pix']
    if closings['card']:
        total += closings['card']

    return total


def calculate_period_expenses(*, start_date: date, end_date: date) -> Decimal:
    """
    Calcula o total de despesas em um período.

    Args:
        start_date: Data inicial
        end_date: Data final

    Returns:
        Total de despesas no período
    """
    result = Expense.objects.filter(
        date__gte=start_date,
        date__lte=end_date
    ).aggregate(total=Sum('amount'))

    return result['total'] or Decimal('0.00')


def calculate_period_profit(*, start_date: date, end_date: date) -> Decimal:
    """
    Calcula o lucro em um período.

    Args:
        start_date: Data inicial
        end_date: Data final

    Returns:
        Lucro do período (vendas - despesas)
    """
    sales = calculate_period_sales(start_date=start_date, end_date=end_date)
    expenses = calculate_period_expenses(start_date=start_date, end_date=end_date)
    return sales - expenses


def calculate_period_orders(*, start_date: date, end_date: date) -> int:
    """
    Calcula o total de pedidos em um período.

    Args:
        start_date: Data inicial
        end_date: Data final

    Returns:
        Total de pedidos no período
    """
    result = DailyClosing.objects.filter(
        date__gte=start_date,
        date__lte=end_date
    ).aggregate(total=Sum('order_count'))

    return result['total'] or 0


def calculate_period_average_ticket(*, start_date: date, end_date: date) -> Decimal:
    """
    Calcula o ticket médio em um período.

    Args:
        start_date: Data inicial
        end_date: Data final

    Returns:
        Ticket médio do período. Retorna 0 se não houver pedidos.
    """
    total_orders = calculate_period_orders(start_date=start_date, end_date=end_date)

    if total_orders == 0:
        return Decimal('0.00')

    total_sales = calculate_period_sales(start_date=start_date, end_date=end_date)
    return total_sales / total_orders


# ============================================================================
# MÉTRICAS POR PERÍODO
# ============================================================================

def get_daily_metrics(*, target_date: date = None) -> Dict[str, Any]:
    """
    Retorna métricas financeiras de um dia específico.

    Args:
        target_date: Data para calcular métricas. Se None, usa hoje.

    Returns:
        Dicionário com métricas do dia:
        {
            'date': date,
            'orders': int,
            'sales': Decimal,
            'expenses': Decimal,
            'profit': Decimal,
            'average_ticket': Decimal
        }
    """
    if target_date is None:
        target_date = timezone.now().date()

    # Buscar fechamento do dia
    try:
        closing = DailyClosing.objects.get(date=target_date)
        orders = closing.order_count
        sales = calculate_total_sales(closing=closing)
        average_ticket = calculate_average_ticket(closing=closing)
    except DailyClosing.DoesNotExist:
        orders = 0
        sales = Decimal('0.00')
        average_ticket = Decimal('0.00')

    # Calcular despesas
    expenses = calculate_total_expenses(date=target_date)

    # Calcular lucro
    profit = sales - expenses

    return {
        'date': target_date,
        'orders': orders,
        'sales': sales,
        'expenses': expenses,
        'profit': profit,
        'average_ticket': average_ticket,
    }


def get_monthly_metrics(*, year: int = None, month: int = None) -> Dict[str, Any]:
    """
    Retorna métricas financeiras de um mês específico.

    Args:
        year: Ano do mês. Se None, usa ano atual.
        month: Mês (1-12). Se None, usa mês atual.

    Returns:
        Dicionário com métricas do mês:
        {
            'year': int,
            'month': int,
            'orders': int,
            'sales': Decimal,
            'expenses': Decimal,
            'profit': Decimal,
            'average_ticket': Decimal,
            'days_with_closing': int
        }
    """
    today = timezone.now().date()

    if year is None:
        year = today.year
    if month is None:
        month = today.month

    # Primeiro e último dia do mês
    first_day = date(year, month, 1)

    # Último dia do mês
    if month == 12:
        last_day = date(year, 12, 31)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)

    # Não permitir datas futuras
    if last_day > today:
        last_day = today

    # Calcular métricas
    orders = calculate_period_orders(start_date=first_day, end_date=last_day)
    sales = calculate_period_sales(start_date=first_day, end_date=last_day)
    expenses = calculate_period_expenses(start_date=first_day, end_date=last_day)
    profit = sales - expenses
    average_ticket = calculate_period_average_ticket(start_date=first_day, end_date=last_day)

    # Contar dias com fechamento
    days_with_closing = DailyClosing.objects.filter(
        date__gte=first_day,
        date__lte=last_day
    ).count()

    return {
        'year': year,
        'month': month,
        'orders': orders,
        'sales': sales,
        'expenses': expenses,
        'profit': profit,
        'average_ticket': average_ticket,
        'days_with_closing': days_with_closing,
        'first_day': first_day,
        'last_day': last_day,
    }


def get_dashboard_metrics() -> Dict[str, Any]:
    """
    Retorna todas as métricas necessárias para o dashboard.

    Returns:
        Dicionário com métricas do dia e do mês:
        {
            'today': {...},  # Métricas do dia
            'month': {...}   # Métricas do mês
        }
    """
    today_metrics = get_daily_metrics()
    month_metrics = get_monthly_metrics()

    return {
        'today': today_metrics,
        'month': month_metrics,
    }


# ============================================================================
# CRIAÇÃO DE DADOS
# ============================================================================

def create_expense_category(*, name: str, active: bool = True) -> ExpenseCategory:
    """
    Cria uma nova categoria de despesa.

    Args:
        name: Nome da categoria
        active: Se a categoria está ativa (default: True)

    Returns:
        Instância de ExpenseCategory criada

    Raises:
        ValidationError: Se já existe categoria com este nome
    """
    # Verificar se já existe
    if ExpenseCategory.objects.filter(name=name).exists():
        raise ValidationError(f'Já existe uma categoria com o nome "{name}".')

    category = ExpenseCategory.objects.create(
        name=name,
        active=active
    )

    return category


def create_expense(
    *,
    date: date,
    category: ExpenseCategory,
    amount: Decimal,
    description: str = ''
) -> Expense:
    """
    Cria uma nova despesa.

    Args:
        date: Data da despesa
        category: Categoria da despesa
        amount: Valor da despesa
        description: Descrição opcional da despesa

    Returns:
        Instância de Expense criada

    Raises:
        ValidationError: Se os dados forem inválidos
    """
    # Validações de negócio
    if amount <= 0:
        raise ValidationError('O valor da despesa deve ser maior que zero.')

    # Criar despesa
    expense = Expense.objects.create(
        date=date,
        category=category,
        amount=amount,
        description=description
    )

    return expense


def create_daily_closing(
    *,
    date: date,
    order_count: int,
    cash_sales: Decimal,
    pix_sales: Decimal,
    card_sales: Decimal,
    notes: str = '',
    source: str = DailyClosing.ClosingSource.MANUAL
) -> DailyClosing:
    """
    Cria um fechamento diário.

    Args:
        date: Data do fechamento
        order_count: Quantidade de pedidos
        cash_sales: Vendas em dinheiro
        pix_sales: Vendas em Pix
        card_sales: Vendas em cartão
        notes: Observações opcionais

    Returns:
        Instância de DailyClosing criada

    Raises:
        ValidationError: Se os dados forem inválidos ou já existir fechamento
    """
    # Validação: apenas um fechamento por dia
    if DailyClosing.objects.filter(date=date).exists():
        raise ValidationError(f'Já existe um fechamento para {date.strftime("%d/%m/%Y")}.')

    # Validação: data não pode ser futura
    if date > timezone.now().date():
        raise ValidationError('A data não pode ser futura.')

    # Validação: valores não podem ser negativos
    if cash_sales < 0 or pix_sales < 0 or card_sales < 0:
        raise ValidationError('Os valores de vendas não podem ser negativos.')

    # Validação: quantidade de pedidos não pode ser negativa
    if order_count < 0:
        raise ValidationError('A quantidade de pedidos não pode ser negativa.')

    # Criar fechamento
    closing = DailyClosing.objects.create(
        date=date,
        order_count=order_count,
        cash_sales=cash_sales,
        pix_sales=pix_sales,
        card_sales=card_sales,
        notes=notes,
        source=source,
    )

    return closing


def update_daily_closing(
    *,
    closing: DailyClosing,
    order_count: int = None,
    cash_sales: Decimal = None,
    pix_sales: Decimal = None,
    card_sales: Decimal = None,
    notes: str = None,
    source: str = None
) -> DailyClosing:
    """
    Atualiza um fechamento diário existente.

    Args:
        closing: Instância do fechamento a ser atualizado
        order_count: Nova quantidade de pedidos (opcional)
        cash_sales: Novo valor de vendas em dinheiro (opcional)
        pix_sales: Novo valor de vendas em Pix (opcional)
        card_sales: Novo valor de vendas em cartão (opcional)
        notes: Novas observações (opcional)

    Returns:
        Instância de DailyClosing atualizada

    Raises:
        ValidationError: Se os dados forem inválidos
    """
    # Atualizar apenas os campos fornecidos
    if order_count is not None:
        if order_count < 0:
            raise ValidationError('A quantidade de pedidos não pode ser negativa.')
        closing.order_count = order_count

    if cash_sales is not None:
        if cash_sales < 0:
            raise ValidationError('O valor de vendas em dinheiro não pode ser negativo.')
        closing.cash_sales = cash_sales

    if pix_sales is not None:
        if pix_sales < 0:
            raise ValidationError('O valor de vendas em Pix não pode ser negativo.')
        closing.pix_sales = pix_sales

    if card_sales is not None:
        if card_sales < 0:
            raise ValidationError('O valor de vendas em cartão não pode ser negativo.')
        closing.card_sales = card_sales

    if notes is not None:
        closing.notes = notes

    if source is not None:
        closing.source = source

    closing.save()
    return closing


def update_expense(
    *,
    expense: Expense,
    date: date = None,
    category: ExpenseCategory = None,
    amount: Decimal = None,
    description: str = None
) -> Expense:
    """
    Atualiza uma despesa existente.

    Args:
        expense: Instância da despesa a ser atualizada
        date: Nova data (opcional)
        category: Nova categoria (opcional)
        amount: Novo valor (opcional)
        description: Nova descrição (opcional)

    Returns:
        Instância de Expense atualizada

    Raises:
        ValidationError: Se os dados forem inválidos
    """
    # Atualizar apenas os campos fornecidos
    if date is not None:
        expense.date = date

    if category is not None:
        expense.category = category

    if amount is not None:
        if amount <= 0:
            raise ValidationError('O valor da despesa deve ser maior que zero.')
        expense.amount = amount

    if description is not None:
        expense.description = description

    expense.save()
    return expense
