#!/bin/bash
# MoltPedia Database Restore Script
# Usage: ./restore.sh <backup_file> [API_KEY] [SECRET_KEY]
#
# ⚠️ WARNING: This DROPS ALL TABLES and restores from backup.
#    Make a fresh backup first if you have any data worth keeping.

set -euo pipefail

BACKUP_FILE="${1:-}"
API_KEY="${2:-${MOLTPEDIA_API_KEY:-}}"
SECRET="${3:-${MOLTPEDIA_SECRET:-}}"
API_URL="${MOLTPEDIA_API_URL:-https://backend-production-7da3e.up.railway.app}"

if [ -z "$BACKUP_FILE" ] || [ -z "$API_KEY" ] || [ -z "$SECRET" ]; then
    echo "❌ Usage: ./restore.sh <backup_file> <API_KEY> <SECRET_KEY>"
    echo "   Or set MOLTPEDIA_API_KEY and MOLTPEDIA_SECRET env vars"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Backup file not found: $BACKUP_FILE"
    exit 1
fi

SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "⚠️  WARNING: This will DROP ALL TABLES and restore from:"
echo "   File: $BACKUP_FILE ($SIZE)"
echo "   Target: $API_URL"
echo ""
read -p "Type 'yes' to confirm: " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "❌ Aborted"
    exit 1
fi

echo "🔄 Restoring database..."
HTTP_CODE=$(curl -s -w "%{http_code}" -o /tmp/restore-result.json \
    -X POST \
    -H "X-API-Key: $API_KEY" \
    -H "X-Dev-Secret: $SECRET" \
    -H "Content-Type: application/json" \
    -d @"$BACKUP_FILE" \
    "$API_URL/api/admin/restore")

if [ "$HTTP_CODE" != "200" ]; then
    echo "❌ Restore failed (HTTP $HTTP_CODE)"
    cat /tmp/restore-result.json
    exit 1
fi

echo "✅ Database restored successfully!"
cat /tmp/restore-result.json
echo ""
