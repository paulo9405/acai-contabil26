# Lista Completa de Testes Manuais - Gestão Financeira

## Pré-requisitos

1. **Servidor rodando**
   ```bash
   source venv/bin/activate
   python manage.py runserver
   ```

2. **Acessar**: http://localhost:8000

3. **Usuário de teste**
   - Se não tiver usuário, criar um:
   ```bash
   python manage.py createsuperuser
   ```

---

## 1. TESTES DE AUTENTICAÇÃO

### 1.1 Login
- [ ] Acessar http://localhost:8000
- [ ] Verificar redirecionamento para /dashboard/
- [ ] Se não autenticado, redireciona para /accounts/login/
- [ ] Fazer login com credenciais corretas
- [ ] Verificar redirecionamento para dashboard
- [ ] Tentar login com credenciais incorretas
- [ ] Verificar mensagem de erro

### 1.2 Logout
- [ ] Clicar no dropdown do usuário (canto superior direito)
- [ ] Clicar em "Sair"
- [ ] Verificar redirecionamento para página de login
- [ ] Tentar acessar /dashboard/ sem estar logado
- [ ] Verificar redirecionamento para login

### 1.3 Admin (apenas superusuários)
- [ ] Acessar dropdown do usuário
- [ ] Verificar link "Admin" (apenas se for superuser)
- [ ] Clicar em "Admin"
- [ ] Verificar acesso ao Django Admin

---

## 2. TESTES DO DASHBOARD

### 2.1 Visualização Geral
- [ ] Acessar /dashboard/
- [ ] Verificar título "Dashboard"
- [ ] Verificar subtítulo "Visão geral do negócio"

### 2.2 Botões de Ação Rápida
- [ ] Verificar presença de 2 botões grandes:
  - [ ] "Novo Fechamento" (azul)
  - [ ] "Nova Despesa" (verde)
- [ ] Clicar em cada botão e verificar redirecionamento

### 2.3 Métricas de Hoje
- [ ] Verificar seção "Hoje - [data]"
- [ ] Verificar 5 cards:
  - [ ] Pedidos (número)
  - [ ] Vendas (R$, borda verde)
  - [ ] Despesas (R$, borda vermelha)
  - [ ] Lucro (R$, borda azul/amarela)
  - [ ] Ticket Médio (R$)
- [ ] Verificar cores corretas
- [ ] Verificar valores formatados corretamente

### 2.4 Métricas do Mês
- [ ] Verificar seção "Este Mês"
- [ ] Verificar 5 cards similares aos de hoje
- [ ] No card de Pedidos, verificar texto "X dias" abaixo
- [ ] Verificar que valores são maiores que os de hoje

### 2.5 Últimos 7 Dias - Resumo
- [ ] Verificar seção "Últimos 7 Dias"
- [ ] Verificar 3 cards de resumo:
  - [ ] Total Vendas (verde)
  - [ ] Total Despesas (vermelho)
  - [ ] Total Lucro (azul/amarelo)

### 2.6 Gráfico de Tendência
- [ ] Verificar card "Tendência de Vendas vs Despesas"
- [ ] Verificar gráfico de linhas renderizado
- [ ] Verificar 3 linhas:
  - [ ] Vendas (verde, área preenchida)
  - [ ] Despesas (vermelho, área preenchida)
  - [ ] Lucro (azul, linha tracejada)
- [ ] Passar mouse sobre o gráfico
- [ ] Verificar tooltips mostrando valores em R$
- [ ] Verificar legendas no topo do gráfico

### 2.7 Últimos 7 Dias - Detalhes (MOBILE)
- [ ] Redimensionar navegador para 390px (ou usar DevTools mobile)
- [ ] Verificar cards compactos (um por dia)
- [ ] Verificar 4 colunas por card:
  - [ ] Data (dd/mm)
  - [ ] Vendas (verde)
  - [ ] Despesas (vermelho)
  - [ ] Lucro (azul/amarelo)

### 2.8 Últimos 7 Dias - Detalhes (DESKTOP)
- [ ] Redimensionar para tela grande (>768px)
- [ ] Verificar tabela com 4 colunas
- [ ] Verificar cabeçalhos: Data, Vendas, Despesas, Lucro
- [ ] Verificar cores nas células

