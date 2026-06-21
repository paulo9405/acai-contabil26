# Como Limpar e Recriar Dados de Teste

## Problema
Você está tentando testar o sistema mas já existem dados no banco com as datas que quer usar, causando erros de "fechamento duplicado".

---

## Solução Rápida (3 comandos)

```bash
# 1. Ativar ambiente virtual
source venv/bin/activate

# 2. Limpar TODOS os dados
python manage.py limpar_dados

# 3. (Opcional) Criar novos dados de teste
python criar_dados_teste.py
```

---

## Opção 1: Limpar Tudo e Recomeçar

### Passo 1: Limpar dados existentes

```bash
source venv/bin/activate
python manage.py limpar_dados
```

O comando irá:
- Mostrar quantos registros serão excluídos
- Pedir confirmação (digite "SIM")
- Excluir todos os fechamentos e despesas
- Manter usuários e categorias

### Passo 2: Criar novos dados

Você tem 2 opções:

**A) Criar manualmente via interface**
- Acesse http://localhost:8000
- Use "Novo Fechamento" e "Nova Despesa"
- Controle total sobre as datas

**B) Criar automaticamente com script**
```bash
python criar_dados_teste.py
```
- Cria 30 dias de dados
- Últimos 30 dias a partir de hoje
- Dados realistas e variados

---

## Opção 2: Limpar Apenas um Período

Se quiser manter alguns dados e limpar apenas um período específico:

```bash
source venv/bin/activate
python manage.py shell
```

Depois no shell do Django:

```python
from finance.models import DailyClosing, Expense
from datetime import date

# Definir período a limpar
data_inicio = date(2026, 6, 1)
data_fim = date(2026, 6, 30)

# Excluir fechamentos do período
fechamentos = DailyClosing.objects.filter(date__gte=data_inicio, date__lte=data_fim)
print(f"Excluindo {fechamentos.count()} fechamentos...")
fechamentos.delete()

# Excluir despesas do período
despesas = Expense.objects.filter(date__gte=data_inicio, date__lte=data_fim)
print(f"Excluindo {despesas.count()} despesas...")
despesas.delete()

print("✓ Dados do período excluídos!")
```

Pressione Ctrl+D para sair do shell.

---

## Opção 3: Verificar Dados Existentes

Para ver quais datas já têm fechamentos:

```bash
source venv/bin/activate
python manage.py shell
```

```python
from finance.models import DailyClosing

# Ver todos os fechamentos
fechamentos = DailyClosing.objects.all().order_by('-date')
for f in fechamentos[:10]:  # Últimos 10
    print(f"{f.date} - {f.order_count} pedidos - R$ {f.total_sales}")
```

---

## Comandos Disponíveis

### Limpar TUDO (com confirmação)
```bash
python manage.py limpar_dados
```

### Limpar TUDO (sem confirmação - CUIDADO!)
```bash
python manage.py limpar_dados --confirmar
```

### Ver comandos disponíveis
```bash
python manage.py help
```

---

## Dica: Testar com Datas Específicas

Se você quer testar criação de fechamento para HOJE:

1. **Limpe os dados de hoje** (se existirem):
```bash
python manage.py shell
```

```python
from finance.models import DailyClosing, Expense
from datetime import date

hoje = date.today()
DailyClosing.objects.filter(date=hoje).delete()
Expense.objects.filter(date=hoje).delete()
print(f"✓ Dados de {hoje} excluídos!")
```

2. **Agora crie via interface** sem erros de duplicação

---

## Estrutura de Dados Atual

Após executar `python criar_dados_teste.py`, você terá:

- **Usuário:** admin / admin123
- **Fechamentos:** 30 (últimos 30 dias)
- **Despesas:** ~90 (3 por dia)
- **Categorias:** 10 (criadas via migration)

**Datas dos fechamentos:**
- Do dia `hoje - 29 dias` até `hoje`
- Exemplo: se hoje é 21/06, vai de 23/05 até 21/06

---

## Troubleshooting

### "Já existe um fechamento para [data]"
**Solução:**
```bash
python manage.py limpar_dados
```

### "Quero manter alguns dados"
**Solução:** Use a Opção 2 (limpar apenas período específico)

### "Quero começar do zero"
**Solução:**
```bash
# Limpar tudo
python manage.py limpar_dados

# Recriar do zero
python criar_dados_teste.py
```

---

## Dados Gerados

O script `criar_dados_teste.py` cria:

### Fechamentos:
- **Período:** Últimos 30 dias
- **Variação:** Mais vendas nos fins de semana (1.5x)
- **Pedidos:** 15-37 por dia
- **Vendas:** R$ 450 - R$ 1.170 por dia

### Despesas:
- **Quantidade:** 3 por dia (padrão)
- **Categorias:** Distribuídas entre as 10 categorias ativas
- **Valores:** R$ 20 - R$ 70

### Total Aproximado:
- **Vendas:** ~R$ 15.000
- **Despesas:** ~R$ 4.000
- **Lucro:** ~R$ 11.000

---

## Workflow Recomendado para Testes

```bash
# 1. Limpar tudo
python manage.py limpar_dados

# 2. Criar dados automáticos
python criar_dados_teste.py
# (aceite os padrões: Enter, Enter, Enter)

# 3. Iniciar servidor
python manage.py runserver

# 4. Acessar e testar
# http://localhost:8000
```

Agora você terá:
- ✅ Dashboard com gráficos populados
- ✅ Relatórios com dados dos últimos 30 dias
- ✅ Listas com paginação
- ✅ Nenhum conflito de datas

---

## Para Testar Criação Manual

Se quiser testar a criação manual de fechamentos:

```bash
# 1. Limpar dados
python manage.py limpar_dados

# 2. NÃO executar criar_dados_teste.py

# 3. Iniciar servidor
python manage.py runserver

# 4. Criar manualmente via interface
# Todas as datas estarão livres!
```

---

**Pronto para começar!** Execute os comandos acima e bons testes! 🚀
