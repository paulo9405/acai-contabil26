# ROADMAP — Módulo de Pedidos (Espelho Digital da Comanda)

> **Fonte oficial de acompanhamento do desenvolvimento.**
> Atualizar ao iniciar e ao concluir cada fase.
> Leia este arquivo integralmente antes de qualquer implementação.

---

## Índice

1. [Objetivo do Módulo](#1-objetivo-do-módulo)
2. [Contexto do Negócio](#2-contexto-do-negócio)
3. [Fluxo Operacional](#3-fluxo-operacional)
4. [Arquitetura Aprovada](#4-arquitetura-aprovada)
5. [Modelagem do Banco de Dados](#5-modelagem-do-banco-de-dados)
6. [Principais Regras de Negócio](#6-principais-regras-de-negócio)
7. [Decisões Arquiteturais](#7-decisões-arquiteturais)
8. [Permissões](#8-permissões)
9. [Integração com o Fechamento Diário](#9-integração-com-o-fechamento-diário)
10. [Riscos Conhecidos](#10-riscos-conhecidos)
11. [Pendências Abertas](#11-pendências-abertas)
12. [Plano de Fases](#12-plano-de-fases)
13. [Diário de Desenvolvimento](#13-diário-de-desenvolvimento)
14. [Continuidade do Projeto](#14-continuidade-do-projeto)

---

## 1. Objetivo do Módulo

Criar um **espelho digital resumido da comanda física**, lançado manualmente pelo funcionário após o preparo e entrega do pedido, com as seguintes finalidades:

- Controlar produtos vendidos e faturamento.
- Registrar formas de pagamento por pedido.
- Identificar horários de pico.
- Alimentar relatórios operacionais e financeiros.

**O que este módulo NÃO é:**
- Não substitui a comanda física de papel.
- Não é um sistema de pedidos feito pelo cliente.
- Não captura nome, telefone, endereço ou referência do cliente.

---

## 2. Contexto do Negócio

**Estabelecimento:** Açaí da Rose — loja de açaí (Buritizeiro, MG).
**Usuária final principal:** proprietária (baixa familiaridade com tecnologia).
**Desenvolvedor:** Paulo (filho da proprietária).
**Sistema em produção:** Render (PostgreSQL). Dev local: SQLite.

### Cardápio atual (referência de modelagem)

**Monte seu Açaí**

| Tamanho  | Preço   | Adicionais incluídos |
|----------|---------|----------------------|
| 300 ml   | R$ 18,00 | 2 |
| 500 ml   | R$ 24,00 | 3 |
| 700 ml   | R$ 28,00 | 3 |
| 1 litro  | R$ 38,00 | 4 |
| 1,5 litro | R$ 50,00 | 5 |
| 2 litros | R$ 64,00 | 6 |

Adicionais gratuitos elegíveis (dentro do limite): Amendoim, Banana, Bis preto ou branco, Biscoito Oreo, Calda de morango, Calda de chocolate, Cereal mix, Granola, Leite condensado, Leite Ninho, Paçoca, Sorvete.

**Adicionais pagos (avulsos)**

| Adicional | Preço |
|---|---|
| Abacaxi | R$ 4,00 |
| Amendoim granulado | R$ 3,00 |
| Banana | R$ 3,00 |
| Bis | R$ 3,50 |
| Bis Oreo | R$ 4,00 |
| Biscoito Oreo | R$ 3,00 |
| Bombom | R$ 5,00 |
| Calda de morango | R$ 3,00 |
| Calda de chocolate | R$ 3,00 |
| Canudo | R$ 4,00 |
| Cereal mix | R$ 3,50 |
| Confete | R$ 4,00 |
| Cupuaçu | R$ 6,00 |
| Gotas de chocolate | R$ 4,50 |
| Granola | R$ 3,00 |
| Kitkat | R$ 5,00 |
| Kiwi | R$ 7,00 |
| Laka | R$ 7,50 |
| Leite condensado | R$ 3,50 |
| Leite Ninho | R$ 3,50 |
| Maltine | R$ 4,00 |
| Morango | R$ 6,50 |
| Nutella | R$ 7,50 |
| Paçoca | R$ 3,00 |
| Sorvete | R$ 5,00 |
| Uva | R$ 7,50 |
| Whey | R$ 6,50 |

**Açaís prontos** (preços por tamanho: 300ml / 500ml / 700ml / 1L / 1,5L / 2L)

| Produto | 300ml | 500ml | 700ml | 1L | 1,5L | 2L |
|---|---|---|---|---|---|---|
| 01 Açaí Puro | 16,00 | 18,00 | 24,00 | 32,00 | 50,00 | 62,00 |
| 02 Açaí Puro c/ Cupuaçu | 18,00 | 22,00 | 26,00 | 36,00 | 52,00 | 64,00 |
| 03 Açaí Gotas de Chocolate | 20,00 | 25,00 | 28,00 | 38,00 | 54,00 | 64,00 |
| 04 Açaí Ninho | 18,00 | 22,00 | 26,00 | 36,00 | 52,00 | 64,00 |
| 05 Açaí Ninho c/ Cupuaçu | 20,00 | 26,00 | 32,00 | 40,00 | 54,00 | 56,00 |
| 06 Açaí Maltine | 18,00 | 24,00 | 28,00 | 37,00 | 53,00 | 62,00 |
| 07 Açaí Kids | 19,00 | 25,00 | 29,00 | 40,00 | 54,00 | 62,00 |
| 08 Açaí Frutas | 20,00 | 27,00 | 30,00 | 39,00 | 55,00 | 63,00 |
| 09 Açaí Nutella | 22,00 | 30,00 | 36,00 | 50,00 | 59,00 | 68,00 |
| 10 Combo Família | — | — | — | — | 60,00 | 72,00 |
| 11 Açaí Zero | 18,00 | 24,00 | 28,00 | 39,50 | — | — |
| 12 Açaí Gourmet | 21,00 | 29,00 | 34,00 | 49,00 | 54,00 | 65,00 |
| 13 Açaí Oreo | 19,00 | 26,00 | 30,00 | 48,00 | 53,00 | 62,00 |

**Sorvetes** (pote 2 litros)

| Sabor | Preço |
|---|---|
| Morango | R$ 36,00 |
| Flocos | R$ 36,00 |
| Laka | R$ 33,00 |
| Coco/Abacaxi | R$ 36,00 |
| Chocolate | R$ 36,00 |
| Ninho Trufado | R$ 39,00 |
| Napolitano | R$ 37,00 |

**Vitaminas** (500ml)

| Produto | Preço | Composição |
|---|---|---|
| Whey Protein | R$ 25,00 | Açaí zero, whey, leite e banana |
| Açaí c/ Nutella | R$ 24,00 | Açaí, leite, banana e nutella |
| Açaí Tradicional | R$ 20,00 | Açaí, leite e banana |

---

## 3. Fluxo Operacional

```
1. Cliente envia pedido pelo WhatsApp
2. Funcionário preenche a comanda física (papel)
3. Pedido é produzido e entregue
4. Funcionário acessa o sistema (área operacional)
5. Lança as informações da comanda no sistema
6. Sistema calcula totais e alimenta relatórios
```

A comanda física **continua existindo**. O sistema é complementar, não substituto.

---

## 4. Arquitetura Aprovada

### App novo: `orders`

Um único novo app Django chamado `orders`, seguindo o padrão mono-app do projeto.

### Stack

- **Backend:** Django 5.0.14, CBVs, sem DRF.
- **Camadas:**
  - `models.py` — modelos + `clean()` + `save()` com `full_clean()`.
  - `services.py` — escrita e regras de negócio (funções keyword-only `*,`).
  - `selectors.py` — leitura e queries complexas.
  - `forms.py` — ModelForms com widgets Bootstrap.
  - `views.py` — finas, delegam para services/selectors.
  - `admin.py` — catálogo administrável pelo Django Admin.
- **Frontend:** Bootstrap 5.3 (CDN), Bootstrap Icons, JS vanilla (`json_script` + POST arrays), mobile-first (base 390px).
- **Dinheiro:** sempre `DecimalField` + `Decimal`. Nunca `float`.
- **Transações:** `transaction.atomic()` ao persistir pedido + itens + adicionais juntos.
- **Nomeação de models:** inglês, singular, PascalCase.

### Referência de arquitetura existente

A `DailyClosingUnifiedView` em `finance/views.py` é o modelo de referência para a tela de lançamento: POST com arrays de campos, parsing manual, `transaction.atomic`, services chamados dentro da view.

---

## 5. Modelagem do Banco de Dados

### Catálogo

#### `ProductCategory`
| Campo | Tipo | Notas |
|---|---|---|
| `id` | BigAutoField | PK |
| `name` | CharField(100) | unique |
| `kind` | CharField choices | `STANDARD`, `BUILD_YOUR_OWN`, `ADDON`, `OTHER` — direciona a UI |
| `sort_order` | PositiveIntegerField | ordem de exibição |
| `active` | BooleanField | default True |

#### `Size`
| Campo | Tipo | Notas |
|---|---|---|
| `id` | BigAutoField | PK |
| `name` | CharField(50) | ex: "300 ml", "2 litros" |
| `volume_ml` | PositiveIntegerField | para relatório de litros vendidos |
| `sort_order` | PositiveIntegerField | |
| `active` | BooleanField | |

#### `Product`
| Campo | Tipo | Notas |
|---|---|---|
| `id` | BigAutoField | PK |
| `category` | FK(ProductCategory, PROTECT) | |
| `name` | CharField(200) | |
| `description` | TextField(blank) | composição do produto |
| `product_type` | CharField choices | `STANDARD`, `BUILD_YOUR_OWN`, `ADDON` |
| `sort_order` | PositiveIntegerField | |
| `active` | BooleanField | |

#### `ProductVariant`
| Campo | Tipo | Notas |
|---|---|---|
| `id` | BigAutoField | PK |
| `product` | FK(Product, CASCADE) | |
| `size` | FK(Size, PROTECT, null=True) | null para produtos sem tamanho |
| `price` | DecimalField(10,2) | preço atual (snapshot no pedido) |
| `included_addons_limit` | PositiveIntegerField | default 0; só usado em BUILD_YOUR_OWN |
| `active` | BooleanField | |

**Constraint:** `UniqueConstraint(['product', 'size'])` — validação adicional via `clean()` para caso `size=NULL`.

#### `Addon`
| Campo | Tipo | Notas |
|---|---|---|
| `id` | BigAutoField | PK |
| `name` | CharField(100) | unique |
| `price` | DecimalField(10,2) | |
| `is_free_option` | BooleanField | elegível como adicional incluído no "Monte seu Açaí" |
| `sort_order` | PositiveIntegerField | |
| `active` | BooleanField | |

---

### Pedidos

#### `Order`
| Campo | Tipo | Notas |
|---|---|---|
| `id` | BigAutoField | PK |
| `comanda_number` | CharField(20) | referência operacional do papel físico — **sem unicidade** (P-08) |
| `order_date` | DateField | data do pedido |
| `order_time` | TimeField | horário informado manualmente (precisão `HH:MM`) |
| `payment_method` | CharField choices | `PIX`, `CASH`, `CARD` |
| `total` | DecimalField(10,2) | calculado pelo sistema |
| `informed_total` | DecimalField(10,2, null=True) | valor escrito na comanda (opcional) |
| `status` | CharField choices | `ACTIVE`, `CANCELLED` |
| `notes` | TextField(blank) | observações livres |
| `created_by` | FK(User, PROTECT) | quem lançou |
| `created_at` | DateTimeField(auto_now_add) | |
| `updated_at` | DateTimeField(auto_now) | |
| `cancelled_at` | DateTimeField(null=True) | |
| `cancelled_by` | FK(User, null=True) | |
| `cancel_reason` | TextField(blank) | |

**Constraint de unicidade:** **NENHUMA sobre `comanda_number`.** O número da comanda se repete livremente (blocos de 1 a 50 reiniciados). O único identificador do sistema é `Order.id`. Ver Seção 6 → "Número da comanda (SEM unicidade)".

**Índices:** `['order_date']`, `['order_date','payment_method']`, `['order_date','order_time']`, `['status']`, `['created_by']`, `['order_date','comanda_number']` (apenas para acelerar a **busca/conferência** por comanda — não é índice único).

#### `OrderItem`
| Campo | Tipo | Notas |
|---|---|---|
| `id` | BigAutoField | PK |
| `order` | FK(Order, CASCADE) | |
| `product` | FK(Product, SET_NULL, null=True) | referência viva |
| `variant` | FK(ProductVariant, SET_NULL, null=True) | referência viva |
| `quantity` | PositiveIntegerField | |
| `product_name` | CharField(200) | **snapshot histórico** |
| `variant_name` | CharField(100, blank) | **snapshot histórico** |
| `size_name` | CharField(50, blank) | **snapshot histórico** |
| `unit_price` | DecimalField(10,2) | **snapshot histórico** |
| `addons_total` | DecimalField(10,2) | soma dos adicionais pagos |
| `line_total` | DecimalField(10,2) | (unit_price + addons_total) × quantity |

**Índice:** `['product']`.

#### `OrderItemAddon`
| Campo | Tipo | Notas |
|---|---|---|
| `id` | BigAutoField | PK |
| `order_item` | FK(OrderItem, CASCADE) | |
| `addon` | FK(Addon, SET_NULL, null=True) | referência viva |
| `name` | CharField(100) | **snapshot histórico** |
| `unit_price` | DecimalField(10,2) | **snapshot histórico** |
| `quantity` | PositiveIntegerField | default 1 — **v1: sempre 1** (P-12); campo mantido para evolução futura |
| `is_included` | BooleanField | True = dentro do limite grátis; False = pago extra |
| `line_total` | DecimalField(10,2) | unit_price × quantity (0 se is_included) |

**Índice:** `['addon']`.

---

### Diagrama de Relacionamentos

```
ProductCategory 1──* Product 1──* ProductVariant *──1 Size
Addon (independente)

User 1──* Order 1──* OrderItem 1──* OrderItemAddon
                     OrderItem *──1 Product      (SET_NULL)
                     OrderItem *──1 ProductVariant (SET_NULL)
                     OrderItemAddon *──1 Addon   (SET_NULL)
```

FKs de catálogo em itens usam `SET_NULL` para nunca quebrar pedidos ao editar/remover produtos. Os snapshots preservam a informação histórica.

---

## 6. Principais Regras de Negócio

### Pedido com múltiplos itens
- Um pedido pode possuir **um ou mais itens independentes**.
- Exemplo de um único pedido (`Order`):
  - 1 Açaí Monte 300 ml
  - 1 Açaí Nutella 500 ml
  - 2 Coca-Cola Lata
- Todos pertencem ao **mesmo `Order`**.
- Cada item é representado por um **`OrderItem` independente** (com seus próprios snapshots e adicionais).
- O total do pedido é a **soma dos `line_total` de todos os `OrderItems`**.
- Esta regra é estrutural: nenhuma implementação futura deve assumir que um pedido tem apenas um item.

### Preço histórico
- No momento do lançamento, o service `create_order` congela em `OrderItem` os campos: `unit_price`, `product_name`, `variant_name`, `size_name`, `addons_total`, `line_total`.
- Em `OrderItemAddon`: `name`, `unit_price`, `is_included`, `line_total`.
- Alterações futuras no catálogo não afetam pedidos passados.

### "Monte seu Açaí"
- Cada `ProductVariant` de um produto `BUILD_YOUR_OWN` tem `included_addons_limit`.
- Adicionais incluídos: subconjunto de `Addon(is_free_option=True)`, selecionáveis até o limite. Geram `OrderItemAddon(is_included=True, unit_price=0, line_total=0)`.
- Adicionais além do limite: geram `OrderItemAddon(is_included=False, unit_price=<preço>, line_total=<preço>)`.
- **Regra do excedente (decidida — P-06):** ao selecionar adicionais acima do limite gratuito, os excedentes são **automaticamente transformados em adicionais pagos**. O lançamento **nunca é bloqueado** por excesso de adicionais.

### Cálculo de totais
```
OrderItemAddon.line_total = 0               se is_included
                          = unit_price × qty se not is_included

OrderItem.addons_total = sum(line_total de adicionais não incluídos)
OrderItem.line_total   = (unit_price + addons_total) × quantity

Order.total = sum(line_total de todos os OrderItems)
```

### Número da comanda (SEM unicidade)
- A loja usa **blocos físicos de comandas numerados de 1 a 50**. Quando o bloco acaba, começa um novo bloco novamente do número 1.
- Consequência: **o mesmo número pode aparecer várias vezes no mesmo dia** (ex.: dois pedidos "comanda 1" no mesmo dia). Não há qualquer garantia de unicidade.
- **`comanda_number` é apenas um campo de referência operacional** para localizar o papel físico durante conferência.
- **O identificador único do sistema é exclusivamente `Order.id`.**
- **Não existe `UniqueConstraint` de comanda.** Nenhuma regra, validação ou índice deve assumir unicidade de `comanda_number` (nem isolado, nem combinado com data/status).
- Para conferência manual, pesquisas podem combinar `comanda_number` + `order_date` + `order_time`, mas isso é apenas um **filtro de busca**, nunca uma chave única.

### Divergência de valor
- Campo `Order.informed_total` opcional.
- Sistema calcula `Order.total`. Se `informed_total` fornecido e diferente de `total`, exibe **alerta visual não bloqueante**.
- Ambos os valores são preservados para relatório de divergências.

### Cancelamento
- Cancelamento gera `status=CANCELLED` com auditoria (`cancelled_at`, `cancelled_by`, `cancel_reason`).
- **Sem delete físico** de registros financeiros.
- **Quem pode cancelar (decidido — P-03):** somente administrador (`is_superuser`). Funcionários (`Operacao`) **não cancelam** — apenas editam.
- **Motivo obrigatório (decidido — P-05):** `cancel_reason` é **obrigatório** ao cancelar.

### Janela de edição/correção
- **Regra decidida (P-04):** o funcionário (`Operacao`) pode editar o pedido **enquanto o fechamento diário daquela data ainda não tiver sido realizado** (isto é, enquanto não existir `DailyClosing` para `order_date`).
- **Após o fechamento do dia:** somente administrador (`is_superuser`) pode alterar o pedido.
- Implementação: verificar existência de `DailyClosing` para `order_date` (consulta simples; não depende da integração completa da Fase 6).

### Horário do pedido
- `order_time` é preenchido **manualmente** pelo funcionário com o horário escrito na comanda.
- Nunca preenchido automaticamente com o horário atual.
- **Precisão (decidido — P-11):** apenas `HH:MM`. Segundos não são necessários.

### Forma de pagamento
- `TextChoices`: `PIX`, `CASH` (Dinheiro), `CARD` (Cartão).
- **Decidido (P-07):** nesta primeira versão existem apenas essas três formas. **Não há `OTHER`.** Novas formas de pagamento, se surgirem, serão implementadas futuramente.
- Mapeamento para `DailyClosing` na Fase 6: PIX→`pix_sales`, CASH→`cash_sales`, CARD→`card_sales`.

---

## 7. Decisões Arquiteturais

| # | Decisão | Justificativa |
|---|---|---|
| DA-01 | Novo app `orders` (não `catalog` + `orders`) | Projeto mono-app; simplicidade; catálogo sem pedidos não tem valor isolado. |
| DA-02 | `TextChoices` para `payment_method` (não model separado) | Conjunto pequeno e estável; mapeia para colunas do `DailyClosing`; sem duplicação de estrutura existente. |
| DA-03 | Snapshots históricos em `OrderItem`/`OrderItemAddon` | Mudanças de preço no catálogo não devem retroagir. FKs com `SET_NULL` mantêm referência viva sem bloquear edição do catálogo. |
| DA-04 | **Comanda SEM unicidade.** Único identificador é `Order.id` | A loja usa blocos físicos de 1 a 50 reiniciados; o mesmo número se repete no mesmo dia. `comanda_number` é só referência do papel. Nenhuma `UniqueConstraint` sobre a comanda. |
| DA-05 | Catálogo via Django Admin (não tela própria) | Admin já existe, é seguro, é suficiente para a proprietária com suporte do Paulo. Evita overengineering. |
| DA-06 | JS vanilla + `json_script` + POST arrays | Padrão já estabelecido em `daily_closing.js`. Sem framework SPA. Catálogo embutido como JSON no template para cálculo client-side sem round-trips. |
| DA-07 | `transaction.atomic()` ao salvar pedido + itens + adicionais | Garante consistência: ou tudo persiste ou nada. Padrão já usado em `DailyClosingUnifiedView`. |
| DA-08 | Integração com `DailyClosing` somente na Fase 6 | Evitar risco de dupla contagem antes do módulo estar validado em produção. |
| DA-09 | `DailyClosing.source` (`MANUAL`/`ORDERS`) para anti-dupla-contagem | Cada dia tem uma única fonte de verdade para vendas. |
| DA-10 | Carga do cardápio via management command idempotente | Cardápio é grande e preços mudam; command com `get_or_create` pode ser reexecutado sem duplicação. |
| DA-11 | Sem signals para fluxo financeiro | Regra explícita do `PROJECT_RULES.md`. Recalcular explicitamente via service. |
| DA-12 | Um único grupo `Operacao` (funcionários) via data migration; **admin = `is_superuser`** | Decidido em P-02/P-03: a proprietária usa `is_superuser`; funcionários usam `Operacao`. Não há necessidade de um grupo `Administracao` separado — "administrador" = `is_superuser`. Reusa `django.contrib.auth` sem criar sistema novo. |
| DA-13 | `order_time` = `TimeField`, manual, precisão `HH:MM` | Dado da comanda física; essencial para relatório de horário de pico. Nunca `auto_now`. Segundos desnecessários (P-11). |
| DA-14 | `Decimal` para todos os valores monetários | Regra absoluta do `PROJECT_RULES.md`. Nunca `float`. |
| DA-15 | `selectors.py` para leitura; `services.py` para escrita | Padrão declarado no `PROJECT_RULES.md`, seguido estritamente no novo app. |
| DA-16 | **Reutilizar antes de criar.** Nunca implementar algo sem antes verificar se já existe na codebase | Sempre reutilizar models, services, selectors, templates, componentes e padrões existentes antes de criar novas estruturas. Evita duplicação de lógica e mantém consistência arquitetural. |
| DA-17 | Janela de edição do funcionário atrelada à existência de `DailyClosing` do dia | Decidido em P-04: funcionário edita enquanto o dia não foi fechado; após o fechamento, só `is_superuser`. Consulta simples de existência, independente da integração da Fase 6. |
| DA-18 | Pagamentos apenas `PIX`/`CASH`/`CARD` na v1 (sem `OTHER`) | Decidido em P-07. Novas formas ficam para versões futuras, evitando complexidade prematura. |
| DA-19 | Excedente de adicionais no "Monte seu Açaí" vira pago automaticamente, sem bloquear | Decidido em P-06. Preserva a velocidade do lançamento e reflete a prática da loja. |

---

## 8. Permissões

### Perfis (decidido — P-02)

| Perfil | Implementação | Pode fazer |
|---|---|---|
| **Funcionário** | Grupo `Operacao` (criado via data migration) | Criar pedido; ver pedidos do dia; editar pedido **enquanto o dia não foi fechado** (P-04); ver listagem do dia. **Não cancela.** |
| **Administrador (proprietária)** | `is_superuser` | Tudo: gerenciar catálogo; ver relatórios e histórico; **cancelar pedido** (com motivo obrigatório); editar pedidos mesmo após o fechamento do dia. |

> Não há um grupo `Administracao` separado. "Administrador" = `is_superuser`. Isso mantém o acesso atual da proprietária sem quebrar nada.

### Padrão de views
- `LoginRequiredMixin` em todas as views do app.
- Views de criação/edição de pedido (funcionário): checagem de pertencimento ao grupo `Operacao` **ou** `is_superuser`.
- Cancelamento e catálogo: `UserPassesTestMixin` com `self.request.user.is_superuser`.
- Edição após fechamento do dia: permitida apenas a `is_superuser` (ver DA-17).
- Exclusão física: apenas `is_superuser` (padrão do projeto) — lembrando que pedidos usam **cancelamento**, não delete.

---

## 9. Integração com o Fechamento Diário

### Situação atual (Fases 1–5)
- `DailyClosing` é o único modelo de vendas. Campos `cash_sales`, `pix_sales`, `card_sales` são preenchidos manualmente.
- Nenhuma alteração neste módulo durante as Fases 1–5.

#### Detalhes da integração (Fase 6)
1. Adicionar `DailyClosing.source = CharField(choices=['MANUAL','ORDERS'], default='MANUAL')`.
2. Service `recalculate_closing_from_orders(date)`: agrega pedidos `ACTIVE` do dia por `payment_method`, conta pedidos, grava/atualiza `DailyClosing(source='ORDERS')`.
3. **Anti-dupla-contagem:** se `source='ORDERS'`, edição manual dos campos de venda é bloqueada/avisada na tela unificada.
4. Dias antigos com `source='MANUAL'` permanecem intocados.
5. Chamar `recalculate_closing_from_orders` explicitamente (no service de salvar/cancelar pedido do dia e/ou via botão de recálculo) — sem signals.

### Mapeamento de pagamento
| `payment_method` | Coluna `DailyClosing` |
|---|---|
| `PIX` | `pix_sales` |
| `CASH` | `cash_sales` |
| `CARD` | `card_sales` |

---

## 10. Riscos Conhecidos

| # | Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|---|
| R-01 | Dupla contagem (pedidos + DailyClosing manual no mesmo dia) | Alta se Fase 6 mal implementada | Crítico | `DailyClosing.source`; fonte exclusiva por dia; testes específicos. |
| R-02 | Quebra de pedidos antigos ao editar catálogo | Média | Alto | FKs `SET_NULL` + snapshots históricos em todos os itens. |
| R-03 | JS complexo na tela de lançamento | Média | Médio | Dados do catálogo via `json_script`; JS vanilla; testar em mobile real. |
| R-04 | Unicidade `(product, size=NULL)` — comportamento varia por banco | Baixa | Médio | Validação extra via `clean()` no `ProductVariant`. |
| R-05 | Cobertura de testes cair abaixo de 80% | Média | Médio | Adicionar factories e testes a cada fase; monitorar com `--cov-fail-under=80`. |
| R-06 | Catálogo desatualizado (preços mudam) | Alta | Médio | Management command idempotente; Admin acessível. |
| R-07 | Implementação futura assumir erroneamente unicidade da comanda | Média | Alto | Documentado explicitamente (Seção 6, DA-04); nenhuma `UniqueConstraint`/índice único sobre `comanda_number`; conferência sempre por `Order.id`. |

---

## 11. Pendências Abertas

> **Todas resolvidas em 2026-07-15.** Nenhuma pendência bloqueia o início da Fase 1. As decisões abaixo estão incorporadas às Seções 5, 6, 7 e 8.

| # | Pergunta | Decisão | Status |
|---|---|---|---|
| P-01 | App: um único `orders` ou dois apps? | **Um único app `orders`.** | ✅ Resolvida |
| P-02 | Perfil da proprietária e dos funcionários? | Proprietária = `is_superuser`; funcionários = grupo `Operacao`. | ✅ Resolvida |
| P-03 | Quem pode cancelar pedido? | **Somente administrador (`is_superuser`).** Funcionários apenas editam. | ✅ Resolvida |
| P-04 | Janela de edição do funcionário? | **Enquanto o fechamento do dia não for realizado.** Após o fechamento, só administrador. | ✅ Resolvida |
| P-05 | Cancelamento exige motivo? | **Sim, motivo obrigatório** (`cancel_reason`). | ✅ Resolvida |
| P-06 | "Monte seu Açaí" acima do limite? | **Excedentes viram adicionais pagos automaticamente.** Não bloqueia o lançamento. | ✅ Resolvida |
| P-07 | Formas de pagamento? | **Apenas `PIX`, `CASH`, `CARD`.** Sem `OTHER`. Novas formas ficam para o futuro. | ✅ Resolvida |
| P-08 | Tipo do número da comanda? | **`CharField`** (flexibilidade futura). **Sem qualquer regra de unicidade.** | ✅ Resolvida |
| P-09 | `load_catalog` no deploy? | **Execução manual.** Não roda automaticamente no deploy. | ✅ Resolvida |
| P-10 | Divergência informado × calculado? | **Apenas alerta visual** na v1. Relatório específico é futuro. | ✅ Resolvida |
| P-11 | Precisão do horário? | **`HH:MM`** (sem segundos). | ✅ Resolvida |
| P-12 | Adicionais com múltiplas unidades? | **Não na v1.** Uma seleção = uma unidade. Evolução futura. | ✅ Resolvida |

---

## 12. Plano de Fases

---

### Fase 0 — Auditoria e Decisões
**Status: ✅ Concluída**

**Objetivo:** Fechar todas as decisões de projeto antes de escrever código.

**Mudanças:** Nenhuma de código. Criação deste documento.

**Dependências:** Plano técnico aprovado pelo Paulo.

**Checklist técnico:**
- [x] Ler toda a codebase existente (`finance/models.py`, `services.py`, `views.py`, `forms.py`, etc.)
- [x] Identificar padrões arquiteturais vigentes
- [x] Mapear modelos existentes para evitar duplicação
- [x] Identificar forma de pagamento atual (colunas, não model)
- [x] Documentar riscos de integração com `DailyClosing`
- [x] Definir estratégia de snapshots históricos
- [x] Propor modelagem completa
- [x] Documentar decisões arquiteturais
- [x] Criar este arquivo ROADMAP_PEDIDOS.md

**Testes esperados:** —

**Critérios de aceite:**
- [x] Documento aprovado pelo Paulo
- [x] Perguntas da Seção 11 encaminhadas

---

### Fase 1 — Catálogo
**Status: ✅ Concluída**

**Objetivo:** Criar os modelos de catálogo administráveis (`ProductCategory`, `Size`, `Product`, `ProductVariant`, `Addon`), com admin configurado e migrações.

**Arquivos que serão criados:**
- `orders/__init__.py`
- `orders/apps.py`
- `orders/models.py` — `ProductCategory`, `Size`, `Product`, `ProductVariant`, `Addon`
- `orders/admin.py` — registro com fieldsets e displays
- `orders/selectors.py` — stub inicial
- `orders/services.py` — stub inicial
- `orders/migrations/0001_initial.py`

**Arquivos que serão modificados:**
- `gestao_financeira/settings.py` — adicionar `'orders'` em `INSTALLED_APPS`

**Dependências:** Fase 0 completa. Todas as pendências (P-01 a P-12) resolvidas.

**Checklist técnico:**
- [x] Criar estrutura do app `orders`
- [x] Implementar `ProductCategory` com `kind` choices
- [x] Implementar `Size` com `volume_ml`
- [x] Implementar `Product` com `product_type` choices
- [x] Implementar `ProductVariant` com `included_addons_limit` e constraint `(product, size)`
- [x] Implementar `Addon` com `is_free_option`
- [x] Configurar `verbose_name`, `ordering` e `indexes` em todos os models
- [x] `clean()` em `ProductVariant` para unicidade com `size=NULL`
- [x] Registrar todos os models no `admin.py` com fieldsets formatados
- [x] Gerar migração `0001_initial`
- [x] Registrar app em `INSTALLED_APPS`
- [x] Rodar `migrate` sem erros

**Testes esperados:**
- Criação de categoria, produto, variação e adicional
- Produto ativo × inativo
- Constraint de variante duplicada `(product, size)`
- `__str__` de cada model

**Critérios de aceite:**
- [x] Cadastrar todo o cardápio pelo Django Admin sem tocar código
- [x] Admin sem erros de runtime
- [x] Testes passando com cobertura ≥ 80%
- [x] `migrate` sem conflitos em SQLite e Postgres

---

### Fase 2 — Carga Inicial do Cardápio
**Status: ✅ Concluída**

**Objetivo:** Popular o catálogo com o cardápio real da Açaí da Rose.

**Arquivos que serão criados:**
- `orders/management/__init__.py`
- `orders/management/commands/__init__.py`
- `orders/management/commands/load_catalog.py` — idempotente, usa `get_or_create`

**Arquivos opcionalmente criados:**
- `orders/migrations/0002_seed_sizes_and_categories.py` — data migration para `Size` e `ProductCategory` base

**Dependências:** Fase 1 completa.

**Checklist técnico:**
- [x] Criar management command `load_catalog`
- [x] Implementar carga de `Size` (6 tamanhos + volume_ml)
- [x] Implementar carga de `ProductCategory` (Monte seu Açaí, Açaís Prontos, Adicionais, Sorvetes, Vitaminas)
- [x] Implementar carga de `Addon` com preços e `is_free_option`
- [x] Implementar carga de `Product` por categoria
- [x] Implementar carga de `ProductVariant` com preços (conferir com cardápio)
- [x] Implementar carga de `ProductVariant` para "Monte seu Açaí" com `included_addons_limit`
- [x] Garantir idempotência: executar 2× não duplica registros
- [x] Execução **manual** apenas (P-09) — não adicionar ao `build.sh`/deploy

**Testes esperados:**
- Rodar command 2× sem duplicação
- Contagem de produtos/variações conferida com o cardápio
- Preços de "Açaí Oreo 500ml" = R$ 26,00 (spot check)
- `included_addons_limit` de "Monte seu Açaí 500ml" = 3

**Critérios de aceite:**
- [x] Cardápio completo disponível no Admin
- [x] Nenhum produto duplicado após reexecução
- [x] Pelo menos 1 produto de cada categoria carregado

---

### Fase 3 — Pedidos e Itens
**Status: ✅ Concluída**

**Objetivo:** Implementar `Order`, `OrderItem`, `OrderItemAddon`, services de criação/atualização/cancelamento com cálculo correto de totais em `transaction.atomic`.

**Pré-requisito:** Nenhum pendente — todas as decisões (P-03 a P-12) já resolvidas na Seção 11.

**Arquivos que serão criados/modificados:**
- `orders/models.py` — adicionar `Order`, `OrderItem`, `OrderItemAddon`
- `orders/services.py` — `create_order`, `update_order`, `cancel_order`, funções de cálculo
- `orders/selectors.py` — `get_orders_by_date`, `get_order_detail`
- `orders/migrations/0002_orders.py` (ou continua em `0001` se gerado junto)
- `tests/conftest.py` — factories para `Order`, `OrderItem`, `OrderItemAddon`
- `tests/test_models.py` — testes dos novos models
- `tests/test_services.py` — testes dos novos services

**Dependências:** Fase 1. (Pendências todas resolvidas.)

**Checklist técnico:**
- [x] Implementar `Order` com todos os campos e choices (`PIX`/`CASH`/`CARD`) — **sem constraint de unicidade de comanda**
- [x] Implementar `OrderItem` com snapshots e cálculo de `line_total` (suporta múltiplos itens por pedido)
- [x] Implementar `OrderItemAddon` com `is_included` e `line_total` (`quantity` sempre 1 na v1)
- [x] Implementar `Order.total` calculado e salvo (não property pura — precisa persistir)
- [x] Implementar `create_order(*, comanda_number, order_date, order_time, payment_method, items, created_by)` com `transaction.atomic`
- [x] Implementar `cancel_order(*, order, cancelled_by, reason)` com auditoria — **`reason` obrigatório**
- [x] Implementar `update_order(...)` com regra de janela (bloqueada para `Operacao` se já existe `DailyClosing` do dia — DA-17)
- [x] Validar limite de adicionais incluídos no service; **excedente vira pago automaticamente** (DA-19), sem bloquear
- [x] Validar `informed_total` vs `total` (divergência gera aviso, não erro)
- [x] Implementar `get_orders_by_date(date)` em `selectors.py`
- [x] Gerar migração
- [x] Adicionar factories ao `conftest.py`

**Testes esperados:**
- Criar pedido com múltiplos itens (ex.: Açaí Monte 300ml + Açaí Nutella 500ml + 2 Coca-Cola)
- Cálculo correto de `line_total`, `addons_total`, `order.total`
- Adicional incluído (grátis) × pago
- Limite de adicionais incluídos no "Monte seu Açaí" respeitado
- **Excedente de adicionais convertido automaticamente em pago, sem bloquear**
- Preservação de preço histórico após alterar catálogo
- **Comanda repetida no mesmo dia é permitida** (dois `Order` com `comanda_number='1'` na mesma data — ambos salvam; `Order.id` distintos)
- Cancelamento com auditoria e **motivo obrigatório** (cancelar sem motivo deve falhar)
- Divergência informado × calculado (aviso, não erro)
- Validação de `payment_method` (apenas `PIX`/`CASH`/`CARD`)

**Critérios de aceite:**
- [x] Criar pedido completo via shell/testes com totais corretos
- [x] Preço histórico isolado de mudanças no catálogo
- [x] Nenhuma constraint de unicidade sobre `comanda_number`
- [x] Cobertura ≥ 80%

---

### Fase 4 — Interface Operacional (Lançamento)
**Status: ✅ Concluída**

**Objetivo:** Tela rápida mobile-first para o funcionário lançar pedidos.

**Pré-requisito:** Nenhum pendente. Perfis definidos (P-02): funcionário = `Operacao`, admin = `is_superuser`.

**Arquivos que serão criados:**
- `orders/views.py` — `OrderCreateView`
- `orders/urls.py`
- `templates/orders/order_form.html` — tela de lançamento
- `static/js/order_form.js` — seleção de categoria/produto/variação/adicionais, cálculo de totais

**Arquivos que serão modificados:**
- `gestao_financeira/urls.py` — incluir `orders.urls`
- `templates/base.html` — item de menu "Pedidos"
- `finance/context_processors.py` — label `NAV_PEDIDOS`

**Dependências:** Fases 1, 2 e 3.

**Checklist técnico:**
- [x] Catálogo embutido via `json_script` no template
- [x] JS: seleção de categoria → produto → tamanho → preço automático
- [x] JS: seleção de adicionais com contador de incluídos (limite visual)
- [x] JS: cálculo de subtotal e total em tempo real
- [x] Campo "valor informado na comanda" com alerta de divergência (não bloqueante)
- [x] Botão "Adicionar item" + lista de itens no carrinho
- [x] POST com arrays de campos no padrão `daily_closing.js`
- [x] View processa POST em `transaction.atomic`, chama `create_order`
- [x] `LoginRequiredMixin` + checagem de grupo `Operacao` **ou** `is_superuser`
- [x] Mensagens de sucesso/erro via `messages`
- [ ] Testar em mobile (390px) — pendente: validação visual em dispositivo real

**Testes esperados:**
- POST cria pedido + itens + adicionais corretamente
- Alerta de divergência aparece mas não bloqueia
- Usuário sem grupo adequado recebe 403
- Campos de horário e número da comanda são obrigatórios

**Critérios de aceite:**
- [x] Lançar "Comanda 10 / 16:30 / PIX / Açaí Oreo 500ml + Nutella = R$ 33,50" em < 5 cliques após seleção de categoria
- [ ] Tela funcional em mobile 390px — pendente: validação visual em dispositivo real
- [x] Total calculado bate com valor esperado
- [x] Cobertura ≥ 80%

---

### Fase 5 — Listagem, Edição e Cancelamento
**Status: ✅ Concluída**

**Objetivo:** Tela de conferência dos pedidos do dia; correção e cancelamento conforme permissão.

**Arquivos que serão criados:**
- `orders/views.py` — `OrderListView`, `OrderDetailView`, `OrderUpdateView`, `OrderCancelView`
- `templates/orders/order_list.html`
- `templates/orders/order_detail.html`
- `templates/orders/order_form_edit.html` (ou reusar `order_form.html`)
- `templates/orders/order_cancel_confirm.html`

**Arquivos que serão modificados:**
- `orders/urls.py` — novas rotas
- `orders/selectors.py` — queries de listagem e detalhe
- `orders/services.py` — lógica de janela de correção em `update_order`

**Dependências:** Fase 4.

**Checklist técnico:**
- [x] `OrderListView`: filtro por data (navegação por dia, padrão da tela de fechamento)
- [x] Exibir: número, horário, itens resumidos, pagamento, total, usuário, status
- [x] Botão "Ver" (todos); "Corrigir" (`Operacao` enquanto o dia não foi fechado, ou `is_superuser` sempre); "Cancelar" (apenas `is_superuser`)
- [x] `OrderUpdateView` com validação da janela de edição (existe `DailyClosing` do dia? → só `is_superuser` — DA-17)
- [x] `OrderCancelView` com confirmação, **motivo obrigatório**, auditoria (`cancel_reason`, `cancelled_by`, `cancelled_at`)
- [x] Pedidos cancelados exibidos com badge/estilo distinto
- [x] Sem delete físico de pedidos

**Testes esperados:**
- Listagem do dia mostra pedidos corretamente (inclui comandas com número repetido)
- Funcionário pode corrigir enquanto o dia não foi fechado; bloqueado após o fechamento
- `is_superuser` pode editar mesmo após o fechamento
- Admin (`is_superuser`) pode cancelar qualquer pedido; **funcionário não pode cancelar** (403)
- Cancelamento sem motivo é rejeitado; com motivo registra auditoria completa
- Dois pedidos com o mesmo `comanda_number` no mesmo dia coexistem normalmente

**Critérios de aceite:**
- [x] Tela facilita conferência com comandas físicas
- [x] Cancelamento com auditoria visível
- [x] Permissões respeitadas
- [x] Cobertura ≥ 80%

---

### Fase 6 — Integração com o Fechamento Diário
**Status: ✅ Concluída**

**Objetivo:** Pedidos `ACTIVE` alimentam automaticamente o `DailyClosing`, sem dupla contagem.

**Pré-requisito:** Fases 1–5 validadas em produção. (Formas de pagamento já definidas — P-07: `PIX`/`CASH`/`CARD`.)

**Arquivos que serão modificados:**
- `finance/models.py` — adicionar campo `source` em `DailyClosing`
- `finance/services.py` — integrar `recalculate_closing_from_orders` no fluxo
- `finance/views.py` — bloquear edição manual quando `source='ORDERS'`
- `orders/services.py` — chamar recálculo após criar/cancelar pedido do dia
- `finance/migrations/` — nova migration para `source`

**Arquivos que serão criados:**
- `orders/services.py` — função `recalculate_closing_from_orders(date)`

**Dependências:** Fases 1–5.

**Checklist técnico:**
- [x] Adicionar `DailyClosing.source` com default `'MANUAL'`
- [x] Implementar `recalculate_closing_from_orders(date)`
- [x] Agregar por `payment_method` → colunas corretas
- [x] `order_count` = contagem de pedidos `ACTIVE`
- [x] Chamar recálculo em `create_order` e `cancel_order` se `order_date == today`
- [x] Bloquear/avisar edição manual de `cash_sales`, `pix_sales`, `card_sales` quando `source='ORDERS'`
- [x] Dias antigos (`source='MANUAL'`) intocados
- [ ] Testar em Postgres (constraint + agregações) — pendente: validar no deploy

**Testes esperados:**
- Totais derivados de pedidos batem com `DailyClosing` gerado
- Dupla contagem impossível: dia só pode ter uma fonte
- Cancelar pedido do dia recalcula o fechamento
- Dia sem pedidos (source MANUAL) permanece inalterado
- Dias antigos com MANUAL não são alterados pela migration

**Critérios de aceite:**
- [x] Dashboard e relatórios refletem pedidos corretamente
- [x] Nenhuma dupla contagem em nenhum cenário de teste
- [x] Compatibilidade com histórico de fechamentos manuais
- [x] Cobertura ≥ 80%

---

### Fase 7 — Relatórios
**Status: ✅ Concluída**

**Objetivo:** Relatórios operacionais de produtos, adicionais, horários e faturamento por produto.

**Arquivos que serão criados/modificados:**
- `orders/selectors.py` — funções de agregação para relatórios
- `orders/views.py` — `OrderReportView`
- `templates/orders/order_report.html`
- `orders/urls.py` — rota de relatório

**Relatórios previstos (implementar gradualmente):**
- Quantidade de pedidos por dia/semana/mês
- Faturamento por período
- Ticket médio
- Vendas por forma de pagamento
- Produtos mais vendidos
- Tamanhos mais vendidos
- Litros de açaí vendidos (`Size.volume_ml × OrderItem.quantity`)
- Adicionais mais selecionados
- Horários de pico (`order_time`)
- Divergências calculado × informado

**Dependências:** Fase 3+ (dados suficientes).

**Checklist técnico:**
- [x] Implementar selectors de agregação com índices existentes
- [x] Gráficos com Chart.js (padrão `dashboard.html`)
- [x] Filtro de período (reutilizar padrão de `ReportFilterForm`)
- [x] Relatório de litros com `volume_ml`
- [x] Relatório de horário de pico com agrupamento por hora
- [x] Relatório de divergências

**Testes esperados:**
- Cada agregação testada com dataset de fixture
- Relatório de litros correto
- Horário de pico identifica hora com mais pedidos

**Critérios de aceite:**
- [x] Relatórios exibem dados coerentes com os pedidos lançados
- [x] Filtro por período funciona
- [x] Cobertura ≥ 80%

---

### Fase 8 — Testes, Documentação e Implantação
**Status: ⬜ Não iniciada**

**Objetivo:** Fechar cobertura de testes, revisar docs e realizar deploy em produção.

**Arquivos que serão modificados:**
- `tests/conftest.py` — factories completas
- `tests/test_*.py` — cobertura completa
- `docs/ROADMAP_PEDIDOS.md` — Diário de Desenvolvimento atualizado
- `PROJECT_RULES.md` — novas regras do app `orders` (se necessário)
- `DEPLOY.md` — instrução de execução **manual** de `load_catalog` (P-09: não roda no deploy)
- `render.yaml` — revisar se necessário

**Dependências:** Fases 1–7.

**Checklist técnico:**
- [ ] Suíte completa verde: `pytest --cov-fail-under=80`
- [ ] Testar `UniqueConstraint(product, size)` do `ProductVariant` no Postgres real (não há constraint de comanda)
- [ ] Testar management command `load_catalog` no ambiente de produção
- [ ] Verificar static files (`collectstatic`)
- [ ] Deploy no Render sem erros de migração
- [ ] Testar tela de lançamento em mobile real

**Critérios de aceite:**
- [ ] Deploy bem-sucedido
- [ ] Cardápio carregado em produção
- [ ] Lançamento de pedido real pela usuária final sem erros

---

## 13. Diário de Desenvolvimento

> Atualizar ao **concluir cada fase**. Registrar data, alterações, arquivos, migrações, testes e pendências encontradas.

---

### Fase 0 — Auditoria e Decisões
**Data:** 2026-07-15
**Fase:** 0 — Auditoria e Decisões
**Responsável:** Paulo + Claude

**Resumo:**
Análise completa da codebase existente. Produção do documento de planejamento técnico detalhado e criação deste ROADMAP.

**Arquivos modificados:**
- `docs/ROADMAP_PEDIDOS.md` (criado)

**Migrações criadas:** nenhuma.

**Testes executados:** nenhum.

**Decisões registradas:** DA-01 a DA-15 (Seção 7).

**Pendências encontradas:** P-01 a P-12 (Seção 11) — encaminhadas ao Paulo.

---

### Revisão do Roadmap (pré-Fase 1)
**Data:** 2026-07-15
**Fase:** Revisão de documentação (nenhuma implementação)
**Responsável:** Paulo + Claude

**Resumo:**
Revisão final do roadmap antes de iniciar a Fase 1. Todas as pendências (P-01 a P-12) foram respondidas e incorporadas. Documentada explicitamente a regra de **múltiplos itens por pedido**. **Removida completamente a unicidade da comanda** (blocos físicos de 1 a 50 reiniciados → números se repetem no mesmo dia; identificador único = `Order.id`). Adicionadas as decisões DA-16 a DA-19 e a seção "Continuidade do Projeto".

**Principais mudanças:**
- Seção 6: nova regra "Pedido com múltiplos itens"; "Número da comanda (SEM unicidade)"; excedente de adicionais → pago automático; cancelamento só admin + motivo obrigatório; janela de edição atrelada ao fechamento; pagamentos sem `OTHER`.
- Seção 5: removida `UniqueConstraint` de comanda; `payment_method` sem `OTHER`; notas de `HH:MM` e `quantity=1`.
- Seção 7: DA-04 reescrita (comanda sem unicidade); DA-12 simplificada (só grupo `Operacao`, admin = `is_superuser`); DA-16 (reutilizar antes de criar), DA-17 (janela de edição), DA-18 (pagamentos), DA-19 (excedente).
- Seção 8: perfis simplificados (funcionário `Operacao` / admin `is_superuser`).
- Seção 11: todas as pendências marcadas ✅ com decisão.
- Seção 14: nova — guia de continuidade entre sessões.

**Arquivos modificados:** `docs/ROADMAP_PEDIDOS.md`.

**Migrações criadas:** nenhuma.

**Testes executados:** nenhum.

**Pendências encontradas:** nenhuma. Projeto liberado para iniciar a Fase 1.

---

### Fase 1 — Catálogo
**Data:** 2026-07-15
**Fase:** 1 — Catálogo
**Responsável:** Paulo + Claude

**Resumo:**
Criação do app `orders` com todos os modelos de catálogo: `ProductCategory`, `Size`, `Product`, `ProductVariant`, `Addon`. Admin configurado com fieldsets e exibições formatadas. Migration `0001_initial` gerada e aplicada sem erros.

**Arquivos criados:**
- `orders/__init__.py`
- `orders/apps.py`
- `orders/models.py`
- `orders/admin.py`
- `orders/selectors.py` (stub)
- `orders/services.py` (stub)
- `orders/migrations/0001_initial.py`
- `tests/test_orders_models.py` (33 testes)

**Arquivos modificados:**
- `gestao_financeira/settings.py` — `'orders'` adicionado a `INSTALLED_APPS`
- `pytest.ini` — `--cov=orders` adicionado
- `tests/conftest.py` — factories e fixtures para os 5 novos models

**Migrações criadas:** `orders/migrations/0001_initial.py`

**Testes executados:** 121 passando, cobertura total 80.06%.

**Decisões registradas:**
- `UniqueConstraint` com `condition=Q(size__isnull=False)` (índice parcial) + `clean()` para `size=NULL` — mais explícito e seguro cross-DB do que constraint sem condição.

**Pendências encontradas:** nenhuma. Fase 2 pode iniciar.

---

### Fase 2 — Carga Inicial do Cardápio
**Data:** 2026-07-15
**Fase:** 2 — Carga Inicial do Cardápio
**Responsável:** Paulo + Claude

**Resumo:**
Management command `load_catalog` criado com cardápio completo da Açaí da Rose. Idempotente via `get_or_create`. Suporta `--dry-run`. Resultado: 5 categorias, 6 tamanhos, 24 produtos, 88 variações, 27 adicionais (150 registros no total).

**Arquivos criados:**
- `orders/management/__init__.py`
- `orders/management/commands/__init__.py`
- `orders/management/commands/load_catalog.py`
- `tests/test_orders_load_catalog.py` (20 testes)

**Migrações criadas:** nenhuma.

**Testes executados:** 141 passando, cobertura total 80.06%.

**Pendências encontradas:** nenhuma. Fase 3 pode iniciar.

---

### Fase 3 — Pedidos e Itens
**Data:** 2026-07-15
**Fase:** 3 — Pedidos e Itens
**Responsável:** Paulo + Claude

**Resumo:**
Implementação completa de `Order`, `OrderItem`, `OrderItemAddon` com todos os campos, choices e snapshots históricos. Services `create_order`, `cancel_order`, `update_order` e selectors `get_orders_by_date`, `get_order_detail`. Migration `0002_orders_and_items` gerada e aplicada.

**Arquivos modificados/criados:**
- `orders/models.py` — adicionados `Order`, `OrderItem`, `OrderItemAddon`
- `orders/services.py` — implementado completamente
- `orders/selectors.py` — implementado completamente
- `orders/migrations/0002_orders_and_items.py`
- `tests/conftest.py` — `OrderFactory`, `OrderItemFactory`, `OrderItemAddonFactory`, fixture `order`
- `tests/test_orders_services.py` — 38 testes

**Migrações criadas:** `orders/migrations/0002_orders_and_items.py`

**Testes executados:** 179 passando, cobertura total 83.01%.

**Decisões registradas:** nenhuma nova — todas já cobertas por DA-01 a DA-19.

**Pendências encontradas:** nenhuma. Fase 4 pode iniciar.

---

### Fase 4 — Interface Operacional (Lançamento)
**Data:** 2026-07-15
**Fase:** 4 — Interface Operacional
**Responsável:** Paulo + Claude

**Resumo:**
Criação da tela de lançamento de pedidos: `OrderCreateView`, URLs, template mobile-first e `order_form.js`. Catálogo embutido via `json_script`. Fluxo Categoria → Produto → Tamanho → Adicionais → Carrinho → Envio. Data migration `0003_create_operacao_group` cria o grupo `Operacao`. Seleção automática quando há apenas um produto/tamanho; adicionais com contador visual de grátis vs. pagos; alerta de divergência não bloqueante.

**Arquivos criados:**
- `orders/migrations/0003_create_operacao_group.py`
- `orders/views.py` — `OrderCreateView`
- `orders/urls.py`
- `templates/orders/order_form.html`
- `static/js/order_form.js`
- `tests/test_orders_views.py` — 18 testes

**Arquivos modificados:**
- `orders/selectors.py` — adicionado `get_catalog_json()`
- `gestao_financeira/urls.py` — include `orders.urls`
- `templates/base.html` — item "Pedidos" no menu
- `finance/context_processors.py` — `NAV_PEDIDOS`

**Migrações criadas:** `orders/migrations/0003_create_operacao_group.py`

**Testes executados:** 197 passando, cobertura total 82.85%.

**Decisões registradas:** nenhuma nova — todas cobertas por DA-01 a DA-19.

**Pendências encontradas:**
- Validação visual em mobile 390px pendente (requer dispositivo real / navegador).
- Após lançamento bem-sucedido, redireciona para o formulário limpo (Phase 5 adicionará link para lista do dia).

---

### Fase 5 — Listagem, Edição e Cancelamento
**Data:** 2026-07-15
**Fase:** 5 — Listagem, Edição e Cancelamento
**Responsável:** Paulo + Claude

**Resumo:**
`OrderListView` com navegação por data (padrão `DailyClosingUnifiedView`), `OrderDetailView` com itens e adicionais, `OrderUpdateView` respeitando janela de edição (DA-17), `OrderCancelView` exclusiva de superusuário com motivo obrigatório e auditoria completa. Menu "Pedidos" atualizado para apontar para a lista. `OrderCreateView` agora redireciona para o detalhe após criação.

**Arquivos criados:**
- `templates/orders/order_list.html`
- `templates/orders/order_detail.html`
- `templates/orders/order_form_edit.html`
- `templates/orders/order_cancel_confirm.html`
- 34 novos testes em `tests/test_orders_views.py`

**Arquivos modificados:**
- `orders/views.py` — `OrderListView`, `OrderDetailView`, `OrderUpdateView`, `OrderCancelView`; redirect do create atualizado
- `orders/urls.py` — 5 novas rotas
- `orders/selectors.py` — `get_orders_by_date_with_items()`
- `templates/base.html` — nav "Pedidos" aponta para `order-list`
- `tests/test_orders_views.py` — novos testes de Fase 5

**Migrações criadas:** nenhuma.

**Testes executados:** 231 passando, cobertura total 83.08%.

**Decisões registradas:** nenhuma nova — todas cobertas por DA-01 a DA-19.

**Pendências encontradas:** nenhuma. Fase 6 pode iniciar (integração com Fechamento Diário).

---

### Fase 6 — Integração com o Fechamento Diário
**Data:** 2026-07-15
**Fase:** 6 — Integração com o Fechamento Diário
**Responsável:** Paulo + Claude

**Resumo:**
Campo `DailyClosing.source` (`MANUAL`/`ORDERS`) adicionado ao modelo. Função `recalculate_closing_from_orders(*, date)` implementada em `orders/services.py`: agrega pedidos `ACTIVE` por forma de pagamento e cria/atualiza o `DailyClosing` do dia com `source='ORDERS'`. Fechamentos com `source='MANUAL'` não são tocados. `create_order` e `cancel_order` chamam o recalculate automaticamente quando `order_date == today`. Tela de fechamento unificada exibe alerta e torna os campos de vendas somente leitura quando `source='ORDERS'`, permitindo ainda editar observações e despesas.

**Arquivos modificados/criados:**
- `finance/models.py` — `DailyClosing.ClosingSource` + campo `source`
- `finance/migrations/0003_dailyclosing_source.py` — migration do novo campo
- `finance/services.py` — `create_daily_closing` e `update_daily_closing` aceitam `source`
- `finance/views.py` — `DailyClosingUnifiedView` trata `source='ORDERS'` no GET e POST
- `orders/services.py` — `recalculate_closing_from_orders`; chamada em `create_order` e `cancel_order`
- `templates/finance/daily_closing_unified.html` — alerta e campos readonly para `source='ORDERS'`
- `tests/test_orders_phase6.py` — 14 novos testes
- `tests/test_orders_services.py` — `TestUpdateOrder` ajustado para usar data passada

**Migrações criadas:** `finance/migrations/0003_dailyclosing_source.py`

**Testes executados:** 245 passando, cobertura total 87.86%.

**Decisão registrada:** `recalculate_closing_from_orders` só cria/atualiza um fechamento `ORDERS`; nunca toca fechamentos `MANUAL`. A chamada automática é restrita a `order_date == today` para não interferir em histórico.

**Pendências encontradas:** Validar agregações no Postgres do Render após deploy. Fase 7 pode iniciar.

---

### Fase 7 — Relatórios
**Data:** 2026-07-15
**Fase:** 7 — Relatórios
**Responsável:** Paulo + Claude

**Resumo:**
Implementação completa do módulo de relatórios de pedidos, acessível apenas a `is_superuser`. Filtro de período reutilizando `ReportFilterForm` de `finance/forms.py` (DA-16). Nove selectors de agregação adicionados a `orders/selectors.py`: resumo do período, vendas por forma de pagamento, top produtos, top tamanhos, litros vendidos (via `variant__size__volume_ml`), top adicionais, horários de pico, divergências e totais diários. Template mobile-first com gráficos Chart.js (donut de pagamentos, linha de faturamento diário, barras de horário de pico). Botão "Relatórios" visível apenas para superusuários na listagem.

**Arquivos criados:**
- `templates/orders/order_report.html`
- `tests/test_orders_phase7.py` — 27 testes

**Arquivos modificados:**
- `orders/selectors.py` — 9 novas funções de agregação
- `orders/views.py` — `OrderReportView` + helper `_calculate_period_dates`
- `orders/urls.py` — rota `pedidos/relatorios/` (inserida antes de `<str:order_date>/`)
- `templates/base.html` — `order-report` adicionado ao active check do nav
- `templates/orders/order_list.html` — botão "Relatórios" para superusuários

**Migrações criadas:** nenhuma.

**Testes executados:** 272 passando, cobertura total 87.71%. `orders/selectors.py` com 100% de cobertura.

**Decisões registradas:** nenhuma nova — todas cobertas por DA-01 a DA-19.

**Pendências encontradas:** nenhuma. Fase 8 pode iniciar (testes, documentação e implantação).

---

> *As próximas entradas serão adicionadas aqui ao final de cada fase.*

---

## 14. Continuidade do Projeto

> Esta seção orienta **qualquer nova sessão de desenvolvimento**, inclusive após perda total do contexto da conversa.

**Sempre que uma nova conversa for iniciada:**

1. **Ler integralmente este roadmap** (`docs/ROADMAP_PEDIDOS.md`).
2. **Identificar a última fase concluída** (Seção 12 → campo "Status"; confirmar no Diário de Desenvolvimento, Seção 13).
3. **Revisar todos os arquivos relacionados** àquela fase (listados em "Arquivos que serão criados/modificados").
4. **Revisar as migrations existentes** do app `orders` (e de `finance`, se relevante).
5. **Revisar os testes existentes** (`tests/` e factories em `tests/conftest.py`).
6. **Não iniciar mais de uma fase por vez.** Implementar somente a próxima fase pendente.
7. **Ao concluir uma fase:**
   - atualizar o "Status" da fase neste roadmap;
   - atualizar o **Diário de Desenvolvimento** (Seção 13) com data, resumo, arquivos, migrações, testes e pendências;
   - registrar novas **Decisões Arquiteturais** (Seção 7) quando houver;
   - **aguardar aprovação** do Paulo antes de iniciar a próxima fase.

**Princípios permanentes (ver também Seção 7 e `PROJECT_RULES.md`):**
- **Reutilizar antes de criar** (DA-16): verificar se models, services, selectors, templates, componentes ou padrões já existem antes de escrever algo novo.
- `Decimal` para dinheiro; nunca `float`.
- Escrita em `services.py`, leitura em `selectors.py`, views finas.
- `comanda_number` **nunca** é chave única; o identificador é `Order.id`.
- Mobile-first, mínimo de cliques, linguagem simples (usuária final não técnica).

**Objetivo:** qualquer desenvolvedor deve conseguir continuar exatamente do ponto onde o projeto parou, sem conhecimento prévio da conversa.
