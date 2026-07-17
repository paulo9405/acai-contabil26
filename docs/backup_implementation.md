# Documentação Técnica — Backup Automático do Banco para o Google Drive

**Projeto:** Açaí da Rose — Sistema de Gestão Financeira
**Data de implementação:** 2026-07-17
**Responsável:** Paulo Gomes

---

## 1. Objetivo da implementação

O sistema roda em produção no **Render** (plano gratuito) com banco de dados **Neon** (PostgreSQL serverless gerenciado). Ambos possuem restrições que inviabilizam backup local tradicional:

- O Render no plano gratuito tem filesystem **efêmero** — qualquer arquivo gravado em disco some no próximo deploy ou reinício. Não há cron jobs disponíveis nesse plano.
- O Neon no plano gratuito oferece PITR (Point-in-Time Recovery) com retenção de apenas algumas horas a 1 dia, e não gera cópias no Google Drive do desenvolvedor.
- Não há servidor dedicado sempre ligado onde um `cron` convencional pudesse rodar.

**O problema:** sem backup independente, uma corrupção de dados, exclusão acidental ou encerramento do serviço no Neon/Render poderia resultar em perda total do histórico financeiro da loja — sem possibilidade de recuperação.

**A solução implementada:** backup diário automatizado via **GitHub Actions**, que:
1. Conecta diretamente ao banco Neon via `pg_dump`
2. Comprime o dump com `gzip`
3. Envia para o Google Drive pessoal do Paulo via `rclone`
4. Mantém os 15 backups mais recentes com rotação automática
5. Gera um resumo visual em cada execução
6. Funciona 24/7 sem depender do notebook do Paulo estar ligado

---

## 2. Arquitetura final

```
Desenvolvedor (Paulo)
        │
        │  git push
        ▼
   GitHub (repo público: paulo9405/acai-contabil26)
        │
        ├──────────────────────────────────────┐
        │  Render (trigger automático via push)│
        │  ↓                                   │
        │  build.sh (pip install, migrate...)  │
        │  ↓                                   │
        │  Aplicação Django (gunicorn)          │
        │  ↓                                   │
        │  Neon (PostgreSQL 18.4) ◄────────────┘
        │  endpoint com pooler (app)
        │  endpoint direto (pg_dump)
        │
        │  GitHub Actions (cron: 0 6 * * *)
        │  todo dia 06:00 UTC = 03:00 BRT
        ▼
   Runner ubuntu-latest (efêmero)
        │
        ├─ checkout do código
        ├─ instala postgresql-client-18 (PGDG)
        ├─ pg_dump (endpoint direto Neon) → SQL puro
        ├─ gzip → acai_backup_YYYY-MM-DD_HHMMSS.sql.gz
        ├─ valida: arquivo existe e tamanho > 0
        ├─ instala rclone
        ├─ configura rclone (via secret RCLONE_CONFIG)
        ├─ rclone copy → gdrive:acai-backups/
        ├─ valida: arquivo encontrado no Drive
        ├─ rotação: mantém 15 mais recentes (apaga excedentes)
        └─ gera resumo em $GITHUB_STEP_SUMMARY
                │
                ▼
        Google Drive pessoal (pasta acai-backups/)
        acai_backup_2026-07-17_014813.sql.gz
        acai_backup_2026-07-18_060000.sql.gz
        ...até 15 arquivos (os mais antigos são removidos)
```

---

## 3. Fluxo detalhado

### 3.1 Disparo do workflow

O GitHub Actions possui um agendador interno baseado em cron YAML. A expressão `0 6 * * *` instrui o GitHub a enfileirar o job todo dia às **06:00 UTC** (equivalente a 03:00 BRT). O agendamento é "best-effort" — pode atrasar alguns minutos sob carga do GitHub, mas é irrelevante para backup diário.

O workflow também aceita disparo manual via `workflow_dispatch`, acessível na aba Actions do repositório (botão "Run workflow"). Isso foi usado para os testes durante a implementação.

### 3.2 Provisionamento do runner

O GitHub provisiona uma máquina virtual `ubuntu-latest` zerada para cada execução. O runner é completamente descartado ao fim do job — nenhum arquivo persiste entre runs. O timeout do job é de 15 minutos.

### 3.3 Checkout do código

