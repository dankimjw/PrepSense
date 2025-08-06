#!/usr/bin/env bash
set -euo pipefail

WATCH_DIR="logs/orchestrator"
LOG_DIR="logs/auto-hook"
mkdir -p "$LOG_DIR"

echo "🔎  auto‑hook watching $WATCH_DIR …"
inotifywait -m -e close_write --format '%w%f' "$WATCH_DIR" |
while read -r orchestrator_json; do
  ts=$(date -u +'%Y-%m-%dT%H-%M-%SZ')
  echo "📝  [$ts] New orchestrator log: $orchestrator_json"

  # 1. Kick off auditor
  claude-cli call project-auditor "audit" --file "$orchestrator_json" \
    | tee "$LOG_DIR/$ts-auditor.log"

  # 2. Let auditor trigger doc-maintainer **internally**
  #    (preferred—you already added that call to auditor’s step 5)
  #    Nothing else to do in this script.

  # --- OPTIONAL: If you still want a direct doc-maintainer call ---
  # Extract every markdown file touched in the last commit
  # change_set=$(git diff --name-only -- '[dD]ocs/flows/*.md')
  # for md in $change_set; do
  #   claude-cli call doc-maintainer "sync" --changed "$md" \
  #     | tee "$LOG_DIR/$ts-doc-maintainer.log"
  # done
done