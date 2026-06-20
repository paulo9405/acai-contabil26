from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal


class ExpenseCategory(models.Model):
    """
    Categoria de despesa.

    Exemplos: Ingredientes, Embalagens, Combustível, etc.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Nome',
        help_text='Nome da categoria'
    )
    active = models.BooleanField(
        default=True,
        verbose_name='Ativa',
        help_text='Categoria ativa para uso'
    )

    class Meta:
        verbose_name = 'Categoria de Despesa'
        verbose_name_plural = 'Categorias de Despesas'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['active']),
        ]

    def __str__(self):
        return self.name


class DailyClosing(models.Model):
    """
    Fechamento diário de vendas.

    Registra o resumo financeiro de um dia de operação.
    Apenas um fechamento permitido por data.
    """
    date = models.DateField(
        unique=True,
        verbose_name='Data',
        help_text='Data do fechamento (única por dia)'
    )
    order_count = models.PositiveIntegerField(
        verbose_name='Quantidade de Pedidos',
        help_text='Total de pedidos realizados no dia',
        validators=[MinValueValidator(0)]
    )
    cash_sales = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Vendas em Dinheiro',
        help_text='Total de vendas pagas em dinheiro',
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    pix_sales = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Vendas em Pix',
        help_text='Total de vendas pagas via Pix',
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    card_sales = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Vendas em Cartão',
        help_text='Total de vendas pagas com cartão',
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Observações',
        help_text='Observações sobre o dia (opcional)'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em'
    )

    class Meta:
        verbose_name = 'Fechamento Diário'
        verbose_name_plural = 'Fechamentos Diários'
        ordering = ['-date']
        indexes = [
            models.Index(fields=['-date']),
        ]

    def clean(self):
        """
        Validações customizadas do modelo.
        """
        super().clean()

        # Validação: data não pode ser futura
        if self.date and self.date > timezone.now().date():
            raise ValidationError({
                'date': 'A data não pode ser futura.'
            })

        # Validação: valores não podem ser negativos (reforço do validator)
        if self.cash_sales and self.cash_sales < 0:
            raise ValidationError({
                'cash_sales': 'O valor não pode ser negativo.'
            })
        if self.pix_sales and self.pix_sales < 0:
            raise ValidationError({
                'pix_sales': 'O valor não pode ser negativo.'
            })
        if self.card_sales and self.card_sales < 0:
            raise ValidationError({
                'card_sales': 'O valor não pode ser negativo.'
            })

    def save(self, *args, **kwargs):
        """
        Sobrescreve save para executar validações.
        """
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def total_sales(self):
        """
        Calcula o total de vendas do dia.
        """
        return self.cash_sales + self.pix_sales + self.card_sales

    @property
    def average_ticket(self):
        """
        Calcula o ticket médio do dia.
        Retorna 0 se não houver pedidos.
        """
        if self.order_count == 0:
            return Decimal('0.00')
        return self.total_sales / self.order_count

    def __str__(self):
        return f"Fechamento {self.date.strftime('%d/%m/%Y')}"


class Expense(models.Model):
    """
    Despesa do negócio.

    Registra gastos operacionais categorizados.
    """
    date = models.DateField(
        verbose_name='Data',
        help_text='Data da despesa'
    )
    category = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.PROTECT,
        verbose_name='Categoria',
        related_name='expenses',
        help_text='Categoria da despesa'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Valor',
        help_text='Valor da despesa em reais',
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descrição',
        help_text='Descrição detalhada da despesa (opcional)'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em'
    )

    class Meta:
        verbose_name = 'Despesa'
        verbose_name_plural = 'Despesas'
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['-date']),
            models.Index(fields=['category']),
            models.Index(fields=['-date', 'category']),
        ]

    def clean(self):
        """
        Validações customizadas do modelo.
        """
        super().clean()

        # Validação: valor deve ser positivo (reforço do validator)
        if self.amount and self.amount <= 0:
            raise ValidationError({
                'amount': 'O valor deve ser maior que zero.'
            })

    def save(self, *args, **kwargs):
        """
        Sobrescreve save para executar validações.
        """
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.category.name} - R$ {self.amount} ({self.date.strftime('%d/%m/%Y')})"
