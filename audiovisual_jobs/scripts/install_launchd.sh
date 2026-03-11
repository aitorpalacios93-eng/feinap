#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLIST_DIR="$HOME/Library/LaunchAgents"
PLIST_PATH="$PLIST_DIR/com.audiovisual.jobs.pipeline.plist"
RUN_SCRIPT="$BASE_DIR/scripts/run_pipeline.sh"
PY_BIN="$BASE_DIR/venv/bin/python"
OFFERS_LIMIT="${DASHBOARD_OFFERS_LIMIT:-1000}"
STDOUT_LOG="$BASE_DIR/logs/launchd_pipeline.out.log"
STDERR_LOG="$BASE_DIR/logs/launchd_pipeline.err.log"

RUN_COMMAND="cd \"$BASE_DIR\" && \"$PY_BIN\" main.py && \"$PY_BIN\" scripts/cleanup_noisy_sources.py --apply && \"$PY_BIN\" scripts/build_review_dashboard.py --offers-limit $OFFERS_LIMIT && \"$PY_BIN\" scripts/upload_to_sheets.py"

mkdir -p "$PLIST_DIR"
mkdir -p "$BASE_DIR/logs"

cat > "$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.audiovisual.jobs.pipeline</string>

  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>-lc</string>
    <string>$RUN_COMMAND</string>
  </array>

  <key>WorkingDirectory</key>
  <string>$HOME</string>

  <key>RunAtLoad</key>
  <true/>

  <key>StartCalendarInterval</key>
  <array>
    <dict><key>Minute</key><integer>0</integer><key>Hour</key><integer>0</integer></dict>
    <dict><key>Minute</key><integer>0</integer><key>Hour</key><integer>6</integer></dict>
    <dict><key>Minute</key><integer>0</integer><key>Hour</key><integer>12</integer></dict>
    <dict><key>Minute</key><integer>0</integer><key>Hour</key><integer>18</integer></dict>
  </array>

  <key>StandardOutPath</key>
  <string>$STDOUT_LOG</string>

  <key>StandardErrorPath</key>
  <string>$STDERR_LOG</string>
</dict>
</plist>
EOF

chmod +x "$RUN_SCRIPT"
xattr -d com.apple.provenance "$RUN_SCRIPT" >/dev/null 2>&1 || true

if launchctl print "gui/$(id -u)/com.audiovisual.jobs.pipeline" >/dev/null 2>&1; then
  launchctl bootout "gui/$(id -u)" "$PLIST_PATH" || true
fi

launchctl bootstrap "gui/$(id -u)" "$PLIST_PATH"
launchctl enable "gui/$(id -u)/com.audiovisual.jobs.pipeline"
launchctl kickstart -k "gui/$(id -u)/com.audiovisual.jobs.pipeline"

echo "LaunchAgent instalado: $PLIST_PATH"
echo "Salida: $STDOUT_LOG"
echo "Errores: $STDERR_LOG"
