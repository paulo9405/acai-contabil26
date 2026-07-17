# PROJECT RULES — Gestão Financeira

Documento oficial de arquitetura, padrões e boas práticas do projeto.

---

## 1. Filosofia do Projeto

### Princípios Fundamentais

**Simplicidade acima de complexidade**
- Prefira soluções diretas a abstrações prematuras
- Evite adicionar funcionalidades "para o futuro"
- Três linhas duplicadas são melhores que uma abstração prematura

**Mobile First**
- Toda interface deve ser pensada primeiro para celular
- Resolução base: 390px
- Desktop é uma adaptação, não o contrário

**Menor número possível de cliques**
- Meta: registrar despesa em < 10 segundos
- Meta: registrar fechamento em < 20 segundos
- Cada clique extra é um fracasso de UX

**Interfaces para usuários não técnicos**
- Linguagem simples e direta
- Evitar jargões técnicos
- Mensagens de erro claras e acionáveis
- Foco em ações, não em conceitos

**Evitar overengineering**
- Não criar helpers para operações únicas
- Não criar abstrações para "possíveis" cenários futuros
- Não adicionar configurabilidade desnecessária
- YAGNI (You Aren't Gonna Need It)

**Evitar dependências desnecessárias**
- Usar recursos nativos do Django sempre que possível
- Cada nova dependência é um custo de manutenção
- Justifique toda nova biblioteca adicionada

---

## 2. Estrutura de Pastas

### Estrutura Oficial

```
gestao_financeira/
├── finance/
│   ├── models.py           # Modelos de dados
│   ├── forms.py            # Formulários
│   ├── views.py            # Views (lógica de apresentação)
│   ├── urls.py             # Roteamento
│   ├── services.py         # Regras de negócio e escrita
│   ├── selectors.py        # Queries e leitura
│   ├── admin.py            # Django Admin
│   ├── apps.py             # Configuração do app
│   ├── tests/              # Testes
│   │   ├── __init__.py
│   │   ├── test_models.py
│   │   ├── test_views.py
│   │   ├── test_services.py
│   │   └── test_forms.py
│   └── migrations/         # Migrations do banco
├── templates/
│   ├── base.html           # Template base
│   ├── finance/            # Templates do app finance
│   │   ├── dashboard.html
│   │   ├── expense_list.html
│   │   ├── expense_form.html
│   │   └── ...
│   └── registration/       # Templates de autenticação
│       ├── login.html
│       └── ...
├── static/
│   ├── css/
│   │   └── custom.css      # CSS customizado
│   ├── js/
│   │   └── charts.js       # JavaScript customizado
│   └── img/
├── gestao_financeira/      # Configurações do projeto
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── manage.py
```

### Responsabilidades

**models.py**
- Definição de modelos de dados
- Validações simples a nível de campo
- Propriedades calculadas simples
- Meta classes e índices

**forms.py**
- Formulários Django
- Validações de entrada
- Layout Bootstrap
- Mensagens de erro customizadas

**views.py**
- Lógica de apresentação
- Validação de permissões
- Delegação para services
- Preparação de contexto para templates

**urls.py**
- Roteamento de URLs
- Nomeação clara de rotas

**services.py**
- Regras de negócio
- Cálculos financeiros
- Criação e atualização de dados
- Lógica de validação complexa

**selectors.py**
- Queries de leitura
- Aggregations
- Filtros complexos
- Queries reutilizáveis

**admin.py**
- Configuração do Django Admin
- Apenas para uso administrativo

---

## 3. Convenções Django

### Quando usar CBV (Class-Based Views)

**Use CBV para:**
- CRUD completo (ListView, CreateView, UpdateView, DeleteView)
- Operações padrão do Django
- Quando os mixins agregam valor real

**Exemplo correto:**
```python
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin

class ExpenseListView(LoginRequiredMixin, ListView):
    model = Expense
    template_name = 'finance/expense_list.html'
    context_object_name = 'expenses'
    paginate_by = 20
```

### Quando usar FBV (Function-Based Views)

**Use FBV para:**
- Lógica personalizada que não se encaixa em CBV
- Dashboard com múltiplas fontes de dados
- Relatórios complexos
- Quando CBV adiciona mais complexidade que valor

**Exemplo correto:**
```python
from django.contrib.auth.decorators import login_required
from finance.selectors import get_dashboard_metrics

@login_required
def dashboard_view(request):
    metrics = get_dashboard_metrics()
    return render(request, 'finance/dashboard.html', {'metrics': metrics})
```

### Nomeação de Models

**Regras:**
- Singular, em inglês
- PascalCase
- Nome descritivo do domínio

**Exemplos:**
```python
class DailyClosing(models.Model):  # ✅ Correto
class ExpenseCategory(models.Model):  # ✅ Correto
class Expense(models.Model):  # ✅ Correto

class Despesa(models.Model):  # ❌ Português
class daily_closing(models.Model):  # ❌ snake_case
class Closings(models.Model):  # ❌ Plural
```

### Nomeação de Forms

**Regras:**
- Nome do modelo + "Form"
- PascalCase

**Exemplos:**
```python
class ExpenseForm(forms.ModelForm):  # ✅ Correto
class DailyClosingForm(forms.ModelForm):  # ✅ Correto

class FormDespesa(forms.ModelForm):  # ❌ Ordem errada
class expense_form(forms.ModelForm):  # ❌ snake_case
```

### Nomeação de Views

**Regras:**
- Ação + Modelo + "View" (CBV)
- Ação + contexto + "_view" (FBV)
- snake_case para funções

**Exemplos:**
```python
# CBV
class ExpenseListView(ListView):  # ✅ Correto
class ExpenseCreateView(CreateView):  # ✅ Correto

# FBV
def dashboard_view(request):  # ✅ Correto
def generate_report_view(request):  # ✅ Correto

def expense_list(request):  # ❌ Sem sufixo _view
def DashboardView(request):  # ❌ PascalCase em FBV
```

### Nomeação de URLs

**Regras:**
- kebab-case
- Descritivo
- Sem verbos HTTP (get, post)

**Exemplos:**
```python
urlpatterns = [
    path('dashboard/', dashboard_view, name='dashboard'),  # ✅
    path('expenses/', ExpenseListView.as_view(), name='expense-list'),  # ✅
    path('expenses/create/', ExpenseCreateView.as_view(), name='expense-create'),  # ✅
    path('expenses/<int:pk>/edit/', ExpenseUpdateView.as_view(), name='expense-edit'),  # ✅

    path('get-expenses/', ExpenseListView.as_view(), name='get_expenses'),  # ❌ Verbo HTTP
    path('expenses_list/', ExpenseListView.as_view(), name='expenses_list'),  # ❌ snake_case
]
```

### Nomeação de Templates

**Regras:**
- snake_case
- Nome do modelo + ação
- Dentro de pasta do app

**Exemplos:**
```
templates/finance/
    dashboard.html              # ✅ Correto
    expense_list.html           # ✅ Correto
    expense_form.html           # ✅ Correto
    daily_closing_list.html     # ✅ Correto

    ExpenseList.html            # ❌ PascalCase
    expense-list.html           # ❌ kebab-case
```

---

## 4. Regras de Views

### Princípio Fundamental

**Views devem ser finas e delegar responsabilidades.**

### ❌ ERRADO - View com Regras de Negócio

```python
def dashboard_view(request):
    # ❌ Cálculos na view
    today = timezone.now().date()
    closings_today = DailyClosing.objects.filter(date=today)

    total_sales = 0
    for closing in closings_today:
        total_sales += closing.cash_sales + closing.pix_sales + closing.card_sales

    expenses_today = Expense.objects.filter(date=today)
    total_expenses = sum(e.amount for e in expenses_today)

    profit = total_sales - total_expenses

    return render(request, 'finance/dashboard.html', {
        'total_sales': total_sales,
        'total_expenses': total_expenses,
        'profit': profit,
    })
```

### ✅ CORRETO - View Delegando para Services

```python
from finance.selectors import get_dashboard_metrics

def dashboard_view(request):
    # ✅ View apenas delega e prepara contexto
    metrics = get_dashboard_metrics()
    return render(request, 'finance/dashboard.html', {'metrics': metrics})
```

### Regras Obrigatórias

1. **Sem cálculos financeiros**
   - Todo cálculo vai para services.py

2. **Sem queries complexas**
   - Queries complexas vão para selectors.py

3. **Sem loops de processamento**
   - Processamento vai para services.py

4. **Apenas:**
   - Validação de permissões
   - Delegação para services/selectors
   - Preparação de contexto
   - Renderização de templates
   - Redirecionamentos

### Exemplo Completo Correto

```python
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from finance.forms import ExpenseForm
from finance.services import create_expense

@login_required
def expense_create_view(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            # ✅ Delega criação para service
            expense = create_expense(**form.cleaned_data)
            messages.success(request, 'Despesa registrada com sucesso!')
            return redirect('expense-list')
    else:
        form = ExpenseForm()

    return render(request, 'finance/expense_form.html', {'form': form})
```

---

## 5. Regras de Services

### Responsabilidades

**services.py contém:**
- Regras de negócio
- Cálculos financeiros
- Criação de registros
- Atualização de registros
- Validações complexas
- Lógica de dashboard

### Estrutura de Funções

```python
def create_something(*, field1, field2, field3):
    """
    Cria um registro de Something.

    Usa keyword-only arguments para maior clareza.
    """
    # Validações
    # Cálculos
    # Criação
    # Retorno
```

### Exemplos Corretos

```python
from decimal import Decimal
from django.utils import timezone
from finance.models import DailyClosing, Expense

def calculate_total_sales(*, closing: DailyClosing) -> Decimal:
    """
    Calcula o total de vendas de um fechamento.
    """
    return closing.cash_sales + closing.pix_sales + closing.card_sales

def calculate_daily_profit(*, date) -> Decimal:
    """
    Calcula o lucro de um dia específico.
    """
    try:
        closing = DailyClosing.objects.get(date=date)
        total_sales = calculate_total_sales(closing=closing)
    except DailyClosing.DoesNotExist:
        total_sales = Decimal('0')

    expenses = Expense.objects.filter(date=date)
    total_expenses = sum(e.amount for e in expenses)

    return total_sales - total_expenses

def calculate_average_ticket(*, closing: DailyClosing) -> Decimal:
    """
    Calcula o ticket médio de um fechamento.
    """
    if closing.order_count == 0:
        return Decimal('0')

    total_sales = calculate_total_sales(closing=closing)
    return total_sales / closing.order_count

def create_expense(*, date, category, amount, description=''):
    """
    Cria uma nova despesa.
    """
    from finance.models import Expense

    # Validação
    if amount <= 0:
        raise ValueError("Valor deve ser maior que zero")

    # Criação
    expense = Expense.objects.create(
        date=date,
        category=category,
        amount=amount,
        description=description
    )

    return expense

def create_daily_closing(*, date, order_count, cash_sales, pix_sales, card_sales, notes=''):
    """
    Cria um fechamento diário.

    Valida que não existe outro fechamento para a mesma data.
    """
    from finance.models import DailyClosing

    # Validação: apenas um fechamento por dia
    if DailyClosing.objects.filter(date=date).exists():
        raise ValueError(f"Já existe um fechamento para {date}")

    # Validação: data não pode ser futura
    if date > timezone.now().date():
        raise ValueError("Data não pode ser futura")

    # Criação
    closing = DailyClosing.objects.create(
        date=date,
        order_count=order_count,
        cash_sales=cash_sales,
        pix_sales=pix_sales,
        card_sales=card_sales,
        notes=notes
    )

    return closing
```

### Padrões Obrigatórios

1. **Usar keyword-only arguments** (`*,`)
2. **Docstrings descritivas**
3. **Type hints quando apropriado**
4. **Uma responsabilidade por função**
5. **Funções pequenas e focadas**
6. **Retornar valores, não None quando possível**

---

## 6. Regras de Selectors

### Responsabilidades

**selectors.py contém:**
- Queries de leitura
- Aggregations
- Filtros complexos
- Dados para relatórios
- Dados para dashboard

### Princípios

- **Read-only**: selectors NUNCA modificam dados
- **Reutilizáveis**: queries usadas em múltiplos lugares
- **Otimizados**: usar select_related, prefetch_related

### Exemplos Corretos

```python
from django.db.models import Sum, Avg, Count, Q
from django.utils import timezone
from finance.models import DailyClosing, Expense
from decimal import Decimal

def get_expenses_by_date_range(*, start_date, end_date):
    """
    Retorna despesas em um período.
    """
    return Expense.objects.filter(
        date__gte=start_date,
        date__lte=end_date
    ).select_related('category').order_by('-date')

def get_daily_closings_by_month(*, year, month):
    """
    Retorna fechamentos de um mês específico.
    """
    return DailyClosing.objects.filter(
        date__year=year,
        date__month=month
    ).order_by('date')

def get_total_expenses_by_category(*, start_date, end_date):
    """
    Retorna total de despesas por categoria em um período.
    """
    return Expense.objects.filter(
        date__gte=start_date,
        date__lte=end_date
    ).values('category__name').annotate(
        total=Sum('amount')
    ).order_by('-total')

def get_dashboard_metrics():
    """
    Retorna todas as métricas para o dashboard.
    """
    today = timezone.now().date()

    # Métricas do dia
    try:
        closing_today = DailyClosing.objects.get(date=today)
        sales_today = (
            closing_today.cash_sales +
            closing_today.pix_sales +
            closing_today.card_sales
        )
        orders_today = closing_today.order_count
        ticket_today = sales_today / orders_today if orders_today > 0 else Decimal('0')
    except DailyClosing.DoesNotExist:
        sales_today = Decimal('0')
        orders_today = 0
        ticket_today = Decimal('0')

    expenses_today = Expense.objects.filter(date=today).aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0')

    profit_today = sales_today - expenses_today

    # Métricas do mês
    first_day_month = today.replace(day=1)

    closings_month = DailyClosing.objects.filter(
        date__gte=first_day_month,
        date__lte=today
    ).aggregate(
        total_sales=Sum('cash_sales') + Sum('pix_sales') + Sum('card_sales'),
        total_orders=Sum('order_count')
    )

    sales_month = closings_month['total_sales'] or Decimal('0')
    orders_month = closings_month['total_orders'] or 0

    expenses_month = Expense.objects.filter(
        date__gte=first_day_month,
        date__lte=today
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    profit_month = sales_month - expenses_month
    ticket_month = sales_month / orders_month if orders_month > 0 else Decimal('0')

    return {
        'today': {
            'orders': orders_today,
            'sales': sales_today,
            'expenses': expenses_today,
            'profit': profit_today,
            'ticket': ticket_today,
        },
        'month': {
            'orders': orders_month,
            'sales': sales_month,
            'expenses': expenses_month,
            'profit': profit_month,
            'ticket': ticket_month,
        }
    }

def get_last_7_days_data():
    """
    Retorna dados dos últimos 7 dias para gráficos.
    """
    today = timezone.now().date()
    start_date = today - timezone.timedelta(days=6)

    closings = DailyClosing.objects.filter(
        date__gte=start_date,
        date__lte=today
    ).order_by('date')

    # Preparar dados para Chart.js
    dates = []
    sales = []
    expenses_data = []
    profit = []

    for closing in closings:
        total_sales = closing.cash_sales + closing.pix_sales + closing.card_sales
        total_expenses = Expense.objects.filter(
            date=closing.date
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        dates.append(closing.date.strftime('%d/%m'))
        sales.append(float(total_sales))
        expenses_data.append(float(total_expenses))
        profit.append(float(total_sales - total_expenses))

    return {
        'dates': dates,
        'sales': sales,
        'expenses': expenses_data,
        'profit': profit,
    }
```

### Padrões Obrigatórios

1. **Keyword-only arguments**
2. **Docstrings descritivas**
3. **Usar select_related para ForeignKey**
4. **Usar prefetch_related para ManyToMany**
5. **Nunca modificar dados**
6. **Retornar QuerySets ou dicts estruturados**

---

## 7. Regras de Models

### Responsabilidades

**Models representam apenas dados e comportamentos simples.**

### ❌ ERRADO - Lógica Pesada no Model

```python
class DailyClosing(models.Model):
    date = models.DateField()
    order_count = models.PositiveIntegerField()
    cash_sales = models.DecimalField(max_digits=10, decimal_places=2)
    pix_sales = models.DecimalField(max_digits=10, decimal_places=2)
    card_sales = models.DecimalField(max_digits=10, decimal_places=2)

    # ❌ Lógica complexa no model
    def calculate_profit(self):
        expenses = Expense.objects.filter(date=self.date)
        total_expenses = sum(e.amount for e in expenses)
        return self.total_sales - total_expenses
```

### ✅ CORRETO - Model Simples

```python
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

class DailyClosing(models.Model):
    """
    Fechamento diário de vendas.
    """
    date = models.DateField(
        unique=True,
        verbose_name='Data',
        help_text='Data do fechamento'
    )
    order_count = models.PositiveIntegerField(
        verbose_name='Quantidade de Pedidos',
        validators=[MinValueValidator(0)]
    )
    cash_sales = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Vendas em Dinheiro',
        validators=[MinValueValidator(Decimal('0'))]
    )
    pix_sales = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Vendas em Pix',
        validators=[MinValueValidator(Decimal('0'))]
    )
    card_sales = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Vendas em Cartão',
        validators=[MinValueValidator(Decimal('0'))]
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Observações'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Fechamento Diário'
        verbose_name_plural = 'Fechamentos Diários'
        ordering = ['-date']
        indexes = [
            models.Index(fields=['-date']),
        ]

    # ✅ Property simples - apenas cálculo direto
    @property
    def total_sales(self):
        """Calcula o total de vendas."""
        return self.cash_sales + self.pix_sales + self.card_sales

    def __str__(self):
        return f"Fechamento {self.date.strftime('%d/%m/%Y')}"
```

### Regras Obrigatórias

1. **verbose_name em todos os campos**
2. **help_text quando necessário**
3. **Validators para regras de validação**
4. **Meta class com ordering e indexes**
5. **Properties apenas para cálculos simples**
6. **__str__ descritivo**
7. **Docstring na classe**

### Exemplo Completo

```python
class Expense(models.Model):
    """
    Despesa do negócio.
    """
    date = models.DateField(
        verbose_name='Data',
        help_text='Data da despesa'
    )
    category = models.ForeignKey(
        'ExpenseCategory',
        on_delete=models.PROTECT,
        verbose_name='Categoria',
        related_name='expenses'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Valor',
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descrição'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Despesa'
        verbose_name_plural = 'Despesas'
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['-date']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return f"{self.category.name} - R$ {self.amount} ({self.date.strftime('%d/%m/%Y')})"
```

---

## 8. Regras de Forms

### Responsabilidades

- Validação de entrada
- Layout Bootstrap
- Mensagens de erro customizadas
- Campos obrigatórios e opcionais

### Exemplo Correto

```python
from django import forms
from finance.models import Expense, DailyClosing
from django.core.exceptions import ValidationError
from django.utils import timezone

class ExpenseForm(forms.ModelForm):
    """
    Formulário para registro de despesas.
    """
    class Meta:
        model = Expense
        fields = ['date', 'category', 'amount', 'description']
        widgets = {
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control form-control-lg',
            }),
            'category': forms.Select(attrs={
                'class': 'form-select form-select-lg',
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0,00',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descrição opcional',
            }),
        }
        labels = {
            'date': 'Data',
            'category': 'Categoria',
            'amount': 'Valor (R$)',
            'description': 'Descrição',
        }

    def clean_date(self):
        """Valida que a data não é futura."""
        date = self.cleaned_data.get('date')
        if date and date > timezone.now().date():
            raise ValidationError('A data não pode ser futura.')
        return date

    def clean_amount(self):
        """Valida que o valor é positivo."""
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise ValidationError('O valor deve ser maior que zero.')
        return amount

class DailyClosingForm(forms.ModelForm):
    """
    Formulário para fechamento diário.
    """
    class Meta:
        model = DailyClosing
        fields = ['date', 'order_count', 'cash_sales', 'pix_sales', 'card_sales', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control form-control-lg',
            }),
            'order_count': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'min': '0',
                'placeholder': '0',
            }),
            'cash_sales': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'step': '0.01',
                'min': '0',
                'placeholder': '0,00',
            }),
            'pix_sales': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'step': '0.01',
                'min': '0',
                'placeholder': '0,00',
            }),
            'card_sales': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'step': '0.01',
                'min': '0',
                'placeholder': '0,00',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações opcionais',
            }),
        }

    def clean(self):
        """Validações customizadas."""
        cleaned_data = super().clean()
        date = cleaned_data.get('date')

        # Valida data futura
        if date and date > timezone.now().date():
            raise ValidationError('A data não pode ser futura.')

        # Valida fechamento duplicado
        if date and self.instance.pk is None:  # Apenas na criação
            if DailyClosing.objects.filter(date=date).exists():
                raise ValidationError(f'Já existe um fechamento para {date.strftime("%d/%m/%Y")}.')

        return cleaned_data
```

### Padrões Obrigatórios

1. **Todos os inputs com classes Bootstrap**
2. **form-control-lg para inputs principais**
3. **Placeholders descritivos**
4. **Labels em português**
5. **Validações customizadas quando necessário**
6. **Mensagens de erro claras**

---

## 9. Responsividade

### Princípio Mobile First

**Toda interface deve funcionar perfeitamente em 390px de largura.**

### Regras Obrigatórias

**Largura Base**
- Resolução mínima: 390px
- Testar em iPhone SE, iPhone 12/13/14

**Botões**
- Altura mínima: 48px
- Largura confortável para toque
- Espaçamento adequado entre botões

**Cards**
- Empilhados verticalmente em mobile
- Grade em desktop (2-3 colunas)

**Tabelas**
- Máximo 3 colunas em mobile
- Scroll horizontal se necessário
- Considerar cards ao invés de tabelas

**Formulários**
- Um campo por linha
- Labels acima dos campos
- Inputs grandes (form-control-lg)

**Navegação**
- Navbar collapse em mobile
- Ícones + texto quando possível

### Exemplo de Estrutura Responsiva

```html
<!-- Dashboard Cards -->
<div class="row g-3">
    <!-- Mobile: 1 coluna, Tablet: 2 colunas, Desktop: 4 colunas -->
    <div class="col-12 col-md-6 col-lg-3">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Vendas Hoje</h5>
                <h2 class="text-success">R$ 650,00</h2>
            </div>
        </div>
    </div>
    <!-- Repetir para outros cards -->
</div>

<!-- Botões Mobile -->
<div class="d-grid gap-2">
    <button class="btn btn-primary btn-lg">Novo Fechamento</button>
    <button class="btn btn-success btn-lg">Nova Despesa</button>
</div>
```

---

## 10. Bootstrap

### Estrutura de Formulários

```html
<form method="post">
    {% csrf_token %}

    <div class="mb-3">
        <label for="{{ form.date.id_for_label }}" class="form-label">
            {{ form.date.label }}
        </label>
        {{ form.date }}
        {% if form.date.errors %}
            <div class="invalid-feedback d-block">
                {{ form.date.errors }}
            </div>
        {% endif %}
    </div>

    <div class="d-grid gap-2">
        <button type="submit" class="btn btn-primary btn-lg">Salvar</button>
        <a href="{% url 'expense-list' %}" class="btn btn-outline-secondary">Cancelar</a>
    </div>
</form>
```

### Estrutura de Cards

```html
<div class="card">
    <div class="card-header">
        <h5 class="mb-0">Título do Card</h5>
    </div>
    <div class="card-body">
        <p class="card-text">Conteúdo</p>
    </div>
</div>
```

### Estrutura de Dashboard

```html
<!-- Métricas -->
<div class="row g-3 mb-4">
    <div class="col-12 col-md-6 col-lg-3">
        <div class="card text-center">
            <div class="card-body">
                <small class="text-muted">Pedidos Hoje</small>
                <h2 class="mb-0">18</h2>
            </div>
        </div>
    </div>
</div>

<!-- Ações Rápidas -->
<div class="row g-2 mb-4">
    <div class="col-12 col-md-4">
        <a href="#" class="btn btn-primary btn-lg w-100">
            Novo Fechamento
        </a>
    </div>
</div>
```

### Estrutura de Tabelas

```html
<div class="table-responsive">
    <table class="table table-hover">
        <thead>
            <tr>
                <th>Data</th>
                <th>Categoria</th>
                <th class="text-end">Valor</th>
            </tr>
        </thead>
        <tbody>
            {% for expense in expenses %}
            <tr>
                <td>{{ expense.date|date:"d/m/Y" }}</td>
                <td>{{ expense.category }}</td>
                <td class="text-end">R$ {{ expense.amount }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
```

---

## 11. Banco de Dados

### PostgreSQL em Produção

**Configuração:**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', default='5432'),
    }
}
```

### Tipos de Dados

**Valores Monetários**
```python
amount = models.DecimalField(
    max_digits=10,
    decimal_places=2,
    validators=[MinValueValidator(Decimal('0'))]
)
```

**Datas Financeiras**
```python
date = models.DateField()  # Sem timezone para datas financeiras
```

**Timestamps**
```python
created_at = models.DateTimeField(auto_now_add=True)
updated_at = models.DateTimeField(auto_now=True)
```

### Índices Recomendados

```python
class Meta:
    indexes = [
        models.Index(fields=['-date']),  # Queries por data DESC
        models.Index(fields=['category']),  # Filtros por categoria
        models.Index(fields=['date', 'category']),  # Queries compostas
    ]
