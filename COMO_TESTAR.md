# Como Testar o Sistema Localmente

## Passo a Passo Rápido

### 1. Preparar o Ambiente

```bash
# Ativar ambiente virtual
source venv/bin/activate

# Aplicar migrations (se ainda não aplicou)
python manage.py migrate

# Criar dados de teste
python criar_dados_teste.py
```

O script irá perguntar:
- Nome de usuário (padrão: `admin`)
- Senha (padrão: `admin123`)
- Quantos dias de fechamentos (padrão: `30`)
- Quantas despesas por dia (padrão: `3`)

**Recomendação:** Aceite os padrões pressionando Enter.

---

### 2. Iniciar o Servidor

```bash
python manage.py runserver
```

Você verá algo como:
```
Starting development server at http://127.0.0.1:8000/
```

---

### 3. Acessar o Sistema

Abra seu navegador em: **http://localhost:8000**

- **Usuário:** `admin`
- **Senha:** `admin123`

---

### 4. Ordem Recomendada de Testes

#### 4.1 Primeiro Acesso (5 minutos)
1. Fazer login
2. Explorar Dashboard
3. Clicar em cada card e botão
4. Verificar gráficos

#### 4.2 Navegação Básica (5 minutos)
1. Clicar em "Relatórios" no menu
2. Testar filtros de período
3. Clicar em "Fechamentos"
4. Clicar em "Despesas"
5. Voltar ao Dashboard

#### 4.3 CRUD de Fechamentos (10 minutos)
1. Ir em "Fechamentos"
2. Clicar em "Novo Fechamento"
3. Preencher com data de hoje
4. Salvar e verificar mensagem de sucesso
5. Editar um fechamento existente
6. Tentar criar fechamento duplicado (mesmo dia) - deve dar erro

#### 4.4 CRUD de Despesas (10 minutos)
1. Ir em "Despesas"
2. Testar filtros (data inicial, data final, categoria)
3. Clicar em "Nova Despesa"
4. Preencher e salvar
5. Editar uma despesa
6. Tentar criar despesa com data futura - deve dar erro

#### 4.5 Relatórios Detalhados (15 minutos)
1. Ir em "Relatórios"
2. Testar cada período do dropdown:
   - Hoje
   - Ontem
   - Últimos 7 dias
   - Últimos 30 dias
   - Este mês
   - Mês passado
3. Testar "Personalizado":
   - Escolher datas específicas
   - Tentar gerar sem preencher datas (deve dar erro)
4. Verificar todos os gráficos

#### 4.6 Testes Mobile (10 minutos)
1. Abrir DevTools (F12)
2. Clicar no ícone de dispositivos (ou Ctrl+Shift+M)
3. Escolher "iPhone 12 Pro" ou configurar 390px
4. Navegar por todas as páginas
5. Verificar que:
   - Tabelas viram cards
   - Botões são grandes
   - Gráficos são responsivos
   - Texto é legível

---

### 5. Checklist Rápido de 5 Minutos

Use este checklist para verificar rapidamente se tudo está funcionando:

- [ ] Login funciona
- [ ] Dashboard mostra métricas
- [ ] Gráfico de linha aparece (últimos 7 dias)
- [ ] Gráfico de rosca aparece (despesas por categoria)
- [ ] Relatórios carregam
- [ ] Gráficos dos relatórios aparecem
- [ ] Consigo criar novo fechamento
- [ ] Consigo criar nova despesa
- [ ] Mensagens de sucesso aparecem
- [ ] Validações de erro funcionam (data futura, duplicado)

---

## Problemas Comuns

### "ModuleNotFoundError: No module named 'django'"
**Solução:** Ativar o ambiente virtual
```bash
source venv/bin/activate
```

### "no such table: finance_dailyclosing"
**Solução:** Aplicar migrations
```bash
python manage.py migrate
```

### Gráficos não aparecem
**Solução:**
1. Abrir DevTools (F12)
2. Ver aba Console
3. Verificar se há erros JavaScript
4. Verificar aba Network se Chart.js carregou
5. Limpar cache (Ctrl+Shift+R)

### "Nenhum dado encontrado"
**Solução:** Executar o script de dados de teste
```bash
python criar_dados_teste.py
```

### Porta 8000 já em uso
**Solução:** Usar outra porta
```bash
python manage.py runserver 8001
```

---

## Testando Recursos Específicos

### Testar Validações
```bash
# No dashboard, criar fechamento:
1. Data futura → Deve dar erro
2. Data de hoje → OK
3. Tentar criar outro do mesmo dia → Deve dar erro
4. Valor negativo → Deve dar erro (HTML5 já bloqueia)
```

### Testar Cálculos
```bash
# Criar fechamento com:
- Dinheiro: 100
- PIX: 200
- Cartão: 300
- Pedidos: 10

# Verificar:
- Total de vendas = 600
- Ticket médio = 60
```

### Testar Gráficos
```bash
# Dashboard:
1. Deve ter 2 gráficos
2. Gráfico de linha com 3 linhas coloridas
3. Gráfico de rosca com cores variadas

# Relatórios (últimos 7 dias):
1. Gráfico de barras com vendas e despesas
2. Gráfico de pizza com categorias
```

### Testar Responsividade
```bash
# DevTools → 390px (mobile)
- Cards empilhados verticalmente
- Navbar com hambúrguer
- Gráficos menores mas visíveis

# DevTools → 1920px (desktop)
- Cards em grid
- Navbar horizontal
- Gráficos maiores
- Tabelas completas
```

---

## Documentação Completa

Para lista completa de testes, consulte: **TESTES_MANUAIS.md**

---

## Dados Gerados pelo Script

O script `criar_dados_teste.py` cria:

- **1 usuário** admin/superuser
- **30 fechamentos** diários (últimos 30 dias)
- **90 despesas** (3 por dia)
- **Variação realista:** mais vendas nos fins de semana
- **10 categorias** padrão (via migrations)

### Estrutura dos Dados

**Fechamentos:**
- Dias de semana: ~15-25 pedidos
- Fins de semana: ~22-37 pedidos (50% mais)
- Vendas crescentes ao longo dos dias
- Total de vendas: ~R$ 13.500 a R$ 20.000

**Despesas:**
- Distribuídas em todas as categorias
- Valores entre R$ 20 e R$ 70
- Total de despesas: ~R$ 3.500 a R$ 5.000

**Lucro esperado:** ~R$ 10.000 a R$ 15.000

---

## Dicas de Teste

### Para Testar Performance
```bash
# Criar mais dados
python criar_dados_teste.py
# Escolher 90 dias e 10 despesas por dia
```

### Para Testar Validações
```bash
# Tentar ações inválidas:
- Data futura
- Fechamento duplicado
- Valor zero ou negativo
- Período com data inicial > final
```

### Para Testar Gráficos
```bash
# Garantir dados nos últimos 7 dias
# Os gráficos só aparecem se houver dados
```

### Para Testar Mobile
```bash
# Usar DevTools de verdade, não apenas redimensionar
# Simula touch events e viewport correto
```

---

## Próximos Passos

Após testar localmente:

1. ✅ Validar todas as funcionalidades (use TESTES_MANUAIS.md)
2. ⏭️ Fase 9: Melhorias de UX e responsividade
3. ⏭️ Fase 10: Testes automatizados (pytest)
4. ⏭️ Fase 11: Deploy no Render

---

**Boa sorte com os testes! 🚀**
