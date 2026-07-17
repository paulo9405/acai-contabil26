# ROADMAP — Backup Automático do Banco para o Google Drive (Açaí)

> **Status:** ✅ Implementado e validado em 2026-07-17.
> Backup diário ativo via GitHub Actions. Primeiro backup confirmado no Google Drive.
>
> **Base:** adaptado do roadmap original do projeto *Nícia Track*
> (`docs/backup_google_drive.md` copiado de lá). O Nícia Track assumia
> **PostgreSQL em Docker + EC2 (servidor sempre ligado)**. **Este projeto NÃO tem
> essa arquitetura** — por isso o roadmap foi reescrito para a stack real do açaí.

---

## 0. Contexto e diferença crucial em relação ao Nícia Track

| Item | Nícia Track (doc original) | Açaí (este projeto) |
|------|---------------------------|---------------------|
| Banco | PostgreSQL em container Docker | **Neon** (PostgreSQL serverless gerenciado) |
| Hospedagem app | EC2 (servidor sempre ligado) | **Render** (web service free) |
| Onde rodava o cron | No próprio EC2 | ❌ Não há servidor pra isso |
| Disco pra `backups/` | Volume Docker no EC2 | ❌ Render tem filesystem **efêmero** |
| Ferramenta de agendamento | `cron` do Linux no servidor | **GitHub Actions** (cron na nuvem) |
| Upload pro Drive | `rclone` instalado no EC2 | `rclone` dentro do runner do GitHub Actions |

**Por que o cenário do Nícia Track não se aplica aqui:**

- O **Render (free)** hiberna após 15 min de inatividade, tem filesystem
  efêmero (qualquer arquivo salvo some no próximo deploy/restart) e **não
  oferece cron jobs** no plano free. Ou seja, não dá pra hospedar o script de
  backup nele.
- O **Neon (free)** é um Postgres gerenciado. Ele tem PITR/branching próprio,
  mas a retenção de histórico no plano free é curta (~6h a 1 dia) e **não gera
  cópia no seu Google Drive** — que é exatamente o que você quer.
- Não existe mais "servidor sempre ligado" onde colocar `cron + rclone + pasta local`.

**Decisão de arquitetura (já tomada):** o backup roda como um
**workflow agendado no GitHub Actions**. É gratuito, está sempre disponível
(não depende do seu notebook estar ligado), e é a escolha "cloud-native" natural
para uma stack Render + Neon. Bônus: é ótimo material de estudo/entrevista
(CI/CD, secrets, cron, OAuth).

---

## Objetivo

Ter um sistema de backup do banco **Neon** que seja simples, seguro, automatizado
e de custo praticamente zero, enviando automaticamente uma cópia comprimida para
a **minha conta pessoal do Google Drive**, com rotação automática (manter apenas
os N backups mais recentes).

Frequência desejada: **diária** (recomendado) ou **semanal** — configurável em
uma única linha (`cron`).

**Importante:** não implementar imediatamente. Este documento é o plano. A
implementação só começa após revisão/aprovação, e será feita fase a fase.

---

## Arquitetura-alvo (fluxo completo)

```
┌─────────────────────────────────────────────────────────────┐
│  GitHub Actions (runner ubuntu-latest, agendado por cron)    │
│                                                              │
│  1. Instala postgresql-client (versão compatível c/ Neon)    │
│  2. pg_dump  ──conecta──▶  Neon (via secret NEON_DATABASE_URL)│
│  3. gzip  ▶  acai_backup_AAAA-MM-DD_HHMMSS.sql.gz            │
│  4. Valida: arquivo existe e tamanho > 0                     │
│  5. Configura rclone (via secret RCLONE_CONFIG)             │
│  6. rclone copy  ─────────▶  Google Drive (pasta acai-backups)│
│  7. Valida upload (rclone lsf confirma presença)            │
│  8. Rotação: mantém só os 15 mais recentes no Drive         │
│  9. Log no resumo do run (+ notificação opcional em falha)   │
└─────────────────────────────────────────────────────────────┘
```

Nada é persistido no runner — ele é descartado ao fim do job. A única cópia
durável vive no **Google Drive**.

---

## FASE 0 — Documento de estudo (living doc)

Assim como no roadmap original, além **deste** roadmap será criado/atualizado um
documento de acompanhamento:

