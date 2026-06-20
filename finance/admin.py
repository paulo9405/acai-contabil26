from django.contrib import admin
from finance.models import ExpenseCategory, DailyClosing, Expense


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    """
    Admin para gerenciamento de categorias de despesas.
    """
    list_display = ('name', 'active', 'expense_count')
    list_filter = ('active',)
    search_fields = ('name',)
    ordering = ('name',)

    def expense_count(self, obj):
        """Exibe a quantidade de despesas na categoria."""
        return obj.expenses.count()
    expense_count.short_description = 'Qtd. Despesas'


@admin.register(DailyClosing)
class DailyClosingAdmin(admin.ModelAdmin):
    """
    Admin para gerenciamento de fechamentos diários.
    """
    list_display = (
        'date',
        'order_count',
        'display_total_sales',
        'display_cash_sales',
        'display_pix_sales',
        'display_card_sales',
        'display_average_ticket',
        'created_at'
    )
    list_filter = ('date',)
    search_fields = ('notes',)
    date_hierarchy = 'date'
    ordering = ('-date',)
    readonly_fields = ('created_at', 'updated_at', 'display_total_sales', 'display_average_ticket')

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('date', 'order_count', 'notes')
        }),
        ('Vendas', {
            'fields': ('cash_sales', 'pix_sales', 'card_sales')
        }),
        ('Calculados', {
            'fields': ('display_total_sales', 'display_average_ticket'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def display_total_sales(self, obj):
        """Exibe o total de vendas formatado."""
        return f"R$ {obj.total_sales:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')
    display_total_sales.short_description = 'Total de Vendas'

    def display_average_ticket(self, obj):
        """Exibe o ticket médio formatado."""
        return f"R$ {obj.average_ticket:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')
    display_average_ticket.short_description = 'Ticket Médio'

    def display_cash_sales(self, obj):
        """Exibe vendas em dinheiro formatadas."""
        return f"R$ {obj.cash_sales:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')
    display_cash_sales.short_description = 'Dinheiro'

    def display_pix_sales(self, obj):
        """Exibe vendas em Pix formatadas."""
        return f"R$ {obj.pix_sales:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')
    display_pix_sales.short_description = 'Pix'

    def display_card_sales(self, obj):
        """Exibe vendas em cartão formatadas."""
        return f"R$ {obj.card_sales:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')
    display_card_sales.short_description = 'Cartão'


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    """
    Admin para gerenciamento de despesas.
    """
    list_display = (
        'date',
        'category',
        'display_amount',
        'description_preview',
        'created_at'
    )
    list_filter = ('date', 'category')
    search_fields = ('description',)
    date_hierarchy = 'date'
    ordering = ('-date', '-created_at')
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ['category']

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('date', 'category', 'amount')
        }),
        ('Detalhes', {
            'fields': ('description',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def display_amount(self, obj):
        """Exibe o valor formatado."""
        return f"R$ {obj.amount:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')
    display_amount.short_description = 'Valor'

    def description_preview(self, obj):
        """Exibe prévia da descrição."""
        if obj.description:
            return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
        return '-'
    description_preview.short_description = 'Descrição'
