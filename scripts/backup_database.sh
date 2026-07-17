#!/usr/bin/env bash
# Cria um dump comprimido do banco Neon e exporta o caminho para o GitHub Actions.
#
# Uso local:
#   NEON_DATABASE_URL="postgresql://user:pass@host/db" bash scripts/backup_database.sh
#
# Uso CI:
#   Chamado pelo workflow .github/workflows/backup.yml
#   A variável NEON_DATABASE_URL deve apontar para o endpoint DIRETO do Neon
#   (sem -pooler) — obrigatório para pg_dump.
#
# Formato: SQL puro comprimido com gzip (.sql.gz)
#   Restore: gunzip -c arquivo.sql.gz | psql "<NEON_DIRECT_URL>"

set -euo pipefail

TIMESTAMP=$(date -u +"%Y-%m-%d_%H%M%S")
FILENAME="acai_backup_${TIMESTAMP}.sql.gz"

echo "==> Iniciando backup: ${FILENAME}"

if [[ -z "${NEON_DATABASE_URL:-}" ]]; then
    echo "ERRO: variável NEON_DATABASE_URL não definida." >&2
    echo "      Defina-a com o endpoint direto do Neon (sem -pooler)." >&2
    exit 1
fi

pg_dump "${NEON_DATABASE_URL}" | gzip > "${FILENAME}"

if [[ ! -s "${FILENAME}" ]]; then
    echo "ERRO: ${FILENAME} não foi criado ou está vazio." >&2
    exit 1
fi

SIZE=$(du -sh "${FILENAME}" | cut -f1)
echo "==> Backup criado com sucesso: ${FILENAME} (${SIZE})"

# Exporta o caminho do arquivo para o GitHub Actions (ignorado localmente)
if [[ -n "${GITHUB_ENV:-}" ]]; then
    echo "BACKUP_FILE=${FILENAME}" >> "${GITHUB_ENV}"
fi
