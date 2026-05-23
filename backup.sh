#!/bin/bash
# Portfolio Backup Script
# Usage: ./backup.sh [backup_directory]
#   backup_directory defaults to ~/portfolio-backup
#   For external drive: ./backup.sh /Volumes/MyDrive/portfolio-backup

BACKUP_DIR="${1:-$HOME/portfolio-backup}"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="$BACKUP_DIR/$DATE"

SUPABASE_URL="https://qbbgrsdofmhiqeusguoq.supabase.co"
SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFiYmdyc2RvZm1oaXFldXNndW9xIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzkzOTc4MTksImV4cCI6MjA5NDk3MzgxOX0.zT_YwQlALesrlqPwXvQpzZ05JJyK0nvLP1RDxlb5_fM"

echo "=== Portfolio Backup ==="
echo "Backing up to: $BACKUP_PATH"
echo ""

mkdir -p "$BACKUP_PATH/data" "$BACKUP_PATH/media"

# 1. Export projects from Supabase
echo "[1/3] Exporting project data from Supabase..."
curl -s "$SUPABASE_URL/rest/v1/portfolio_projects?select=*" \
  -H "apikey: $SUPABASE_KEY" \
  -H "Authorization: Bearer $SUPABASE_KEY" \
  > "$BACKUP_PATH/data/projects.json"

curl -s "$SUPABASE_URL/rest/v1/portfolio_media?select=*&order=project_id,sort_order" \
  -H "apikey: $SUPABASE_KEY" \
  -H "Authorization: Bearer $SUPABASE_KEY" \
  > "$BACKUP_PATH/data/media.json"

# Verify exports aren't empty/error
if ! python3 -c "import json; json.load(open('$BACKUP_PATH/data/projects.json'))" 2>/dev/null; then
    echo "ERROR: Failed to export projects. Check Supabase connection."
    exit 1
fi

PROJECT_COUNT=$(python3 -c "import json; print(len(json.load(open('$BACKUP_PATH/data/projects.json'))))")
MEDIA_RECORD_COUNT=$(python3 -c "import json; print(len(json.load(open('$BACKUP_PATH/data/media.json'))))")
echo "  Projects: $PROJECT_COUNT"
echo "  Media records: $MEDIA_RECORD_COUNT"

# 2. Download all media files
echo ""
echo "[2/3] Downloading media files..."

URLS=$(python3 -c "
import json
for m in json.load(open('$BACKUP_PATH/data/media.json')):
    print(m['url'])
")

COUNT=0
DOWNLOADED=0
SKIPPED=0
TOTAL=$(echo "$URLS" | wc -l | tr -d ' ')

while IFS= read -r url; do
    [ -z "$url" ] && continue
    COUNT=$((COUNT + 1))

    # Skip YouTube IDs (not downloadable files)
    if [[ ! "$url" =~ ^https?:// ]]; then
        SKIPPED=$((SKIPPED + 1))
        echo "  [$COUNT/$TOTAL] Skip (YouTube): $url"
        continue
    fi

    # Create filename from URL
    FILENAME=$(python3 -c "import urllib.parse, os; print(os.path.basename(urllib.parse.unquote('$url')))")

    if [ -f "$BACKUP_PATH/media/$FILENAME" ]; then
        echo "  [$COUNT/$TOTAL] Exists: $FILENAME"
    else
        echo "  [$COUNT/$TOTAL] Downloading: $FILENAME"
        curl -sL "$url" -o "$BACKUP_PATH/media/$FILENAME"
        if [ $? -eq 0 ]; then
            DOWNLOADED=$((DOWNLOADED + 1))
        else
            echo "    WARNING: Download failed"
        fi
    fi
done <<< "$URLS"

# 3. Summary
echo ""
echo "[3/3] Backup complete!"
echo ""
TOTAL_SIZE=$(du -sh "$BACKUP_PATH" | cut -f1)
MEDIA_FILES=$(ls -1 "$BACKUP_PATH/media/" 2>/dev/null | wc -l | tr -d ' ')

echo "=== Summary ==="
echo "  Projects:       $PROJECT_COUNT"
echo "  Media records:  $MEDIA_RECORD_COUNT"
echo "  Files saved:    $MEDIA_FILES"
echo "  Downloaded:     $DOWNLOADED new"
echo "  Skipped:        $SKIPPED (YouTube IDs)"
echo "  Total size:     $TOTAL_SIZE"
echo "  Location:       $BACKUP_PATH"
echo ""
echo "To backup to external drive:"
echo "  ./backup.sh /Volumes/YOUR_DRIVE/portfolio-backup"
