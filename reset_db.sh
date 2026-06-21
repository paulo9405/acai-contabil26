#!/bin/bash
# Script para resetar banco de dados e recriar dados de teste

echo "================================================"
echo "RESET DO BANCO DE DADOS"
echo "================================================"
echo ""

# Ativar ambiente virtual
source venv/bin/activate

echo "1️⃣  Limpando dados existentes..."
echo ""
python manage.py limpar_dados --confirmar

echo ""
echo "2️⃣  Criando novos dados de teste..."
echo ""

# Criar dados automaticamente (30 dias, 3 despesas/dia)
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestao_financeira.settings')
django.setup()

from django.utils import timezone
from django.contrib.auth.models import User
from finance.models import ExpenseCategory, DailyClosing, Expense
from decimal import Decimal
from datetime import timedelta

print('📝 Criando usuário admin...')
user, created = User.objects.get_or_create(
    username='admin',
    defaults={'email': 'admin@example.com', 'is_staff': True, 'is_superuser': True}
)
if created:
    user.set_password('admin123')
    user.save()
    print('✓ Usuário admin criado: admin / admin123')
else:
    print('✓ Usuário admin já existe')

print('')
print('📅 Criando 30 dias de fechamentos...')
hoje = timezone.now().date()
inicio = hoje - timedelta(days=29)

for i in range(30):
    data = inicio + timedelta(days=i)
    multiplicador = 1.5 if data.weekday() in [5, 6] else 1.0

    pedidos = int((15 + (i % 10)) * multiplicador)
    dinheiro = Decimal(str((100 + (i * 10)) * multiplicador))
    pix = Decimal(str((150 + (i * 15)) * multiplicador))
    cartao = Decimal(str((200 + (i * 20)) * multiplicador))

    DailyClosing.objects.create(
        date=data,
        order_count=pedidos,
        cash_sales=dinheiro,
        pix_sales=pix,
        card_sales=cartao,
        notes=f'Fechamento de teste - {data.strftime(\"%A\")}'
    )

print(f'✓ {DailyClosing.objects.count()} fechamentos criados')

print('')
print('💰 Criando despesas...')
categorias = list(ExpenseCategory.objects.filter(active=True))

for i in range(30):
    data = inicio + timedelta(days=i)
    for j in range(3):
        categoria = categorias[j % len(categorias)]
        valor = Decimal(str(20 + (j * 15) + (i % 20)))

        Expense.objects.create(
            date=data,
            category=categoria,
            amount=valor,
            description=f'Despesa de teste - {categoria.name}'
        )

print(f'✓ {Expense.objects.count()} despesas criadas')

# Calcular resumo
total_vendas = sum(c.total_sales for c in DailyClosing.objects.all())
total_despesas = sum(e.amount for e in Expense.objects.all())
lucro = total_vendas - total_despesas

print('')
print('=' * 50)
print('RESUMO FINANCEIRO:')
print('=' * 50)
print(f'💰 Vendas:   R\$ {total_vendas:,.2f}')
print(f'💸 Despesas: R\$ {total_despesas:,.2f}')
print(f'📈 Lucro:    R\$ {lucro:,.2f}')
print('=' * 50)
"

echo ""
echo "================================================"
echo "✅ BANCO RESETADO COM SUCESSO!"
echo "================================================"
echo ""
echo "Dados criados:"
echo "  - Usuário: admin / admin123"
echo "  - 30 fechamentos (últimos 30 dias)"
echo "  - 90 despesas (3 por dia)"
echo ""
echo "Iniciar servidor:"
echo "  python manage.py runserver"
echo ""
echo "Acessar:"
echo "  http://localhost:8000"
echo ""