```

### Regras Obrigatórias

1. **DecimalField para dinheiro** (nunca FloatField)
2. **DateField para datas financeiras** (sem timezone)
3. **Índices em campos filtrados com frequência**
4. **ForeignKey com on_delete explícito**
5. **unique=True quando apenas um registro por critério**

---

## 12. Segurança

### Login Obrigatório

**Todas as views devem exigir autenticação.**

**FBV:**
```python
from django.contrib.auth.decorators import login_required

@login_required
def dashboard_view(request):
    pass
```

**CBV:**
```python
from django.contrib.auth.mixins import LoginRequiredMixin

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'finance/dashboard.html'
```

### CSRF

**Sempre habilitado.**
```html
<form method="post">
    {% csrf_token %}
    <!-- form fields -->
</form>
```

### Permissões

**Exclusão apenas para superusuários:**
```python
from django.contrib.auth.mixins import UserPassesTestMixin

class ExpenseDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Expense

    def test_func(self):
        return self.request.user.is_superuser
```

### Senhas

**Usar validadores padrão do Django:**
```python
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
```

### Variáveis de Ambiente

**Nunca commitar secrets:**
```python
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
```

---

## 13. Testes

### Estrutura

```
finance/tests/
├── __init__.py
├── test_models.py
├── test_forms.py
├── test_views.py
├── test_services.py
└── test_selectors.py
```

### Ferramentas

- **pytest**
- **pytest-django**
- **coverage**

### Cobertura Mínima

**80% de cobertura obrigatória.**

### O Que Testar

**Models:**
- Validações
- Properties
- __str__
- Constraints

**Forms:**
- Validações customizadas
- Clean methods
- Required fields

**Services:**
- Regras de negócio
- Cálculos
- Validações
- Edge cases

**Selectors:**
- Queries retornam dados corretos
- Filtros funcionam
- Aggregations corretas

**Views:**
- Autenticação obrigatória
- Redirecionamentos
- Contexto correto

### Exemplo de Teste

```python
import pytest
from decimal import Decimal
from django.utils import timezone
from finance.models import DailyClosing
from finance.services import calculate_total_sales, create_daily_closing