### 2.9 Gráfico de Despesas por Categoria
- [ ] Verificar 2 cards lado a lado (desktop) ou empilhados (mobile)
- [ ] Card 1: Gráfico de rosca (doughnut)
  - [ ] Verificar cores variadas
  - [ ] Passar mouse e verificar tooltips com valor e percentual
  - [ ] Verificar legenda na parte inferior
- [ ] Card 2: "Top 5 Categorias"
  - [ ] Verificar lista com até 5 categorias
  - [ ] Verificar badges vermelhos com valores

### 2.10 Links Rápidos
- [ ] Rolar até o final da página
- [ ] Verificar 2 botões:
  - [ ] "Ver Todos os Fechamentos" (outline azul)
  - [ ] "Ver Todas as Despesas" (outline verde)
- [ ] Clicar em cada botão e verificar redirecionamento

---

## 3. TESTES DE FECHAMENTOS DIÁRIOS

### 3.1 Listar Fechamentos
- [ ] Acessar /closings/
- [ ] Verificar título "Fechamentos Diários"
- [ ] Verificar botão "Novo Fechamento" (verde, topo)

### 3.2 Lista de Fechamentos (MOBILE - 390px)
- [ ] Verificar cards compactos, um por fechamento
- [ ] Em cada card, verificar:
  - [ ] Data (dd/mm/yyyy)
  - [ ] Pedidos
  - [ ] Dinheiro, PIX, Cartão
  - [ ] Total de Vendas (negrito, verde)
  - [ ] Ticket Médio
  - [ ] Ícone de editar (azul)

### 3.3 Lista de Fechamentos (DESKTOP - >768px)
- [ ] Verificar tabela com 8 colunas
- [ ] Verificar cabeçalhos corretos
- [ ] Verificar botão "Editar" em cada linha
- [ ] Verificar paginação se houver mais de 20 registros

### 3.4 Criar Fechamento
- [ ] Clicar em "Novo Fechamento"
- [ ] Verificar formulário com campos grandes (form-control-lg)
- [ ] Verificar campos:
  - [ ] Data (type=date)
  - [ ] Quantidade de Pedidos (mínimo 0)
  - [ ] Vendas em Dinheiro (step=0.01, mínimo 0)
  - [ ] Vendas em Pix (step=0.01, mínimo 0)
  - [ ] Vendas em Cartão (step=0.01, mínimo 0)
  - [ ] Observações (textarea, 3 linhas, opcional)

### 3.5 Validações de Criação
- [ ] Tentar criar fechamento com data futura
  - [ ] Verificar mensagem: "A data não pode ser futura."
- [ ] Criar fechamento válido
  - [ ] Preencher todos os campos obrigatórios
  - [ ] Clicar em "Salvar Fechamento"
  - [ ] Verificar mensagem de sucesso
  - [ ] Verificar redirecionamento para lista
- [ ] Tentar criar fechamento duplicado (mesma data)
  - [ ] Verificar mensagem: "Já existe um fechamento para [data]."

### 3.6 Editar Fechamento
- [ ] Na lista, clicar em "Editar" em um fechamento
- [ ] Verificar formulário preenchido com dados atuais
- [ ] Verificar que data está desabilitada (readonly na prática)
- [ ] Alterar valores de vendas
- [ ] Clicar em "Atualizar Fechamento"
- [ ] Verificar mensagem de sucesso
- [ ] Verificar valores atualizados na lista

### 3.7 Excluir Fechamento (apenas superuser)
- [ ] Na lista, verificar se há botão "Excluir" (apenas superuser)
- [ ] Clicar em "Excluir"
- [ ] Verificar página de confirmação
- [ ] Verificar detalhes do fechamento
- [ ] Confirmar exclusão
- [ ] Verificar mensagem de sucesso
- [ ] Verificar que fechamento foi removido da lista

---

## 4. TESTES DE DESPESAS

### 4.1 Listar Despesas
- [ ] Acessar /expenses/
- [ ] Verificar título "Despesas"
- [ ] Verificar botão "Nova Despesa" (verde, topo)