```
docs/backup_implementation.md
```

Esse arquivo será atualizado **a cada fase concluída**, registrando de forma
didática:

- o que foi implementado e por quê;
- alternativas consideradas e por que a escolhida venceu;
- arquivos criados/modificados;
- comandos importantes;
- problemas encontrados e como foram resolvidos;
- conceitos relevantes (Neon/Postgres, GitHub Actions, cron, rclone, OAuth, secrets);
- perguntas de entrevista relacionadas + respostas sugeridas.

Objetivo final: que o `backup_implementation.md` conte toda a história da
construção e sirva como material de estudo.

---

## FASE 1 — Estudo da infraestrutura atual (resumo já levantado)

Levantamento já feito durante o planejamento (confirmar antes de implementar):

- **App:** Django 5.0.14, `gunicorn`, deploy no Render via `render.yaml` +
  `build.sh`. Banco configurado por `DATABASE_URL` (parseada por
  `dj_database_url` em `gestao_financeira/settings.py`).
- **Banco:** migrado para o **Neon** (projeto "acai", região AWS US East 1).
  Connection string usa `-pooler` para a app; para `pg_dump`/`pg_restore`
  usar o endpoint **direto** (sem `-pooler`).
- **Tabelas:** 21 tabelas (Django auth/admin/sessions + apps `orders_*` e
  `finance_*`). Backup completo hoje ≈ 156 KB comprimido — volume pequeno.
- **Ferramentas locais:** `pg_dump`/`psql` 18.4 disponíveis; `rclone` **ainda
  não instalado** localmente (não é necessário pra abordagem GitHub Actions).
- **Repo:** ainda **não** há `.github/workflows/` nem pasta `scripts/`.

> ⚠️ **Pendência de segurança já detectada:** o arquivo `backup_atual.dump`
> (gerado na migração) contém **dados reais** e o `.gitignore` atual só ignora
> `.env`/`.env.local`. Antes de qualquer commit, adicionar padrões de backup ao
> `.gitignore` (ver Fase 3) e garantir que nenhum `.dump`/`.sql.gz` seja
> versionado.

**Confirmar antes de implementar:**
1. O repositório do açaí é **público ou privado** no GitHub?
   (Público = minutos de Actions ilimitados; privado = cota grátis de 2.000 min/mês,
   mais que suficiente para um backup diário.)
2. Qual a **versão exata do PostgreSQL no Neon** (para instalar o
   `postgresql-client` compatível no runner)? — checar no Neon Console.

---

## FASE 2 — Planejamento e decisão técnica

**Solução escolhida:** GitHub Actions (workflow agendado) + `pg_dump` + `gzip`
+ `rclone` → Google Drive.

**Vantagens:**
- Custo zero (dentro da cota grátis do Actions; Drive pessoal já existe).
- Sempre disponível — não depende do notebook do Paulo estar ligado.
- Secrets nativos e criptografados no GitHub (nada de senha em texto puro).
- Versionável: o `.yml` do workflow fica no próprio repo, com histórico.
- Ótimo valor de aprendizado (CI/CD, cron, OAuth, gestão de secrets).

**Riscos e mitigação:**
- *Agendamento "best-effort":* o cron do GitHub Actions pode atrasar alguns
  minutos sob carga. Irrelevante para backup diário.
- *Versão do `pg_dump` < servidor:* causa erro. Mitigação: instalar
  `postgresql-client` do repositório oficial PGDG, casando com a versão do Neon.
- *Token do Drive expira/revoga:* o `rclone` guarda **refresh token**, então
  renova sozinho. Documentar como regerar caso o Paulo troque a senha do Google.
- *Vazamento de segredo:* nunca logar a connection string; usar `secrets`.

**Alternativas consideradas (e por que não):**
- *Cron no notebook do Paulo:* simples, mas só roda com a máquina ligada — risco
  de pular dias. Descartado como solução principal.
- *Backup nativo do Neon (PITR/branch):* bom como camada extra, mas free tier
  retém pouco e não cria cópia no Drive. Não atende o pedido sozinho.
- *Render Cron Job:* indisponível no plano free.

---

## FASE 3 — Estrutura de diretórios

Estrutura proposta (mínima, sem pasta `backups/` local — o backup vive no runner
efêmero e no Drive):

