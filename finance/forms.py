"""
Formulários da aplicação finance.
"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from finance.models import Expense, ExpenseCategory, DailyClosing
from decimal import Decimal


class ExpenseForm(forms.ModelForm):
    """
    Formulário para criação e edição de despesas.
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
                'placeholder': 'Descrição opcional da despesa',
            }),
        }
        labels = {
            'date': 'Data',
            'category': 'Categoria',
            'amount': 'Valor (R$)',
            'description': 'Descrição',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar apenas categorias ativas
        self.fields['category'].queryset = ExpenseCategory.objects.filter(active=True)

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


class ExpenseFilterForm(forms.Form):
    """
    Formulário para filtrar despesas por data e categoria.
    """
    date_from = forms.DateField(
        required=False,
        label='Data inicial',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
        })
    )
    date_to = forms.DateField(
        required=False,
        label='Data final',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
        })
    )
    category = forms.ModelChoiceField(
        queryset=ExpenseCategory.objects.filter(active=True),
        required=False,
        label='Categoria',
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        empty_label='Todas as categorias'
    )

    def clean(self):
        """Valida que a data inicial não é maior que a final."""
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')

        if date_from and date_to and date_from > date_to:
            raise ValidationError('A data inicial não pode ser maior que a data final.')

        return cleaned_data


class DailyClosingForm(forms.ModelForm):
    """
    Formulário para criação e edição de fechamento diário.
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
                'placeholder': 'Observações opcionais sobre o dia',
            }),
        }
        labels = {
            'date': 'Data',
            'order_count': 'Quantidade de Pedidos',
            'cash_sales': 'Vendas em Dinheiro (R$)',
            'pix_sales': 'Vendas em Pix (R$)',
            'card_sales': 'Vendas em Cartão (R$)',
            'notes': 'Observações',
        }

    def clean_date(self):
        """Valida que a data não é futura."""
        date = self.cleaned_data.get('date')
        if date and date > timezone.now().date():
            raise ValidationError('A data não pode ser futura.')
        return date

    def clean(self):
        """Validações customizadas do formulário."""
        cleaned_data = super().clean()
        date = cleaned_data.get('date')

        # Valida fechamento duplicado (apenas na criação)
        if date and self.instance.pk is None:
            if DailyClosing.objects.filter(date=date).exists():
                raise ValidationError({
                    'date': f'Já existe um fechamento para {date.strftime("%d/%m/%Y")}.'
                })

        return cleaned_data