O step `actions/checkout@v4` clona o repositório para o runner, disponibilizando o arquivo `scripts/backup_database.sh`.

### 3.4 Instalação do postgresql-client-18

O runner ubuntu-latest já vem com `postgresql-client-16` instalado por padrão. Como o banco Neon roda PostgreSQL **18.4**, o `pg_dump` versão 16 rejeita a conexão com erro de "server version mismatch" (pg_dump não pode ser mais antigo que o servidor).

A instalação usa o repositório oficial **PGDG** (PostgreSQL Global Development Group):
1. Baixa e instala a chave GPG do repositório PGDG
2. Adiciona a source list `pgdg.list` apontando para o repositório ubuntu da versão do runner
3. Executa `apt-get install postgresql-client-18`
4. **Adiciona `/usr/lib/postgresql/18/bin` ao `$GITHUB_PATH`** — isso garante que todos os steps seguintes usem o `pg_dump` versão 18, não o versão 16 que já estava na PATH

Esta foi uma correção necessária descoberta na primeira tentativa: o `apt-get install` instala corretamente, mas o binário antigo da versão 16 ainda estava na frente na PATH do sistema.

### 3.5 Criação do backup (`scripts/backup_database.sh`)

O script executa com `set -euo pipefail` — qualquer comando que falhe interrompe imediatamente a execução com exit code 1.

**Passos internos do script:**

1. Gera timestamp UTC no formato `YYYY-MM-DD_HHMMSS` via `date -u`
2. Define o nome do arquivo: `acai_backup_<timestamp>.sql.gz`
3. Valida que `NEON_DATABASE_URL` está definida; aborta com mensagem de erro se não estiver
4. Executa `pg_dump "${NEON_DATABASE_URL}" | gzip > "${FILENAME}"` — o dump SQL é produzido e imediatamente comprimido via pipe, sem arquivo SQL intermediário em disco
5. Valida que o arquivo foi criado e tem tamanho maior que zero (`-s`)
6. Loga o tamanho do arquivo via `du -sh`
7. Escreve `BACKUP_FILE=<nome_do_arquivo>` em `$GITHUB_ENV` — mecanismo nativo do GitHub Actions para compartilhar variáveis de ambiente entre steps do mesmo job

A `NEON_DATABASE_URL` usada aqui é o **endpoint direto** do Neon (sem `-pooler` no hostname). O endpoint pooler usa PgBouncer e não é compatível com `pg_dump`, que precisa de conexão direta ao servidor PostgreSQL.

### 3.6 Instalação do rclone

O rclone é instalado via script oficial (`curl https://rclone.org/install.sh | sudo bash`). Não há versão fixada — usa sempre a mais recente disponível no momento do run.

### 3.7 Configuração do rclone

O secret `RCLONE_CONFIG` contém o conteúdo completo do arquivo `~/.config/rclone/rclone.conf` gerado localmente. Ele é escrito no runner em `~/.config/rclone/rclone.conf` usando a variável de ambiente `RCLONE_CONF` (para evitar que o valor apareça inline no shell, o que poderia causar problemas com caracteres especiais).

O arquivo de configuração define um remote chamado `gdrive` do tipo `drive` (Google Drive) com:
- `scope = drive.file` — o rclone só enxerga e manipula arquivos que ele mesmo criou (princípio do menor privilégio)
- `token` — JSON contendo `access_token` (curta duração) e **`refresh_token`** (longa duração). O rclone usa o refresh_token para renovar o access_token automaticamente antes de cada operação, tornando o sistema auto-sustentável sem reautenticação manual

### 3.8 Upload para o Google Drive

```bash
rclone copy "${BACKUP_FILE}" gdrive:acai-backups/
```

O rclone copia o arquivo local para a pasta `acai-backups/` no Google Drive da conta autenticada. Se a pasta não existir, é criada automaticamente. O `rclone copy` não sincroniza nem apaga destino — apenas copia o arquivo de origem.

### 3.9 Validação do upload

Após o upload, o workflow lista os arquivos da pasta remota com `rclone lsf gdrive:acai-backups/ --files-only` e procura o nome do arquivo recém-enviado com `grep -qF`. Se não for encontrado, o step falha com exit code 1, o job é marcado como falho e a rotação **não é executada** — garantindo que nunca se apague um backup antigo sem confirmar que o novo chegou.

