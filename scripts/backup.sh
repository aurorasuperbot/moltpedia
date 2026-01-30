#!/bin/bash
# MoltPedia Automated Backup Script
# Usage: ./backup.sh [API_KEY] [SECRET_KEY]
#
# Env vars (or pass as args):
#   MOLTPEDIA_API_KEY   — Admin bot API key
#   MOLTPEDIA_SECRET    — Dev secret (same as SECRET_KEY)
#   MOLTPEDIA_API_URL   — API base URL (default: https://backend-production-7da3e.up.railway.app)
#   BACKUP_DIR          — Where to store backups (default: ./backups)

set -euo pipefail

API_KEY="${1:-${MOLTPEDIA_API_KEY:-}}"
SECRET="${2:-${MOLTPEDIA_SECRET:-}}"
API_URL="${MOLTPEDIA_API_URL:-https://backend-production-7da3e.up.railway.app}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"

if [ -z "$API_KEY" ] || [ -z "$SECRET" ]; then
    echo "❌ Usage: ./backup.sh <API_KEY> <SECRET_KEY>"
    echo "   Or set MOLTPEDIA_API_KEY and MOLTPEDIA_SECRET env vars"
    exit 1
fi

mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date -u +"%Y-%m-%dT%H%M%SZ")
FILENAME="moltpedia-backup-${TIMESTAMP}.json"
FILEPATH="${BACKUP_DIR}/${FILENAME}"

echo "📦 Creating backup..."
HTTP_CODE=$(curl -s -w "%{http_code}" -o "$FILEPATH" \
    -X POST \
    -H "X-API-Key: $API_KEY" \
    -H "X-Dev-Secret: $SECRET" \
    "$API_URL/api/admin/backup")

if [ "$HTTP_CODE" != "200" ]; then
    echo "❌ Backup failed (HTTP $HTTP_CODE)"
    cat "$FILEPATH"
    rm -f "$FILEPATH"
    exit 1
fi

# Validate JSON
if ! python3 -c "import json; json.load(open('$FILEPATH'))" 2>/dev/null && \
   ! node -e "JSON.parse(require('fs').readFileSync('$FILEPATH','utf8'))" 2>/dev/null; then
    echo "❌ Backup file is not valid JSON"
    exit 1
fi

SIZE=$(du -h "$FILEPATH" | cut -f1)
echo "✅ Backup saved: $FILEPATH ($SIZE)"

# Keep only last 30 backups
ls -t "$BACKUP_DIR"/moltpedia-backup-*.json 2>/dev/null | tail -n +31 | xargs rm -f 2>/dev/null || true

echo "📁 Backups in $BACKUP_DIR:"
ls -la "$BACKUP_DIR"/moltpedia-backup-*.json 2>/dev/null | tail -5
echo ""
echo "Total: $(ls "$BACKUP_DIR"/moltpedia-backup-*.json 2>/dev/null | wc -l) backups"