### 4.2 Filtros de Despesas
- [ ] Verificar formulário de filtro com:
  - [ ] Data inicial (opcional)
  - [ ] Data final (opcional)
  - [ ] Categoria (dropdown com "Todas as categorias")
- [ ] Testar filtro por data inicial
- [ ] Testar filtro por data final
- [ ] Testar filtro por categoria
- [ ] Testar combinação de filtros
- [ ] Verificar que lista atualiza corretamente
- [ ] Verificar total de despesas no rodapé

### 4.3 Validação de Filtros
- [ ] Preencher data inicial maior que data final
- [ ] Clicar em "Filtrar"
- [ ] Verificar mensagem: "A data inicial não pode ser maior que a data final."

### 4.4 Lista de Despesas (MOBILE)
- [ ] Redimensionar para 390px
- [ ] Verificar cards compactos
- [ ] Em cada card, verificar:
  - [ ] Data
  - [ ] Categoria (badge azul)
  - [ ] Valor (vermelho, negrito)
  - [ ] Descrição truncada
  - [ ] Ícone de editar

### 4.5 Lista de Despesas (DESKTOP)
- [ ] Verificar tabela com 5 colunas
- [ ] Verificar paginação (20 por página)

### 4.6 Criar Despesa
- [ ] Clicar em "Nova Despesa"
- [ ] Verificar formulário com campos:
  - [ ] Data (type=date)
  - [ ] Categoria (dropdown com apenas categorias ativas)
  - [ ] Valor (step=0.01, mínimo 0.01)
  - [ ] Descrição (textarea opcional)

### 4.7 Validações de Criação
- [ ] Tentar criar despesa com data futura
  - [ ] Verificar mensagem de erro
- [ ] Tentar criar despesa com valor 0 ou negativo
  - [ ] Verificar mensagem: "O valor deve ser maior que zero."
- [ ] Criar despesa válida
  - [ ] Verificar mensagem de sucesso
  - [ ] Verificar na lista

### 4.8 Editar Despesa
- [ ] Clicar em "Editar" em uma despesa
- [ ] Alterar valores
- [ ] Salvar
- [ ] Verificar atualização

### 4.9 Excluir Despesa (apenas superuser)
- [ ] Verificar botão "Excluir" (apenas superuser)
- [ ] Excluir e verificar confirmação

---

## 5. TESTES DE RELATÓRIOS

### 5.1 Acessar Relatórios
- [ ] Clicar em "Relatórios" no menu
- [ ] Verificar /reports/
- [ ] Verificar título "Relatórios Financeiros"

### 5.2 Formulário de Filtro de Período
- [ ] Verificar dropdown de período com opções:
  - [ ] Hoje
  - [ ] Ontem
  - [ ] Últimos 7 dias
  - [ ] Últimos 30 dias
  - [ ] Este mês (padrão)
  - [ ] Mês passado
  - [ ] Personalizado
- [ ] Verificar que campos de data customizada estão ocultos

### 5.3 Testar Períodos Pré-definidos
- [ ] Selecionar "Hoje"
  - [ ] Clicar em "Gerar Relatório"
  - [ ] Verificar período exibido
  - [ ] Verificar métricas
- [ ] Repetir para cada período:
  - [ ] Ontem
  - [ ] Últimos 7 dias
  - [ ] Últimos 30 dias
  - [ ] Este mês
  - [ ] Mês passado

### 5.4 Período Personalizado
- [ ] Selecionar "Personalizado"
- [ ] Verificar que campos de data aparecem
- [ ] Tentar gerar sem preencher datas
  - [ ] Verificar mensagens de erro
- [ ] Preencher data inicial e final
- [ ] Gerar relatório
- [ ] Verificar dados do período selecionado

### 5.5 Validação de Datas Customizadas
- [ ] Preencher data inicial > data final
- [ ] Verificar mensagem de erro

### 5.6 Resumo do Período
- [ ] Verificar alerta azul com período selecionado
- [ ] Verificar 5 cards de resumo:
  - [ ] Total de Pedidos
  - [ ] Total de Vendas (verde)
  - [ ] Total de Despesas (vermelho)
  - [ ] Lucro Líquido (azul/amarelo)
  - [ ] Ticket Médio
