#!/usr/bin/env python
"""
Script para criar dados de teste para a aplicação de Gestão Financeira.
Execute com: python criar_dados_teste.py
"""

import os
import django
from decimal import Decimal
from datetime import timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestao_financeira.settings')
django.setup()

from django.utils import timezone
from django.contrib.auth.models import User
from finance.models import ExpenseCategory, DailyClosing, Expense


def criar_dados_teste():
    """Cria dados de teste para todas as funcionalidades."""

    print("=" * 60)
    print("CRIANDO DADOS DE TESTE")
    print("=" * 60)

    # 1. Criar usuário de teste se não existir
    print("\n1. USUÁRIO DE TESTE")
    print("-" * 60)

    username = input("Nome de usuário (pressione Enter para 'admin'): ").strip() or 'admin'

    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': f'{username}@example.com',
            'is_staff': True,
            'is_superuser': True
        }
    )

    if created:
        password = input("Senha (pressione Enter para 'admin123'): ").strip() or 'admin123'
        user.set_password(password)
        user.save()
        print(f"✓ Usuário '{username}' criado com sucesso!")
        print(f"  - Login: {username}")
        print(f"  - Senha: {password}")
    else:
        print(f"✓ Usuário '{username}' já existe")

    # 2. Verificar categorias
    print("\n2. CATEGORIAS DE DESPESAS")
    print("-" * 60)

    categoria_count = ExpenseCategory.objects.count()
    print(f"✓ {categoria_count} categorias cadastradas")

    if categoria_count < 5:
        print("  AVISO: Poucas categorias. Execute as migrations para criar as padrão.")

    # 3. Criar fechamentos diários
    print("\n3. FECHAMENTOS DIÁRIOS")
    print("-" * 60)

    dias_input = input("Quantos dias de fechamentos criar? (padrão: 30): ").strip()
    dias = int(dias_input) if dias_input.isdigit() else 30

    hoje = timezone.now().date()
    inicio = hoje - timedelta(days=dias-1)

    # Limpar fechamentos existentes no período (opcional)
    limpar = input("Limpar fechamentos existentes neste período? (s/N): ").strip().lower()
    if limpar == 's':
        DailyClosing.objects.filter(date__gte=inicio, date__lte=hoje).delete()
        print("  ✓ Fechamentos antigos removidos")

    criados = 0
    pulados = 0

    for i in range(dias):
        data = inicio + timedelta(days=i)

        # Verificar se já existe
        if DailyClosing.objects.filter(date=data).exists():
            pulados += 1
            continue

        # Simular variação de vendas (mais vendas nos fins de semana)
        multiplicador = 1.5 if data.weekday() in [5, 6] else 1.0
        base_pedidos = 15

        pedidos = int((base_pedidos + (i % 10)) * multiplicador)
        dinheiro = Decimal(str((100 + (i * 10)) * multiplicador))
        pix = Decimal(str((150 + (i * 15)) * multiplicador))
        cartao = Decimal(str((200 + (i * 20)) * multiplicador))

        DailyClosing.objects.create(
            date=data,
            order_count=pedidos,
            cash_sales=dinheiro,
            pix_sales=pix,
            card_sales=cartao,
            notes=f"Fechamento de teste - {data.strftime('%A')}"
        )
        criados += 1

    print(f"✓ {criados} fechamentos criados")
    print(f"  {pulados} já existiam (pulados)")

    # 4. Criar despesas
    print("\n4. DESPESAS")
    print("-" * 60)

    categorias = list(ExpenseCategory.objects.filter(active=True))

    if not categorias:
        print("✗ ERRO: Nenhuma categoria ativa encontrada!")
        print("  Execute as migrations primeiro.")
        return

    despesas_por_dia = input("Quantas despesas por dia? (padrão: 3): ").strip()
    despesas_por_dia = int(despesas_por_dia) if despesas_por_dia.isdigit() else 3

    # Limpar despesas existentes (opcional)
    limpar = input("Limpar despesas existentes neste período? (s/N): ").strip().lower()
    if limpar == 's':
        Expense.objects.filter(date__gte=inicio, date__lte=hoje).delete()
        print("  ✓ Despesas antigas removidas")

    criadas = 0

    for i in range(dias):
        data = inicio + timedelta(days=i)

        for j in range(despesas_por_dia):
            # Selecionar categoria aleatoriamente (usando índice)
            categoria = categorias[j % len(categorias)]

            # Valor variável
            valor = Decimal(str(20 + (j * 15) + (i % 20)))

            Expense.objects.create(
                date=data,
                category=categoria,
                amount=valor,
                description=f"Despesa de teste - {categoria.name} - Dia {i+1}"
            )
            criadas += 1

    print(f"✓ {criadas} despesas criadas")

    # 5. Resumo final
    print("\n" + "=" * 60)
    print("RESUMO FINAL")
    print("=" * 60)
    print(f"✓ Usuários: {User.objects.count()}")
    print(f"✓ Categorias: {ExpenseCategory.objects.filter(active=True).count()}")
    print(f"✓ Fechamentos: {DailyClosing.objects.count()}")
    print(f"✓ Despesas: {Expense.objects.count()}")

    # Cálculos de exemplo
    total_vendas = sum(c.total_sales for c in DailyClosing.objects.all())
    total_despesas = sum(e.amount for e in Expense.objects.all())
    lucro = total_vendas - total_despesas

    print(f"\n💰 FINANCEIRO TOTAL:")
    print(f"   Vendas: R$ {total_vendas:,.2f}")
    print(f"   Despesas: R$ {total_despesas:,.2f}")
    print(f"   Lucro: R$ {lucro:,.2f}")

    print("\n" + "=" * 60)
    print("DADOS DE TESTE CRIADOS COM SUCESSO!")
    print("=" * 60)
    print("\nAgora você pode:")
    print("1. Iniciar o servidor: python manage.py runserver")
    print("2. Acessar: http://localhost:8000")
    print(f"3. Fazer login com: {username} / {password if created else '(senha existente)'}")
    print("\n")


if __name__ == '__main__':
    try:
        criar_dados_teste()
    except KeyboardInterrupt:
        print("\n\nOperação cancelada pelo usuário.")
    except Exception as e:
        print(f"\n✗ ERRO: {e}")
        import traceback
        traceback.print_exc()