### 3.10 Rotação automática

A rotação acontece inteiramente no Google Drive:

1. Lista todos os arquivos com `rclone lsf gdrive:acai-backups/ --files-only`
2. Conta o total com `wc -l`
3. Se `TOTAL > 15`, calcula `EXCEDENTES = TOTAL - 15`
4. Ordena alfabeticamente com `sort` — como os nomes contêm timestamp ISO (`YYYY-MM-DD_HHMMSS`), ordem alfabética = ordem cronológica
5. Pega os `EXCEDENTES` primeiros (mais antigos) com `head -n`
6. Apaga cada um com `rclone deletefile gdrive:acai-backups/<nome>`

A ordenação por nome funciona porque o formato `YYYY-MM-DD_HHMMSS` é naturalmente ordenável como string — ano antes do mês, mês antes do dia, etc.

### 3.11 Resumo do run

O step final usa `if: always()` — roda mesmo se steps anteriores falharam. Escreve um resumo Markdown em `$GITHUB_STEP_SUMMARY`, visível na aba Summary de cada run no GitHub Actions. Em caso de sucesso mostra nome do arquivo, tamanho e quantidade de backups no Drive. Em caso de falha exibe mensagem de erro.

### 3.12 Tratamento de erros

- `set -euo pipefail` no script bash: qualquer falha aborta imediatamente
- Validação explícita da variável `NEON_DATABASE_URL`
- Validação explícita do arquivo gerado (existe e não está vazio)
- Validação do upload antes de rodar a rotação
- `timeout-minutes: 15` no job: se o job travar por qualquer motivo, é cancelado automaticamente
- O step "Resumo do run" roda sempre (`if: always()`) para reportar o estado mesmo em falha
- GitHub envia e-mail automático ao dono do repositório quando um workflow falha

---

## 4. Tecnologias utilizadas

| Tecnologia | Versão / Plano | Papel |
|---|---|---|
| **Django** | 5.0.14 | Framework web da aplicação |
| **Python** | 3.12.8 | Runtime da aplicação |
| **PostgreSQL** | 18.4 (Neon) | Banco de dados em produção |
| **Neon** | Plano gratuito | PostgreSQL serverless gerenciado |
| **Render** | Plano gratuito | Hospedagem da aplicação Django |
| **GitHub** | Repositório público | Controle de versão e CI/CD |
| **GitHub Actions** | — | Orquestrador do backup (cron) |
| **GitHub Secrets** | — | Armazenamento seguro de credenciais |
| **Bash** | 5.x (ubuntu-latest) | Linguagem do script de backup |
| **pg_dump** | 18.4 (PGDG) | Ferramenta de dump do PostgreSQL |
| **gzip** | Sistema | Compressão do dump SQL |
| **rclone** | Última estável | Transferência para Google Drive |
| **Google Drive** | Conta pessoal | Destino final dos backups |
| **PGDG** | Repositório APT oficial | Fonte do postgresql-client-18 |

---

## 5. Arquivos criados

### `scripts/backup_database.sh`

Script Bash responsável exclusivamente pela criação do dump. Portátil — pode ser executado localmente (com `NEON_DATABASE_URL` definida) ou via CI. Usa `set -euo pipefail` para falhar rápido. Gera o arquivo `acai_backup_<timestamp>.sql.gz` no diretório de trabalho atual. Em ambiente GitHub Actions, exporta o caminho do arquivo via `$GITHUB_ENV`.

### `.github/workflows/backup.yml`

Workflow do GitHub Actions que orquestra todo o processo: instala dependências, executa o script, instala e configura o rclone, faz upload, valida, rotaciona e gera resumo. Ativado por cron (`0 6 * * *`) e por disparo manual (`workflow_dispatch`).

---

## 6. Arquivos modificados

### `.gitignore`

Já continha os padrões de backup antes desta implementação (adicionados previamente):
```gitignore
*.dump
*.sql
*.sql.gz
backups/
```
Isso garante que nenhum arquivo de dump seja acidentalmente versionado no repositório, mesmo que gerado localmente.

### `docs/backup_google_drive.md`

O cabeçalho foi atualizado de "documento de planejamento — nada implementado" para "✅ Implementado e validado em 2026-07-17", refletindo a conclusão da implementação.

