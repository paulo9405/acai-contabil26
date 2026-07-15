---

# FASE 1 — Setup Inicial do Projeto

Você é um desenvolvedor Django Senior especialista em arquitetura limpa, Django 5, Bootstrap 5 e PostgreSQL.

Crie a estrutura inicial de um projeto chamado "gestao_financeira".

Tecnologias:

* Python 3.12
* Django 5
* PostgreSQL
* Bootstrap 5.3
* WhiteNoise
* Gunicorn

Requisitos:

* Ambiente preparado para desenvolvimento local
* Ambiente preparado para deploy futuro no Render
* Configuração de arquivos estáticos
* Configuração de templates
* Configuração de timezone Brasil
* Configuração de autenticação Django
* Estrutura de diretórios organizada

Arquitetura:

finance/
├── models.py
├── forms.py
├── views.py
├── urls.py
├── services.py
├── selectors.py
├── tests/

Explique cada decisão tomada.

Não implemente funcionalidades ainda.
Apenas a estrutura inicial.

---

# FASE 2 — Modelagem do Banco

Analise o contexto abaixo e implemente apenas os modelos Django.

Sistema de gestão financeira para pequenos negócios.

Criar os modelos:

1. DailyClosing

Campos:

* date
* order_count
* cash_sales
* pix_sales
* card_sales
* notes
* created_at
* updated_at

Regras:

* Apenas um fechamento por dia
* Data não pode ser futura
* Valores não podem ser negativos

2. ExpenseCategory

Campos:

* name
* active

Categorias iniciais:

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

3. Expense

Campos:

* date
* category
* amount
* description
* created_at
* updated_at

Crie:

* models.py completo
* validações
* Meta classes
* métodos auxiliares
* propriedades calculadas

Não criar views ainda.

---

# FASE 3 — Services e Regras de Negócio

Implemente a camada services.py.

Criar funções para:

* calcular total de vendas
* calcular total de despesas
* calcular lucro
* calcular ticket médio
* calcular métricas do dashboard

Seguir boas práticas Django.

As views não devem conter cálculos.

Toda regra de negócio deve ficar em services.py.

Mostrar código completo.

---

# FASE 4 — CRUD de Despesas

Implemente o módulo completo de despesas.

Criar:

* Forms
* Views CBV
* URLs
* Templates Bootstrap 5

Funcionalidades:

* listar despesas
* criar despesa
* editar despesa
* excluir despesa

Requisitos:

* mobile first
* Bootstrap 5
* mensagens de sucesso
* paginação
* filtros por data
* filtros por categoria

Utilizar LoginRequiredMixin.

Mostrar todos os arquivos necessários.

---

# FASE 5 — CRUD de Fechamento Diário

Implemente o módulo completo de fechamento diário.

Campos:

* Data
* Quantidade de pedidos

* Venda dinheiro
* Venda pix
* Venda cartão
* Observações

Criar:

* Forms
* Views
* URLs
* Templates Bootstrap 5

Regras:

* Apenas um fechamento por dia
* Data não pode ser futura

Mobile first.

Utilizar CBVs.

Mostrar todos os arquivos.

---

# FASE 6 — Dashboard

Crie o dashboard principal do sistema.

Exibir:

Hoje:

* Pedidos
* Vendas
* Despesas
* Lucro
* Ticket médio

Mês:

* Pedidos
* Vendas
* Despesas
* Lucro
* Ticket médio

Últimos 7 dias:

* vendas
* despesas
* lucro

Utilizar:

* services.py
* Bootstrap 5
* Cards responsivos

Dashboard otimizado para celular.

Não utilizar JavaScript complexo.

---

# FASE 7 — Relatórios

Implemente módulo de relatórios.

Filtros:

* Hoje
* Ontem
* Últimos 7 dias
* Últimos 30 dias
* Este mês
* Mês passado
* Personalizado

Exibir:

* Total de pedidos
* Total vendido
* Total de despesas
* Lucro
* Ticket médio

Criar:

* View
* Form
* Template

Bootstrap 5.

Mobile first.

Mostrar implementação completa.

---

# FASE 8 — Gráficos

Adicionar gráficos Chart.js ao dashboard.

Gráficos:

1. Vendas últimos 7 dias

2. Despesas últimos 7 dias

3. Lucro últimos 7 dias

Requisitos:

* responsivo
* mobile first
* carregar rapidamente
* gerar dados via Django View

Mostrar implementação completa.

---

# FASE 9 — Responsividade e UX

Faça uma revisão completa da interface.

Objetivos:

* uso confortável em celular
* mínimo de cliques
* botões grandes
* formulários simples
* boa acessibilidade

Revisar:

* templates
* navbar
* cards
* formulários
* tabelas

Sugerir melhorias e gerar código atualizado.

---

# FASE 10 — Testes

Crie testes automatizados para o sistema.

Cobrir:

* models
* forms
* services
* views

Utilizar:

* pytest
* pytest-django

Cobertura mínima:

80%

Mostrar estrutura completa dos testes.

---

# FASE 11 — Deploy Render

Prepare o projeto para produção no Render.

Gerar:

* settings produção
* Procfile
* requirements.txt
* variáveis de ambiente
* PostgreSQL
* WhiteNoise
* Gunicorn

Aplicar boas práticas de segurança.

Explicar passo a passo do deploy.

Minha sugestão: após a Fase 2, peça também para o Claude gerar um `PROJECT_RULES.md` com os padrões do projeto (CBV, services.py, Bootstrap, nomenclaturas, etc.). Isso evita que ele comece a mudar o estilo da arquitetura nas próximas fases.