```
.github/
  workflows/
    backup.yml          # workflow agendado (o coração da solução)

scripts/
  backup_database.sh    # script chamado pelo workflow (reutilizável localmente)

docs/
  backup_google_drive.md      # este roadmap
  backup_implementation.md     # living doc (Fase 0)
```

Ajustar `.gitignore` para **nunca** versionar dumps:

```gitignore
# Backups do banco (nunca versionar — contêm dados reais)
*.dump
*.sql
*.sql.gz
backups/
```

> Manter o script em `scripts/backup_database.sh` (e o workflow só o invoca)
> permite também rodar o backup manualmente na máquina local quando quiser,
> reaproveitando a mesma lógica.

---

## FASE 4 — Script de backup (`scripts/backup_database.sh`)

Requisitos do script (a implementar):

- usar `pg_dump` oficial;
- ler a connection string **exclusivamente** de variável de ambiente
  (`NEON_DATABASE_URL`) — nunca hardcode;
- usar o endpoint **direto** do Neon (sem `-pooler`);
- gerar dump completo (formato custom `-Fc` **ou** SQL puro + gzip — decidir na
  implementação; `-Fc` já é comprimido e mais flexível pro `pg_restore`);
- nome do arquivo com data/hora: `acai_backup_AAAA-MM-DD_HHMMSS.sql.gz`;
- validar que o arquivo foi criado e tem **tamanho > 0**;
- `set -euo pipefail` — abortar em qualquer erro;
- mensagens claras de sucesso/erro e **exit codes** apropriados;
- comentários explicando cada etapa.

> **Nota sobre formato:** `-Fc` (custom) já vem comprimido e permite restore
> seletivo com `pg_restore`. Se preferir SQL legível, usar `pg_dump | gzip`.
> A decisão será registrada no `backup_implementation.md`.

---

## FASE 5 — Rotação automática (manter só os 15 mais recentes)

Como não há pasta local persistente, a rotação acontece **no Google Drive**,
via `rclone`, **somente após** o upload do novo backup ser confirmado.

Estratégia (a implementar):
1. confirmar que o novo upload chegou ao Drive;
2. listar os backups na pasta remota (`rclone lsf`), ordenados por nome
   (o timestamp no nome garante ordem cronológica);
3. manter os 15 mais recentes;
4. deletar os excedentes (`rclone deletefile`).

Regra de ouro: **nunca** apagar nada antes de confirmar que o backup novo subiu.

---

## FASE 6 — Integração com Google Drive (rclone)

Ferramenta: **rclone** (dentro do runner do GitHub Actions).

Passos de configuração (feitos **uma vez**, localmente, para gerar o segredo):

1. instalar rclone localmente (`curl https://rclone.org/install.sh | sudo bash`);
2. `rclone config` → criar um remote do tipo **Google Drive** (ex.: nome `gdrive`),
   autenticando com a conta pessoal do Paulo pelo navegador;
3. escopo recomendado: `drive.file` (rclone só enxerga o que ele mesmo cria —
   princípio do menor privilégio);
4. abrir `~/.config/rclone/rclone.conf`, copiar o conteúdo (inclui o
   **refresh token**);
5. salvar esse conteúdo como **GitHub Secret** `RCLONE_CONFIG`.

No workflow, o conteúdo do secret é escrito num `rclone.conf` temporário e usado
via `rclone --config`. Assim nenhuma credencial fica no repo.

Fluxo esperado (ordem obrigatória):
1. criar backup → 2. validar → 3. enviar pro Drive → 4. confirmar upload →
5. **só então** rodar a rotação.

Se o upload falhar: **não** rodar rotação, marcar o job como falho, manter logs.

> **Alternativa (service account):** para automação "pura", pode-se usar uma
> service account JSON e compartilhar uma pasta do Drive com o e-mail dela.
> Mais robusto, porém mais passos. Para uso pessoal, o refresh token do
> `rclone config` é mais simples. Decisão registrada no living doc.

---

## FASE 7 — Logs e observabilidade

- Cada run do GitHub Actions já gera **log completo** e fica no histórico da aba
  *Actions* (início, duração, sucesso/falha por step).
- Adicionar um resumo amigável via `$GITHUB_STEP_SUMMARY` (nome do arquivo,
  tamanho, quantos backups restaram após a rotação).