@pytest.mark.django_db
class TestDailyClosingServices:

    def test_calculate_total_sales(self):
        """Testa cálculo de vendas totais."""
        closing = DailyClosing.objects.create(
            date=timezone.now().date(),
            order_count=10,
            cash_sales=Decimal('100.00'),
            pix_sales=Decimal('200.00'),
            card_sales=Decimal('150.00'),
        )

        total = calculate_total_sales(closing=closing)

        assert total == Decimal('450.00')

    def test_create_daily_closing_duplicate_date_raises_error(self):
        """Testa que não permite fechamentos duplicados."""
        date = timezone.now().date()

        create_daily_closing(
            date=date,
            order_count=10,
            cash_sales=Decimal('100'),
            pix_sales=Decimal('200'),
            card_sales=Decimal('150'),
        )

        with pytest.raises(ValueError, match="Já existe um fechamento"):
            create_daily_closing(
                date=date,
                order_count=5,
                cash_sales=Decimal('50'),
                pix_sales=Decimal('100'),
                card_sales=Decimal('75'),
            )
```

### Rodar Testes

```bash
# Rodar todos os testes
pytest

# Com cobertura
pytest --cov=finance --cov-report=html

# Apenas um arquivo
pytest finance/tests/test_services.py

# Apenas um teste
pytest finance/tests/test_services.py::TestDailyClosingServices::test_calculate_total_sales
```

---

## 14. Performance

### N+1 Queries

**❌ ERRADO:**
```python
def expense_list_view(request):
    expenses = Expense.objects.all()  # ❌ N+1 ao acessar category
    return render(request, 'finance/expense_list.html', {'expenses': expenses})