- [ ] Verificar valores corretos

### 5.7 Gráficos do Relatório (períodos até 31 dias)
- [ ] Selecionar "Últimos 7 dias"
- [ ] Verificar 2 gráficos:

  **Gráfico de Barras (Vendas vs Despesas)**
  - [ ] Verificar barras verdes (vendas)
  - [ ] Verificar barras vermelhas (despesas)
  - [ ] Passar mouse e verificar tooltips
  - [ ] Verificar legendas

  **Gráfico de Pizza (Distribuição de Despesas)**
  - [ ] Verificar fatias com cores diferentes
  - [ ] Passar mouse e verificar valores + percentuais
  - [ ] Verificar legenda na parte inferior

### 5.8 Gráficos em Períodos Longos
- [ ] Selecionar período > 31 dias (ex: "Últimos 30 dias" é ok, mas testar com datas customizadas > 31)
- [ ] Verificar que gráficos NÃO aparecem (limitação de performance)
- [ ] Verificar que tabelas ainda funcionam

### 5.9 Tabela de Despesas por Categoria
- [ ] Verificar tabela com 3 colunas:
  - [ ] Categoria
  - [ ] Total (R$)
  - [ ] % do Total
- [ ] Verificar cálculo de percentuais
- [ ] Verificar ordenação por total (maior primeiro)

### 5.10 Fechamentos do Período (MOBILE)
- [ ] Redimensionar para 390px
- [ ] Verificar cards de fechamentos
- [ ] Verificar botão "Editar" em cada card

### 5.11 Fechamentos do Período (DESKTOP)
- [ ] Verificar tabela com 8 colunas
- [ ] Verificar link para editar cada fechamento

### 5.12 Despesas do Período (MOBILE)
- [ ] Verificar cards de despesas
- [ ] Verificar dados completos

### 5.13 Despesas do Período (DESKTOP)
- [ ] Verificar tabela com 5 colunas
- [ ] Verificar descrições truncadas

### 5.14 Mensagem de Sem Dados
- [ ] Selecionar período sem dados (ex: data futura)
- [ ] Verificar alerta: "Nenhum dado encontrado para o período selecionado."

---

## 6. TESTES DE NAVEGAÇÃO

### 6.1 Navbar (MOBILE - 390px)
- [ ] Verificar navbar fixa no topo
- [ ] Verificar ícone de hambúrguer (3 linhas)
- [ ] Clicar no hambúrguer
- [ ] Verificar menu expansível com:
  - [ ] Dashboard
  - [ ] Relatórios
  - [ ] Fechamentos
  - [ ] Despesas
  - [ ] Dropdown do usuário (nome + ícone)
- [ ] Clicar em cada link e verificar navegação
- [ ] Verificar que menu fecha após clicar

### 6.2 Navbar (DESKTOP - >992px)
- [ ] Verificar todos os links visíveis horizontalmente
- [ ] Verificar dropdown do usuário à direita
- [ ] Passar mouse sobre dropdown
- [ ] Verificar opções:
  - [ ] Admin (se superuser)
  - [ ] Sair

### 6.3 Logo/Título
- [ ] Clicar em "Gestão Financeira" (logo)
- [ ] Verificar redirecionamento para /dashboard/

---

## 7. TESTES DE RESPONSIVIDADE

### 7.1 Mobile (390px) - iPhone 12 Pro
- [ ] Abrir DevTools (F12)
- [ ] Selecionar "Responsive" ou dispositivo específico
- [ ] Configurar 390px de largura
- [ ] Navegar por todas as páginas:
  - [ ] Dashboard
  - [ ] Fechamentos (lista, criar, editar)
  - [ ] Despesas (lista, criar, editar)
  - [ ] Relatórios
- [ ] Verificar que:
  - [ ] Texto é legível (mínimo 16px)
  - [ ] Botões têm mínimo 48px de altura
  - [ ] Cards se empilham verticalmente
  - [ ] Tabelas viram cards
  - [ ] Gráficos são responsivos (300px altura)
  - [ ] Não há scroll horizontal
  - [ ] Formulários são fáceis de preencher

