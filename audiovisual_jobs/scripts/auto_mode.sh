#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLIST_PATH="$HOME/Library/LaunchAgents/com.audiovisual.jobs.pipeline.plist"
SERVICE="gui/$(id -u)/com.audiovisual.jobs.pipeline"

usage() {
  echo "Uso: $0 {start|stop|status|logs}"
}

action="${1:-}"

case "$action" in
  start)
    "$BASE_DIR/scripts/install_launchd.sh"
    ;;
  stop)
    if launchctl print "$SERVICE" >/dev/null 2>&1; then
      launchctl bootout "gui/$(id -u)" "$PLIST_PATH" || true
      launchctl disable "$SERVICE" || true
      echo "Auto mode detenido."
    else
      echo "Auto mode ya estaba detenido."
    fi
    ;;
  status)
    launchctl print "$SERVICE"
    ;;
  logs)
    echo "OUT: $BASE_DIR/logs/launchd_pipeline.out.log"
    echo "ERR: $BASE_DIR/logs/launchd_pipeline.err.log"
    ;;
  *)
    usage
    exit 1
    ;;
esac
