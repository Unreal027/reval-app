#!/usr/bin/env bash
# 每日备份 PostgreSQL 并保留最近 7 份
# crontab: 10 3 * * * /opt/reval-app/backend/scripts/backup_db.sh >> /var/log/reval_backup.log 2>&1
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/opt/reval-backups}"
KEEP=7
STAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"
docker compose -f /opt/reval-app/docker-compose.yml exec -T db \
  pg_dump -U "${POSTGRES_USER:-reval}" "${POSTGRES_DB:-reval}" \
  | gzip > "$BACKUP_DIR/reval_${STAMP}.sql.gz"

ls -1t "$BACKUP_DIR"/reval_*.sql.gz | tail -n +$((KEEP + 1)) | xargs -r rm -f
echo "[$(date)] backup done: reval_${STAMP}.sql.gz"
