# ROADMAP FINAL — GESTÃO FINANCEIRA AÇAÍ DA ROSE

## Visão Geral

Sistema financeiro simples, rápido e mobile-first para pequenos negócios.

O objetivo é permitir que o usuário registre o fechamento diário em menos de 20 segundos e acompanhe a evolução financeira do negócio sem complexidade.

---

# Objetivos do Sistema

Responder rapidamente:

* Quanto vendeu hoje?
* Quanto vendeu este mês?
* Quantos pedidos teve?
* Qual foi o ticket médio?
* Quanto entrou em Pix?
* Quanto entrou em Dinheiro?
* Quanto entrou em Cartão?
* Quanto foi gasto?
* Qual foi o lucro?
* Como está a evolução do negócio?

---

# O que o sistema NÃO será

Nesta primeira versão não haverá:

* Controle de estoque
* Controle de clientes
* Sistema de pedidos
* Delivery
* Integração com WhatsApp
* Controle de produtos
* Controle de colaboradores
* Comissões
* Fluxo de caixa avançado

Tudo isso poderá existir futuramente.

---

# Público-Alvo

Pequenos negócios que fazem fechamento manual.

Exemplos:

* Açaí
* Lanches
* Food trucks
* Marmitas
* Pequenos restaurantes

---

# Tecnologias

## Backend

* Python 3.12
* Django 5

## Banco de Dados

* PostgreSQL

## Frontend

* Bootstrap 5.3

## Gráficos

* Chart.js

## Deploy

* Render

## Arquivos Estáticos

* WhiteNoise

## Servidor

* Gunicorn

---

# Arquitetura

```text
finance/

├── models.py
├── forms.py
├── views.py
├── urls.py
├── services.py
├── selectors.py
├── tests/

templates/

static/
```

---

# Usuários

## V1

Apenas um usuário administrador.

---

# Funcionalidades

## Login

O sistema deve exigir autenticação.

Após login:

Dashboard.

---

# Dashboard

## Cards do Dia

Mostrar:

* Pedidos Hoje
* Vendas Hoje
* Despesas Hoje
* Lucro Hoje
* Ticket Médio Hoje

---

## Cards do Mês

Mostrar:

* Pedidos no Mês
* Vendas do Mês
* Despesas do Mês
* Lucro do Mês
* Ticket Médio do Mês

---

## Gráfico

Últimos 7 dias:

* Vendas
* Despesas
* Lucro

---

## Ações Rápidas

Botões:

* Novo Fechamento
* Nova Despesa
* Relatórios

---

# Módulo: Fechamento Diário

Representa o resumo do dia.

## Campos

### Data

Tipo:

```text
DateField
```

Obrigatório.

Não pode ser futura.

---

### Quantidade de Pedidos

Tipo:

```text
PositiveIntegerField
```

Obrigatório.

Exemplo:

```text
18
```

---

### Venda Dinheiro

Tipo:

```text
DecimalField
```

Obrigatório.

---

### Venda Pix

Tipo:

```text
DecimalField
```

Obrigatório.

---

### Venda Cartão

Tipo:

```text
DecimalField
```

Obrigatório.

---

### Observações

Tipo:

```text
TextField
```

Opcional.

Exemplos:

```text
Jogo do Brasil

Promoção Dia dos Namorados

Dia muito chuvoso

Fechamos mais cedo
```

---

# Regras do Fechamento Diário

## Regra 1

Somente um fechamento por dia.

Exemplo:

```text
20/06/2026 ✅

20/06/2026 novamente ❌
```

---

## Regra 2

Nenhum valor pode ser negativo.

---

## Regra 3

Data futura proibida.

---

## Regra 4

Quantidade de pedidos deve ser maior ou igual a zero.

---

# Módulo: Despesas

Cada despesa é registrada individualmente.

---

## Campos

### Data

Obrigatório.

---

### Categoria

Obrigatório.

---

### Valor

Obrigatório.

---

### Descrição

Opcional.

---

# Categorias Padrão

* Ingredientes
* Embalagens
* Entrega
* Combustível
* Energia
* Internet
* Marketing
* Equipamentos
* Manutenção
* Outros

---

# Exemplo de Despesa

```text
Data:
20/06/2026

Categoria:
Ingredientes

Valor:
R$65

Descrição:
Compra de morangos
```

---

# Cálculos Automáticos

## Total de Vendas

```python
total_vendas = (
    venda_dinheiro +
    venda_pix +
    venda_cartao
)
```

---

## Total de Despesas

```python
sum(despesas)
```

---

## Lucro

```python
lucro =
total_vendas -
total_despesas
```

---

## Ticket Médio

```python
ticket_medio =
total_vendas /
quantidade_pedidos
```

Se pedidos for zero:

```python
ticket_medio = 0
```

---

# Fluxo de Uso

## Durante o Dia

Sempre que houver um gasto:

```text
Nova Despesa

Categoria:
Ingredientes

Valor:
65

Descrição:
Compra de morangos
```

Salvar.

---

## Final do Dia

Clicar:

```text
Novo Fechamento
```

Preencher:

```text
Data:
20/06/2026

Pedidos:
18

Dinheiro:
120

Pix:
350

Cartão:
180

Observações:
Jogo do Brasil
```

Salvar.

---

## Resultado

Sistema calcula automaticamente:

```text
Vendas:
650

Despesas:
65

Lucro:
585

Ticket Médio:
36,11
```

---

# Relatórios

## Filtros

### Período

* Hoje
* Ontem
* Últimos 7 dias
* Últimos 30 dias
* Este mês
* Mês passado
* Personalizado

---

## Categoria

Filtrar despesas por categoria.

---

# Relatórios Disponíveis

## Resumo Financeiro

Mostrar:

* Pedidos
* Vendas
* Despesas
* Lucro
* Ticket Médio

---

## Relatório Diário

Tabela:

```text
Data

Pedidos

Vendas

Despesas

Lucro
```

---

## Relatório de Despesas

Tabela:

```text
Data

Categoria

Valor

Descrição
```

---

# Mobile First (Obrigatório)

O sistema deve ser pensado primeiro para celular.

---

## Resolução Base

```text
390px
```

---

## Layout

Cards empilhados.

Botões grandes.

Pouco texto.

Poucos cliques.

---

## Meta de Usabilidade

O usuário deve conseguir:

* Registrar uma despesa em menos de 10 segundos
* Registrar o fechamento do dia em menos de 20 segundos

---

# Segurança

* Login obrigatório
* CSRF habilitado
* Usuário autenticado para todas as páginas
* Exclusão apenas para administrador

---

# Fase 1

* Criar projeto Django
* Configurar PostgreSQL
* Configurar Bootstrap
* Configurar autenticação

---

# Fase 2

* Criar modelos
* Criar migrations
* Configurar Django Admin

---

# Fase 3

* CRUD de Despesas

---

# Fase 4

* CRUD de Fechamento Diário

---

# Fase 5

* Dashboard

---

# Fase 6

* Relatórios

---

# Fase 7

* Gráficos com Chart.js

---

# Fase 8

* Responsividade Mobile

---

# Fase 9

* Testes

---

# Fase 10

* Deploy no Render

---

# Melhorias Futuras (V2)

* Exportar Excel
* Exportar PDF
* Metas mensais
* Comparativo entre meses
* Fluxo de caixa
* Upload de comprovantes
* Múltiplos usuários
* Multiempresa
* PWA
* Backup automático

