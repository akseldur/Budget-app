#!/bin/bash
# Kjøres periodisk via crontab på produksjonsserveren (se docs/deploy.md).
# Dumper Postgres-databasen til en komprimert fil og sletter dumper eldre enn 7 dager.
set -euo pipefail

APP_DIR="/opt/budsjett-app"
BACKUP_DIR="$APP_DIR/backups"
TIMESTAMP=$(date +%Y-%m-%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

docker compose -f "$APP_DIR/docker-compose.prod.yml" exec -T db \
  pg_dump -U budsjett budsjett | gzip > "$BACKUP_DIR/budsjett_$TIMESTAMP.sql.gz"

find "$BACKUP_DIR" -name "budsjett_*.sql.gz" -mtime +7 -delete