---

## 7. GitHub Secrets

| Secret | Finalidade |
|---|---|
| `NEON_DATABASE_URL` | Connection string PostgreSQL direta do Neon (sem `-pooler`), usada pelo `pg_dump` para conectar ao banco. Inclui host, porta, usuário, senha, nome do banco e `sslmode=require`. |
| `RCLONE_CONFIG` | Conteúdo completo do arquivo `~/.config/rclone/rclone.conf` gerado localmente via `rclone config`. Contém o refresh token OAuth do Google Drive, que permite ao rclone autenticar sem interação humana. |

Nenhum dos dois secrets aparece nos logs do Actions — o GitHub mascara automaticamente valores de secrets nas saídas de log (exibidos como `***`).

---

## 8. Workflow do GitHub Actions

O arquivo `.github/workflows/backup.yml` define um job chamado `backup` com 9 steps executados sequencialmente:

| # | Step | O que faz | Falha se... |
|---|---|---|---|
| 1 | Checkout | Clona o repo para o runner | Repo inacessível |
| 2 | Instalar postgresql-client-18 | Adiciona repositório PGDG e instala pg_dump 18; adiciona ao PATH | Repositório PGDG indisponível |
| 3 | Criar backup do banco | Executa `scripts/backup_database.sh`; exporta `BACKUP_FILE` | Conexão ao Neon falha; arquivo vazio |
| 4 | Instalar rclone | Baixa e instala rclone via script oficial | Script de instalação falha |
| 5 | Configurar rclone | Escreve `RCLONE_CONFIG` em `~/.config/rclone/rclone.conf` | — |
| 6 | Enviar backup para o Drive | `rclone copy` do arquivo local para `gdrive:acai-backups/` | Drive inacessível; token expirado/revogado |
| 7 | Validar upload no Drive | `rclone lsf` confirma que o arquivo está no Drive | Arquivo não encontrado após upload |
| 8 | Rotação | Lista, ordena, apaga os mais antigos se total > 15 | Erro de permissão no Drive |
| 9 | Resumo do run | Escreve Markdown em `$GITHUB_STEP_SUMMARY` | Nunca (roda com `if: always()`) |

---

## 9. Estratégia de backup

**Periodicidade:** diária, às 06:00 UTC (03:00 BRT). Horário escolhido por ser madrugada no Brasil, quando o banco está ocioso.

**Nomenclatura:** `acai_backup_YYYY-MM-DD_HHMMSS.sql.gz`. O timestamp está em UTC. O formato ISO garante que ordenação alfabética = ordem cronológica, o que é explorado pela rotação.

**Formato do dump:** SQL puro gerado por `pg_dump` sem flags de formato especial (plain text), comprimido com `gzip` via pipe. Resultado: arquivo `.sql.gz` legível após `gunzip`. Alternativa considerada e descartada: formato custom (`-Fc`) do pg_dump — mais flexível para restore seletivo, mas requer `pg_restore` em vez de simples `psql`. Para este projeto, a simplicidade do SQL puro foi preferida.

**Compressão:** `gzip` via pipe direto da saída do `pg_dump`, sem arquivo SQL intermediário em disco. Eficiente em memória e espaço.

**Retenção:** 15 backups mais recentes, correspondendo a aproximadamente **15 dias de histórico**. Valor escolhido como balanço entre cobertura temporal e consumo de espaço no Google Drive (gratuito: 15 GB).

**Rotação:** executada no próprio Google Drive após confirmação do upload. Ordena os arquivos por nome (= ordem cronológica), mantém os 15 últimos, apaga os excedentes. A rotação nunca roda se o upload falhou.

**Destino:** pasta `acai-backups/` no Google Drive pessoal, criada automaticamente pelo rclone na primeira execução. O rclone usa escopo `drive.file`, que restringe o acesso apenas aos arquivos criados por ele — não acessa outros arquivos do Drive.

---

## 10. Como restaurar

### Pré-requisitos
- `psql` instalado localmente (versão compatível com PostgreSQL 18)
- Acesso à connection string direta do Neon (sem `-pooler`)
- rclone instalado e configurado com o remote `gdrive`

### Passo a passo