### 7.2 Tablet (768px) - iPad
- [ ] Configurar 768px
- [ ] Repetir navegação
- [ ] Verificar layout intermediário
- [ ] Verificar que algumas coisas já aparecem em grid (2 colunas)

### 7.3 Desktop (1920px)
- [ ] Configurar tela grande
- [ ] Verificar:
  - [ ] Cards em grid (3-5 colunas)
  - [ ] Tabelas completas (não cards)
  - [ ] Gráficos maiores (350px altura)
  - [ ] Navbar horizontal completa
  - [ ] Bom uso do espaço

### 7.4 Testes de Touch
- [ ] Usar mouse para simular touch
- [ ] Verificar que todos os botões são clicáveis
- [ ] Verificar espaçamento entre botões
- [ ] Verificar que não há elementos muito pequenos

---

## 8. TESTES DE MENSAGENS

### 8.1 Mensagens de Sucesso
- [ ] Criar um fechamento
- [ ] Verificar mensagem verde no topo direito
- [ ] Verificar que mensagem desaparece após alguns segundos
- [ ] Ou clicar no X para fechar

### 8.2 Mensagens de Erro
- [ ] Tentar criar fechamento duplicado
- [ ] Verificar mensagem vermelha
- [ ] Verificar X para fechar

### 8.3 Posicionamento (MOBILE)
- [ ] Verificar que mensagens não bloqueiam conteúdo importante
- [ ] Verificar max-width 90%

### 8.4 Posicionamento (DESKTOP)
- [ ] Verificar mensagens no canto superior direito
- [ ] Verificar max-width 400px

---

## 9. TESTES DE PERFORMANCE E CARGA

### 9.1 Paginação
- [ ] Criar mais de 20 fechamentos
- [ ] Verificar que lista pagina
- [ ] Navegar entre páginas
- [ ] Verificar controles de paginação

### 9.2 Gráficos com Muitos Dados
- [ ] Criar fechamentos para 30 dias consecutivos
- [ ] Acessar dashboard
- [ ] Verificar que gráfico de 7 dias carrega rápido
- [ ] Acessar relatórios com período de 30 dias
- [ ] Verificar que gráficos carregam sem travar

---

## 10. TESTES DE DADOS

### 10.1 Cálculos Corretos
- [ ] Criar fechamento com:
  - Dinheiro: R$ 100,00
  - PIX: R$ 200,00
  - Cartão: R$ 300,00
  - Pedidos: 10
- [ ] Verificar que:
  - [ ] Total de vendas = R$ 600,00
  - [ ] Ticket médio = R$ 60,00

### 10.2 Cálculos de Período
- [ ] Criar 3 fechamentos em dias diferentes
- [ ] Criar despesas nos mesmos dias
- [ ] Acessar dashboard
- [ ] Verificar que:
  - [ ] Soma de vendas está correta
  - [ ] Soma de despesas está correta
  - [ ] Lucro = vendas - despesas

### 10.3 Percentuais em Gráficos
- [ ] Criar despesas em 3 categorias diferentes
  - Categoria A: R$ 100,00
  - Categoria B: R$ 200,00
  - Categoria C: R$ 700,00
- [ ] Total = R$ 1000,00
- [ ] Verificar no gráfico/tabela:
  - [ ] A = 10%
  - [ ] B = 20%
  - [ ] C = 70%

---

## 11. TESTES DE SEGURANÇA

### 11.1 Proteção de Rotas
- [ ] Fazer logout
- [ ] Tentar acessar diretamente:
  - [ ] /dashboard/
  - [ ] /closings/
  - [ ] /expenses/
  - [ ] /reports/
- [ ] Verificar redirecionamento para login

### 11.2 Exclusão Restrita
- [ ] Logar com usuário comum (não superuser)
- [ ] Verificar que botões "Excluir" NÃO aparecem
- [ ] Logar com superuser
- [ ] Verificar que botões "Excluir" aparecem

### 11.3 Admin Restrito
- [ ] Logar com usuário comum
- [ ] Verificar que link "Admin" NÃO aparece no dropdown
- [ ] Logar com superuser
- [ ] Verificar que link "Admin" aparece

