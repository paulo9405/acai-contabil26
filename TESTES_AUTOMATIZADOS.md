# Testes Automatizados - Gestão Financeira

## ✅ Cobertura Atual: 89.66%

**Meta:** 80% (ATINGIDA! ✅)

---

## 🚀 Executar Testes

### Método 1: Script Rápido
```bash
./run_tests.sh
```

### Método 2: Comando Direto
```bash
source venv/bin/activate
pytest
```

### Método 3: Com Opções
```bash
# Apenas rodar testes
pytest --no-cov

# Com cobertura detalhada
pytest -v --cov-report=term-missing

# Rodar testes específicos
pytest tests/test_models.py
pytest tests/test_services.py::TestCalculationServices

# Modo quiet (menos output)
pytest -q

# Parar no primeiro erro
pytest -x
```

---

## 📊 Estrutura de Testes

### Arquivos Criados
```
tests/
├── __init__.py
├── conftest.py          # Fixtures e factories compartilhadas
├── test_models.py       # 19 testes - Models
├── test_services.py     # 21 testes - Business logic
├── test_forms.py        # 22 testes - Validações de formulários
└── test_views.py        # 26 testes - Views e URLs

Total: 88 testes
```

### Configuração
```
pytest.ini              # Configuração do pytest
.coveragerc             # Configuração de cobertura
run_tests.sh            # Script para executar testes
```

---

## 📈 Cobertura por Arquivo

| Arquivo | Cobertura | Linhas | Faltam |
|---------|-----------|--------|--------|
| **finance/forms.py** | **100.00%** | 71 | 0 |
| **finance/urls.py** | **100.00%** | 3 | 0 |
| **gestao_financeira/urls.py** | **100.00%** | 4 | 0 |
| finance/models.py | 93.15% | 73 | 5 |
| finance/services.py | 88.89% | 144 | 16 |
| finance/views.py | 85.84% | 226 | 32 |
| **TOTAL** | **89.66%** | **522** | **54** |

---

## 🧪 Testes por Categoria

### 1. Models (19 testes)
- ✅ ExpenseCategory (4 testes)
  - Criação, unicidade, status ativo/inativo, __str__
- ✅ DailyClosing (7 testes)
  - CRUD, total_sales, average_ticket, ordenação, validações
- ✅ Expense (5 testes)
  - CRUD, relacionamentos, ordenação, protect delete
- ✅ Validations (3 testes)
  - Campos positivos, precisão decimal

### 2. Services (21 testes)
- ✅ Calculation Functions (8 testes)
  - calculate_total_sales
  - calculate_average_ticket
  - calculate_period_sales/expenses/profit/orders/avg_ticket
- ✅ Metrics Functions (3 testes)
  - get_daily_metrics
  - get_monthly_metrics
  - get_dashboard_metrics
- ✅ CRUD Functions (10 testes)
  - create/update DailyClosing
  - create/update Expense
  - create ExpenseCategory
  - Validações (duplicados, datas futuras, valores negativos)

### 3. Forms (22 testes)
- ✅ ExpenseForm (6 testes)
  - Dados válidos/inválidos
  - Validações de data e valor
  - Categorias ativas
- ✅ ExpenseFilterForm (4 testes)
  - Campos opcionais
  - Range de datas
- ✅ DailyClosingForm (5 testes)
  - Validações completas
  - Duplicação (create vs update)
- ✅ ReportFilterForm (7 testes)
  - Todos os períodos
  - Custom period com validações

### 4. Views (26 testes)
- ✅ Dashboard (3 testes)
  - Autenticação, acesso, dados
- ✅ DailyClosing Views (10 testes)
  - List, Create, Update, Delete
  - Permissões (superuser)
  - GET e POST
- ✅ Expense Views (9 testes)
  - List, Create, Update, Delete
  - Filtros, permissões
- ✅ Report View (4 testes)
  - Períodos, custom dates