- **Notificação em falha (recomendado):** e-mail automático do GitHub em workflow
  que falha (nativo), e opcionalmente um webhook (Discord/Telegram) — ver Fase 11.
- **Nunca** logar a connection string nem o conteúdo do `rclone.conf`.

---

## FASE 8 — Automação (agendamento via cron do GitHub Actions)

O agendamento fica no próprio `backup.yml`:

```yaml
on:
  workflow_dispatch:        # permite rodar manualmente (teste sob demanda)
  schedule:
    - cron: '0 6 * * *'     # todo dia às 06:00 UTC = 03:00 BRT
```

Pontos a documentar na implementação:
- **Fuso:** o cron do GitHub Actions é sempre **UTC**. Brasil = UTC−3, então
  `06:00 UTC` = `03:00` no horário de Brasília (madrugada, banco ocioso — ideal).
- **Diário vs semanal:** para semanal usar `0 6 * * 0` (domingos). Trocar é uma
  linha só.
- **Como testar sem esperar o horário:** botão *Run workflow* (graças ao
  `workflow_dispatch`) ou `gh workflow run backup.yml`.
- **Como listar/editar/remover:** o agendamento é o próprio arquivo `.yml`
  versionado — editar o cron ou remover o workflow = commit no repo.

Depois disso, nenhum comando manual é necessário no dia a dia.

---

## FASE 9 — Testes

Antes de considerar concluído, validar:
- backup criado corretamente e íntegro (`gzip -t` / `pg_restore --list`);
- **restauração real** num banco de teste (ex.: um branch do Neon) — o teste que
  mais importa: backup que não restaura não é backup;
- upload chegando no Drive;
- rotação apagando **apenas** os excedentes (nunca o backup recém-criado);
- disparo manual (`workflow_dispatch`) funcionando;
- comportamento correto em falha (upload falho → não roda rotação → job vermelho).

Registrar o resultado de cada teste no `backup_implementation.md`.

---

## FASE 10 — Como restaurar um backup (runbook)

Procedimento de restore (documentar com comandos reais na implementação):

```bash
# 1. baixar o backup do Drive (rclone copy gdrive:acai-backups/arquivo .)
# 2a. se formato custom (-Fc):
pg_restore --no-owner --no-privileges -d "<NEON_DIRECT_URL>" arquivo.dump
# 2b. se SQL + gzip:
gunzip -c arquivo.sql.gz | psql "<NEON_DIRECT_URL>"
```

Sempre restaurar usando o endpoint **direto** do Neon (sem `-pooler`) e, em
produção, de preferência para um **branch novo** antes de promover — evita
sobrescrever dados bons por engano.

---

## FASE 11 — Melhorias futuras

- **Segunda cópia** em outro destino (S3, Backblaze B2) — regra 3-2-1 de backup.
- **Criptografia** dos dumps (`rclone crypt` ou `gpg`) antes do upload.
- **Verificação automática de integridade** (restore de teste periódico agendado).
- **Notificações** em Discord/Telegram além do e-mail nativo.
- **Backup nativo do Neon** (PITR/branch) como camada extra de defesa.
- **Alerta de "backup não rodou"** (dead man's switch — ex.: healthchecks.io).

---

## Regras importantes (herdadas do roadmap original)

- Não implementar imediatamente — este é o plano.
- Ao finalizar **cada fase**, atualizar `docs/backup_implementation.md`.
- Explicar cada decisão técnica.
- Priorizar sempre: simplicidade, segurança, baixo custo, fácil manutenção.
- Nunca versionar dumps nem credenciais; tudo sensível vai em **GitHub Secrets**.

---

## Resumo dos segredos (GitHub Secrets) a criar na implementação

| Secret | Conteúdo | Origem |
|--------|----------|--------|
| `NEON_DATABASE_URL` | connection string **direta** do Neon (sem `-pooler`) | Neon Console → Connect |
| `RCLONE_CONFIG` | conteúdo de `~/.config/rclone/rclone.conf` (com refresh token) | `rclone config` local |

---

### Dúvidas em aberto para o Paulo confirmar antes de começar

1. Repositório GitHub do açaí é **público ou privado**?
2. Frequência final: **diária** (recomendado) ou **semanal**?
3. Quantos backups manter na rotação? (proposto: **15**)
4. Versão do PostgreSQL no Neon (para o `postgresql-client` do runner).
