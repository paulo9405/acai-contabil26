# 🚀 Deploy no Render - Gestão Financeira

Este guia mostra como fazer deploy da aplicação no Render.com

## 📋 Pré-requisitos

- Conta no [Render.com](https://render.com) (gratuita)
- Código no GitHub (ou GitLab/Bitbucket)
- Repositório público ou privado

---

## 🎯 Opção 1: Deploy Automático (Recomendado)

O projeto já está configurado com `render.yaml` para deploy automático.

### Passo a Passo:

1. **Push do código para GitHub**
   ```bash
   git add .
   git commit -m "Preparar deploy para Render"
   git push origin main
   ```

2. **Criar novo Web Service no Render**
   - Acesse https://dashboard.render.com
   - Clique em "New +" → "Blueprint"
   - Conecte seu repositório GitHub
   - Selecione o repositório `acai-contabil`
   - Render detectará automaticamente o `render.yaml`
   - Clique em "Apply"

3. **Configurar Variáveis de Ambiente**
   
   O Render vai criar automaticamente:
   - `DATABASE_URL` (PostgreSQL)
   - `SECRET_KEY` (gerado automaticamente)
   
   Você precisa adicionar manualmente:
   - `ALLOWED_HOSTS` = `seu-app.onrender.com,localhost`
   
   **Como adicionar:**
   - Dashboard do Render → Seu serviço → Environment
   - Adicione as variáveis listadas acima

4. **Deploy Automático**
   - O Render vai:
     - Criar banco PostgreSQL
     - Instalar dependências
     - Rodar migrations
     - Coletar arquivos estáticos
     - Iniciar o servidor com Gunicorn

5. **Aguarde o Deploy**
   - Primeira vez: ~5-10 minutos
   - Próximos deploys: ~2-3 minutos

6. **Criar Superusuário**
   
   Após deploy completo, acesse o Shell do Render:
   ```bash
   python manage.py createsuperuser
   ```

---

## 🔧 Opção 2: Deploy Manual

Se preferir configurar manualmente:

### 1. Criar PostgreSQL Database

- Dashboard → New + → PostgreSQL
- Nome: `gestao-financeira-db`
- Plan: Free
- Aguarde criação (~2 minutos)
- Copie a `Internal Database URL`

### 2. Criar Web Service

- Dashboard → New + → Web Service
- Conecte o repositório
- Configurações:
  - **Name**: gestao-financeira
  - **Runtime**: Python 3
  - **Build Command**: `./build.sh`
  - **Start Command**: `gunicorn gestao_financeira.wsgi:application`
  - **Plan**: Free

### 3. Environment Variables

Adicione em Environment:

```env
DATABASE_URL=<URL-do-PostgreSQL-criado-acima>
SECRET_KEY=<gere-uma-chave-secreta-forte>
DEBUG=False
ALLOWED_HOSTS=seu-app.onrender.com,localhost
PYTHON_VERSION=3.12.8
```

**Gerar SECRET_KEY:**
```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 4. Deploy

- Clique em "Create Web Service"
- Aguarde o build e deploy

---

## ✅ Verificação Pós-Deploy

### 1. Acessar a Aplicação

```
https://seu-app.onrender.com
```

### 2. Criar Superusuário

No Shell do Render:
```bash
python manage.py createsuperuser
```

### 3. Acessar Admin

```
https://seu-app.onrender.com/admin/
```

### 4. Testar Funcionalidades

- ✅ Login
- ✅ Dashboard
- ✅ Criar Fechamento
- ✅ Criar Despesa
- ✅ Relatórios

---

## 🔄 Deploy Contínuo

Após configuração inicial:

1. **Faça alterações no código**
   ```bash
   git add .
   git commit -m "Sua mensagem"
   git push origin main
   ```

2. **Deploy Automático**
   - Render detecta push no GitHub
   - Inicia build automaticamente
   - Deploy em ~2-3 minutos

---

## 🐛 Troubleshooting

### Erro: "Application Error"

**Verifique:**
1. Logs no Dashboard → Seu serviço → Logs
2. Variáveis de ambiente estão corretas
3. `ALLOWED_HOSTS` inclui seu domínio Render

### Erro: "Static files not found"

**Solução:**
```bash
# No Shell do Render
python manage.py collectstatic --no-input
```

### Erro: "Database connection failed"

**Verifique:**
1. DATABASE_URL está configurada
2. PostgreSQL está rodando (Dashboard → Database)
3. Internal Database URL foi usada (não External)

### Migrations não foram aplicadas

**Solução:**
```bash
# No Shell do Render
python manage.py migrate
```

### Plano Free "hiberna" após inatividade

O plano Free do Render hiberna após 15 minutos de inatividade.
- Primeira requisição após hibernação: ~30-60s
- Solução: Upgrade para plano pago ($7/mês) ou aceitar o delay

---

## 📊 Monitoramento

### Logs em Tempo Real

Dashboard → Seu serviço → Logs

### Métricas

Dashboard → Seu serviço → Metrics
- CPU usage
- Memory usage
- Response times

---

## 🔒 Segurança em Produção

### Configurações Aplicadas Automaticamente (quando DEBUG=False):

✅ `SECURE_SSL_REDIRECT = True`
✅ `SESSION_COOKIE_SECURE = True`
✅ `CSRF_COOKIE_SECURE = True`
✅ `SECURE_HSTS_SECONDS = 31536000`
✅ `SECURE_BROWSER_XSS_FILTER = True`
✅ `SECURE_CONTENT_TYPE_NOSNIFF = True`
✅ `X_FRAME_OPTIONS = DENY`

### Recomendações Adicionais:

1. **Nunca commitar .env**
   - Já está no .gitignore
   - Usar apenas Environment Variables do Render

2. **Usar HTTPS sempre**
   - Render fornece SSL gratuito
   - HTTPS é automático

3. **Backup do Banco**
   - Render Free: sem backup automático
   - Plano pago: backups diários
   - Alternativa: exportar dados periodicamente

4. **Secrets no Environment**
   - Nunca hardcode senhas
   - Usar Environment Variables

---

## 💰 Custos

### Plano Free (Atual)

**Web Service:**
- 750 horas/mês grátis
- Hiberna após 15 min inatividade
- 512 MB RAM
- Compartilhado com outros serviços

**PostgreSQL:**
- 1 GB storage
- 90 dias de dados (depois expira)
- Sem backup automático

**Total:** $0/mês

### Plano Pago (Opcional)

**Web Service Starter:** $7/mês
- Sempre ativo (sem hibernação)
- 512 MB RAM garantida

**PostgreSQL Starter:** $7/mês
- 1 GB storage
- Backups diários
- Não expira

**Total:** $14/mês

---

## 📚 Recursos

- [Render Docs](https://render.com/docs)
- [Deploy Django on Render](https://render.com/docs/deploy-django)
- [Render Free Tier](https://render.com/docs/free)
- [Blueprint Spec](https://render.com/docs/blueprint-spec)

---

## 🎉 Conclusão

Seu projeto está configurado e pronto para deploy no Render!

**Próximos Passos:**
1. Push para GitHub
2. Conectar repositório no Render
3. Aguardar deploy automático
4. Criar superusuário
5. Testar aplicação

**Dúvidas?**
- Verifique os logs no Dashboard
- Consulte o Troubleshooting acima
- Documentação oficial do Render

---

**Deploy preparado por: Claude Sonnet 4.5**
**Data:** 2026-06-21
