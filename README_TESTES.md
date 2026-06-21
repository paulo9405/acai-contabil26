# Guia Rápido de Testes

## 🚀 Comandos Essenciais

### Limpar TUDO (sem recriar)
```bash
./limpar.sh
```
ou
```bash
python manage.py limpar_dados
```

### Resetar e Recriar Dados Automaticamente
```bash
./reset_db.sh
```

Isso irá:
1. ✅ Limpar todos os dados
2. ✅ Criar usuário admin/admin123
3. ✅ Criar 30 dias de fechamentos
4. ✅ Criar 90 despesas (3/dia)

### Criar Dados Manualmente (Interativo)
```bash
python criar_dados_teste.py
```

---

## 📋 Solução para seu Problema Atual

Você está vendo erro de **"Já existe um fechamento para [data]"** porque o banco já tem dados nessas datas.

### Solução em 2 comandos:

```bash
# 1. Limpar tudo
./limpar.sh

# 2. Iniciar servidor e criar manualmente
python manage.py runserver
```

Agora TODAS as datas estarão livres para você testar a criação manual! ✅

---

## 🎯 Cenários de Teste

### Cenário 1: Testar com Banco Vazio
```bash
./limpar.sh
python manage.py runserver
```
- Dashboard vazio (empty states)
- Criar primeiro fechamento
- Criar primeira despesa
- Ver gráficos populando

### Cenário 2: Testar com Dados Completos
```bash
./reset_db.sh
python manage.py runserver
```
- Dashboard com gráficos
- Listas com paginação
- Filtros com resultados
- Relatórios de 30 dias

### Cenário 3: Testar Período Específico
```bash
./limpar.sh
python criar_dados_teste.py
# Escolher datas específicas
python manage.py runserver
```

---

## 🔍 Ver Dados Existentes

```bash
python manage.py shell
```

```python
from finance.models import DailyClosing

# Ver fechamentos existentes
for f in DailyClosing.objects.all().order_by('-date')[:10]:
    print(f"{f.date} - R$ {f.total_sales}")
```

---

## ⚠️ Erros Comuns

### "Já existe um fechamento para..."
**Solução:** `./limpar.sh`

### "No module named django"
**Solução:** `source venv/bin/activate`

### "ModuleNotFoundError"
**Solução:** `pip install -r requirements.txt`

---

## 📊 Dados Criados pelo reset_db.sh

- **Usuário:** admin / admin123
- **Fechamentos:** 30 (últimos 30 dias)
- **Despesas:** 90 (3 por dia)
- **Vendas totais:** ~R$ 15.000
- **Despesas totais:** ~R$ 4.000
- **Lucro:** ~R$ 11.000

---

## 🎨 Testes de UX (Fase 9)

Após resetar dados, teste:

1. **Empty States**
   - `./limpar.sh` → Ver mensagens vazias bonitas

2. **Loading States**
   - Criar fechamento → Ver spinner no botão

3. **Confirmações**
   - Tentar excluir → Ver confirmação

4. **Breadcrumbs**
   - Navegar criar/editar → Ver navegação

5. **Mobile**
   - DevTools 390px → Testar touch targets

---

**Pronto! Use os scripts acima para facilitar seus testes.** 🚀