```bash
# 1. Listar backups disponíveis no Drive
rclone lsf gdrive:acai-backups/

# 2. Baixar o backup desejado (substitua pelo nome real do arquivo)
rclone copy gdrive:acai-backups/acai_backup_2026-07-17_014813.sql.gz .

# 3. Verificar integridade do arquivo comprimido
gzip -t acai_backup_2026-07-17_014813.sql.gz && echo "OK"

# 4. Restaurar no banco (substitua pela connection string real)
gunzip -c acai_backup_2026-07-17_014813.sql.gz | psql "postgresql://neondb_owner:...@ep-xxx.neon.tech/neondb?sslmode=require"
```

**Recomendação:** antes de restaurar em produção, restaurar em um **branch do Neon** (funcionalidade nativa do Neon) para validar os dados sem risco de sobrescrever dados bons.

**Atenção:** a restauração via `psql` em um banco existente pode gerar conflitos se os objetos já existirem. Para um restore limpo, considerar dropar e recriar o banco de destino antes de restaurar, ou usar um branch novo do Neon.

---

## 11. Decisões de arquitetura

**GitHub Actions em vez de servidor dedicado:**
O projeto não tem servidor sempre ligado. O Render hiberna após 15 min de inatividade e não oferece cron no plano gratuito. O notebook do Paulo estar desligado durante a madrugada inviabilizaria um cron local. O GitHub Actions é gratuito para repositórios públicos com minutos ilimitados, sempre disponível, não depende de nenhuma infraestrutura extra, e o arquivo `.yml` do workflow fica versionado no próprio repositório.

**Google Drive em vez de AWS S3, Backblaze B2 ou similar:**
O Google Drive pessoal já existe, tem 15 GB gratuitos, não exige cadastro, cartão de crédito ou configuração de IAM. Para um sistema de backup pessoal/familiar de pequeno porte, a simplicidade supera as vantagens de serviços de object storage. S3 e B2 têm custo por GB e por requisição, mesmo que pequeno.

**rclone em vez de SDK do Google Drive:**
O rclone abstrai a API do Google Drive, gerencia o token OAuth (refresh automático), trata chunked upload, validação e listagem de forma robusta e testada por milhares de usuários. Implementar isso manualmente com a API do Drive seria complexo e propenso a erros. O rclone é uma ferramenta CLI madura (Go), sem dependências de runtime.

**Escopo `drive.file` no rclone:**
Princípio do menor privilégio. O rclone com esse escopo só enxerga os arquivos que ele mesmo criou — não pode ler, modificar ou apagar outros arquivos do Drive. Reduz o impacto de um eventual vazamento do token.

**SQL puro + gzip em vez de formato custom (`-Fc`) do pg_dump:**
O formato SQL puro pode ser restaurado com `gunzip | psql`, sem ferramentas adicionais além do `psql` padrão. O formato custom exige `pg_restore`. Para um cenário de emergência onde se precisa restaurar rapidamente, a simplicidade é valiosa. O arquivo SQL também é legível em qualquer editor de texto se necessário.

**Retenção de 15 backups:**
15 dias de histórico cobrem a maioria dos cenários de recuperação (dado corrompido percebido com atraso, erro humano, etc.). Com backups de ~200 KB comprimidos, 15 arquivos ocupam menos de 3 MB no Drive — irrelevante para o plano gratuito de 15 GB.

**Endpoint direto do Neon (sem `-pooler`):**
O Neon oferece dois endpoints: o pooler (via PgBouncer, ideal para conexões de curta duração da aplicação web) e o direto (conexão ao servidor PostgreSQL real). O `pg_dump` exige conexão direta pois usa features do protocolo PostgreSQL incompatíveis com PgBouncer (como `COPY TO STDOUT` e múltiplas transações de leitura).

**PGDG em vez do postgresql-client padrão do Ubuntu:**
O repositório PGDG tem sempre a versão mais recente do PostgreSQL. O Ubuntu 24.04 (base do runner ubuntu-latest) só oferece postgresql-client-16 por padrão. Como o Neon usa PostgreSQL 18.4, é obrigatório instalar o pg_dump versão 18 do PGDG.

---

## 12. Custos