---

## 🔧 Tecnologias Utilizadas

- **pytest 8.3.4** - Framework de testes
- **pytest-django 4.9.0** - Integração Django
- **pytest-cov 6.0.0** - Relatórios de cobertura
- **factory-boy 3.3.1** - Factories para criar objetos
- **faker 33.1.0** - Dados fake realistas

---

## 🎯 Fixtures Disponíveis

### Usuários
```python
@pytest.fixture
def user(db):                    # Usuário comum
def superuser(db):               # Superusuário
```

### Models
```python
@pytest.fixture
def expense_category(db):        # Categoria ativa
def inactive_expense_category(db): # Categoria inativa
def daily_closing(db):           # Fechamento único
def expense(db):                 # Despesa única
def multiple_closings(db):       # 7 dias de fechamentos
def multiple_expenses(db):       # 7 dias de despesas
```

### Clients
```python
@pytest.fixture
def api_client():                # Cliente não autenticado
def authenticated_client(user):  # Cliente autenticado
def superuser_client(superuser): # Cliente superuser
```

---

## 📝 Exemplo de Uso

### Testar um Model
```python
@pytest.mark.django_db
def test_create_closing():
    closing = DailyClosingFactory(
        order_count=20,
        cash_sales=Decimal('100.00')
    )
    assert closing.order_count == 20
```

### Testar um Service
```python
@pytest.mark.django_db
def test_calculate_total_sales(daily_closing):
    total = services.calculate_total_sales(closing=daily_closing)
    assert total > 0
```

### Testar uma View
```python
@pytest.mark.django_db
def test_dashboard_authenticated(authenticated_client):
    response = authenticated_client.get(reverse('dashboard'))
    assert response.status_code == 200
    assert 'today' in response.context
```

---

## 🐛 Debug de Testes

### Ver output do print
```bash
pytest -s  # Mostra prints
```

### Ver traceback completo
```bash
pytest --tb=long
```

### Rodar com pdb (debugger)
```bash
pytest --pdb  # Para no primeiro erro
```

### Ver testes coletados sem executar
```bash
pytest --collect-only
```

---

## 📊 Relatório HTML

Após executar `./run_tests.sh` ou `pytest`, um relatório HTML é gerado:

```bash
# Ver relatório no navegador
firefox htmlcov/index.html
# ou
google-chrome htmlcov/index.html
# ou
xdg-open htmlcov/index.html
```

O relatório mostra:
- Cobertura por arquivo
- Linhas cobertas (verde)
- Linhas não cobertas (vermelho)
- Linhas parcialmente cobertas (amarelo)

---

## ✨ Boas Práticas Implementadas

1. **Factories em vez de objetos hardcoded**
   - Usa factory-boy para criar dados de teste
   - Dados realistas com faker

2. **Fixtures reutilizáveis**
   - Configuradas em conftest.py
   - Disponíveis para todos os testes

3. **Testes isolados**
   - Cada teste usa `@pytest.mark.django_db`
   - Banco limpo entre testes (--reuse-db)

4. **Nomenclatura clara**
   - test_nome_que_descreve_o_teste
   - Classes Test*

5. **Cobertura ≥ 80%**
   - Meta: 80%
   - Atual: 89.66% ✅

6. **Fast tests**
   - --nomigrations (não roda migrations)
   - --reuse-db (reutiliza banco)

---

## 🚦 CI/CD Ready

Os testes estão prontos para integração contínua:

```yaml
# Exemplo .github/workflows/tests.yml
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest --cov-fail-under=80
```

---

## 📚 Documentação

- [pytest docs](https://docs.pytest.org/)
- [pytest-django](https://pytest-django.readthedocs.io/)
- [factory-boy](https://factoryboy.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)

---

**Fase 10 Completa! ✅**

Cobertura: **89.66%** (Meta: 80%)
Testes: **88 passando**
Falhas: **0**
