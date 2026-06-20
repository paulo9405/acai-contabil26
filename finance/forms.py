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