| Componente | Custo | Motivo |
|---|---|---|
| GitHub Actions (repo público) | **Gratuito** | Minutos ilimitados em repos públicos |
| GitHub Secrets | **Gratuito** | Incluído em todos os planos |
| Neon (plano free) | **Gratuito** | Banco de produção já existente |
| Render (plano free) | **Gratuito** | Hospedagem da app já existente |
| Google Drive (15 GB) | **Gratuito** | Conta pessoal já existente |
| rclone | **Gratuito** | Open source |
| pg_dump / gzip | **Gratuito** | Ferramentas do sistema |

**Custo total da solução: R$ 0,00.**

A arquitetura foi escolhida intencionalmente para ser totalmente gratuita e adequada à realidade de um sistema de pequeno porte para um negócio familiar. Toda a infraestrutura reutiliza recursos já existentes (conta Google, repositório GitHub, banco Neon).

---

## 13. Melhorias futuras

**Segurança:**
- Criptografia do arquivo antes do upload com `gpg` ou `rclone crypt`, para que mesmo com acesso ao Drive os dados estejam protegidos
- Rotação automática do token OAuth do Google (hoje requer intervenção manual se o token for revogado, ex.: troca de senha Google)

**Resiliência:**
- Segunda cópia em destino diferente (Backblaze B2, MEGA, OneDrive) — regra 3-2-1 de backup: 3 cópias, 2 mídias diferentes, 1 off-site
- Backup nativo do Neon (branch/PITR) como camada extra, complementar ao Drive
- Dead man's switch: se o backup não rodar por 2 dias consecutivos, enviar alerta (ex.: healthchecks.io)

**Observabilidade:**
- Notificação no WhatsApp ou Telegram em caso de falha (via webhook no step de erro)
- Dashboard simples mostrando histórico de runs (tamanho do backup ao longo do tempo, tendência de crescimento do banco)

**Validação automática:**
- Teste de restauração periódico: criar um branch do Neon, restaurar o backup nele, executar queries básicas para validar integridade, destruir o branch. "Backup não testado não é backup."
- Verificação de integridade do `.sql.gz` após download com `gzip -t`

**Flexibilidade:**
- Parâmetro configurável de retenção (hoje hardcoded em 15)
- Suporte a backup semanal além do diário, com retenção separada
- Versão fixada do rclone no workflow para garantir reprodutibilidade

---

## 14. Lições aprendidas

**Versão do pg_dump importa criticamente.**
O pg_dump não pode ser mais antigo que o servidor. O runner ubuntu-latest tinha pg_dump 16 instalado por padrão, mas o Neon roda PostgreSQL 18.4. Isso causou falha na primeira tentativa. A solução foi instalar o postgresql-client-18 do PGDG e, crucialmente, adicionar o binário correto ao `$GITHUB_PATH` — não basta instalar, é preciso garantir que o PATH aponte para a versão certa.

**Endpoint direto vs. pooler no Neon.**
A connection string para a aplicação web usa o endpoint com `-pooler` (via PgBouncer), que é mais eficiente para múltiplas conexões curtas. Mas o `pg_dump` requer conexão direta. Usar a URL errada resultou em "password authentication failed" porque o PgBouncer tem regras de autenticação diferentes. Sempre ter os dois endpoints anotados separadamente.

**GitHub Secrets com conteúdo multiline.**
Colar o `rclone.conf` na interface web do GitHub falhou silenciosamente. A solução mais confiável foi usar o GitHub CLI (`gh secret set < arquivo`), que lida corretamente com conteúdo multiline e caracteres especiais.

**Validar antes de rotacionar.**
A ordem correta é: upload → validar → rotacionar. Rotacionar antes de confirmar o upload poderia apagar o backup mais antigo sem garantia de que o novo chegou. O step de validação (`rclone lsf | grep`) garante essa sequência de forma explícita.

**`$GITHUB_PATH` vs PATH local.**
Adicionar ao PATH dentro de um step (`export PATH=...`) não persiste para o próximo step no GitHub Actions. O mecanismo correto é escrever em `$GITHUB_PATH` (arquivo de ambiente do runner), que é carregado automaticamente antes de cada step subsequente.

**Runners são efêmeros — design para isso.**
Nenhum arquivo, cache ou configuração persiste entre runs. Toda configuração necessária (rclone, pg_dump, secrets) precisa ser reconstituída do zero a cada execução. Isso é uma restrição, mas também uma vantagem: cada run parte de um estado limpo e reprodutível.