---

## 12. TESTES DE FORMULÁRIOS

### 12.1 Campos Obrigatórios
- [ ] Tentar submeter formulário sem preencher campos obrigatórios
- [ ] Verificar validação HTML5 (required)
- [ ] Verificar mensagens do navegador

### 12.2 Tipos de Input
- [ ] Campo de data: verificar calendário do navegador
- [ ] Campo numérico: verificar step (0.01)
- [ ] Campo numérico: tentar digitar letras
- [ ] Textarea: verificar contador de caracteres (se houver)

### 12.3 Placeholder e Labels
- [ ] Verificar que todos os campos têm labels
- [ ] Verificar placeholders úteis
- [ ] Verificar tradução em português

---

## 13. TESTES VISUAIS

### 13.1 Cores
- [ ] Verde para vendas/sucesso
- [ ] Vermelho para despesas/perigo
- [ ] Azul para lucro positivo/primário
- [ ] Amarelo para lucro negativo/aviso
- [ ] Cores consistentes em todas as páginas

### 13.2 Ícones Bootstrap Icons
- [ ] Verificar ícones carregando corretamente
- [ ] Dashboard: bi-speedometer2
- [ ] Relatórios: bi-file-earmark-bar-graph
- [ ] Fechamentos: bi-calendar-check
- [ ] Despesas: bi-receipt
- [ ] Gráficos: bi-graph-up, bi-pie-chart, bi-bar-chart

### 13.3 Tipografia
- [ ] Verificar fonte legível
- [ ] Verificar tamanhos hierárquicos (h1 > h2 > h3 > p)
- [ ] Verificar peso adequado (bold em valores importantes)

---

## 14. TESTES DE ACESSIBILIDADE

### 14.1 Contraste
- [ ] Verificar contraste de texto (mínimo 4.5:1)
- [ ] Testar em modo de alto contraste do OS

### 14.2 Navegação por Teclado
- [ ] Usar apenas TAB para navegar
- [ ] Verificar que todos os elementos interativos são acessíveis
- [ ] Verificar ordem lógica de tabulação
- [ ] Usar ENTER/SPACE para ativar botões
- [ ] Verificar indicadores de foco visíveis

### 14.3 Labels
- [ ] Verificar que todos os inputs têm labels associados
- [ ] Usar leitor de tela (se disponível) para testar

---

## RESUMO DE CHECKLIST RÁPIDO

### Setup Inicial
- [ ] Servidor Django rodando
- [ ] Migrações aplicadas
- [ ] Superusuário criado
- [ ] Categorias de despesas criadas (10 padrão)

### Funcionalidades Core
- [ ] Login/Logout funcionando
- [ ] Dashboard com métricas corretas
- [ ] CRUD de Fechamentos completo
- [ ] CRUD de Despesas completo
- [ ] Relatórios com filtros funcionando
- [ ] Gráficos renderizando

### Responsividade
- [ ] Mobile 390px OK
- [ ] Tablet 768px OK
- [ ] Desktop 1920px OK

### Validações
- [ ] Datas futuras bloqueadas
- [ ] Fechamentos duplicados bloqueados
- [ ] Valores negativos bloqueados
- [ ] Filtros de data validados

### Gráficos
- [ ] 4 gráficos funcionando (2 no dashboard, 2 nos relatórios)
- [ ] Tooltips mostrando valores
- [ ] Cores consistentes
- [ ] Responsivos

---

## Problemas Comuns e Soluções

### Gráficos não aparecem
- Verificar console do navegador (F12)
- Verificar se Chart.js carregou (ver aba Network)
- Verificar se há dados para exibir

### Estilos quebrados
- Verificar se Bootstrap CDN carregou
- Limpar cache do navegador (Ctrl+Shift+R)

### Validações não funcionam
- Verificar console para erros JavaScript
- Verificar mensagens de erro do Django

### Páginas lentas
- Verificar quantidade de dados
- Verificar se queries estão otimizadas (select_related)

---

**Data do documento:** 2026-06-21
**Versão do sistema:** Fase 8 completa
**Próxima fase:** Fase 9 - Responsividade e UX