```

**✅ CORRETO:**
```python
def expense_list_view(request):
    expenses = Expense.objects.select_related('category').all()  # ✅
    return render(request, 'finance/expense_list.html', {'expenses': expenses})
```

### select_related vs prefetch_related

**select_related (ForeignKey, OneToOne):**
```python
# Uma query com JOIN
expenses = Expense.objects.select_related('category')
```

**prefetch_related (ManyToMany, reverse ForeignKey):**
```python
# Duas queries, uma para cada lado
categories = ExpenseCategory.objects.prefetch_related('expenses')
```

### Paginação Obrigatória

**Listagens devem ser paginadas:**
```python
class ExpenseListView(LoginRequiredMixin, ListView):
    model = Expense
    paginate_by = 20  # ✅ Obrigatório
```

### QuerySet Evaluation

**Evitar múltiplas avaliações:**

**❌ ERRADO:**
```python
expenses = Expense.objects.filter(date=today)
count = len(expenses)  # Avaliação 1
total = sum(e.amount for e in expenses)  # Avaliação 2
```

**✅ CORRETO:**
```python
result = Expense.objects.filter(date=today).aggregate(
    count=Count('id'),
    total=Sum('amount')
)
count = result['count']
total = result['total']
```

### Debug Toolbar

**Usar em desenvolvimento:**
```python
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
```

---

## 15. Checklist de Pull Request

Antes de criar um PR, verifique:

### Código

- [ ] Código segue padrões de nomenclatura
- [ ] Sem regras de negócio nas views
- [ ] Sem consultas complexas nas views
- [ ] Services documentados com docstrings
- [ ] Selectors documentados com docstrings
- [ ] Sem código comentado
- [ ] Sem prints ou debugs

### Models

- [ ] verbose_name em todos os campos
- [ ] Meta class configurada
- [ ] Índices necessários criados
- [ ] Validators aplicados
- [ ] __str__ implementado

### Forms

- [ ] Classes Bootstrap aplicadas
- [ ] Labels em português
- [ ] Placeholders descritivos
- [ ] Validações customizadas quando necessário

### Views

- [ ] LoginRequiredMixin ou @login_required
- [ ] Delegação para services/selectors
- [ ] Sem cálculos ou queries complexas

### Templates

- [ ] Responsivo (testado em 390px)
- [ ] Bootstrap aplicado corretamente
- [ ] Botões com tamanho adequado (min 48px)
- [ ] Formulários mobile-friendly
- [ ] CSRF token presente

### Testes

- [ ] Testes criados para novos serviços
- [ ] Testes criados para novos selectors
- [ ] Testes passando (pytest)
- [ ] Cobertura >= 80%

### Performance

- [ ] select_related usado em ForeignKeys
- [ ] prefetch_related usado quando necessário
- [ ] Paginação em listagens
- [ ] Sem N+1 queries

### Segurança

- [ ] Autenticação obrigatória
- [ ] CSRF habilitado
- [ ] Sem secrets no código
- [ ] Validações de entrada

### Banco de Dados

- [ ] Migrations criadas
- [ ] Migrations testadas
- [ ] DecimalField para valores monetários
- [ ] Índices criados para campos filtrados

### Documentação

- [ ] Docstrings em funções complexas
- [ ] Comentários apenas quando necessário
- [ ] README atualizado se necessário

---

## 16. Comandos Úteis

### Desenvolvimento

```bash
# Criar ambiente virtual
python3.12 -m venv venv

# Ativar ambiente
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Migrations
python manage.py makemigrations
python manage.py migrate

# Rodar servidor
python manage.py runserver

# Criar superusuário
python manage.py createsuperuser

# Shell
python manage.py shell
```

### Testes

```bash
# Rodar testes
pytest

# Com cobertura
pytest --cov=finance --cov-report=html

# Verificar cobertura
open htmlcov/index.html
```

### Produção

```bash
# Coletar arquivos estáticos
python manage.py collectstatic --noinput

# Rodar com Gunicorn
gunicorn gestao_financeira.wsgi:application
```

---

## 17. Referências

- [Django Documentation](https://docs.djangoproject.com/)
- [Bootstrap 5 Documentation](https://getbootstrap.com/docs/5.3/)
- [Chart.js Documentation](https://www.chartjs.org/)
- [pytest-django](https://pytest-django.readthedocs.io/)
- [WhiteNoise](http://whitenoise.evans.io/)

---

**Este documento é a fonte oficial de verdade para o projeto.**

Qualquer dúvida ou decisão técnica deve ser consultada aqui primeiro.

Atualize este documento conforme o projeto evolui.
