#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$BASE_DIR/logs"
RUN_TS="$(date +"%Y%m%d_%H%M%S")"
LOG_FILE="$LOG_DIR/pipeline_${RUN_TS}.log"
LATEST_LOG="$LOG_DIR/pipeline_latest.log"
LOCK_DIR="$BASE_DIR/.pipeline_lock"
OFFERS_LIMIT="${DASHBOARD_OFFERS_LIMIT:-1000}"

mkdir -p "$LOG_DIR"

if [ ! -x "$BASE_DIR/venv/bin/python" ]; then
  echo "No se encontro Python en venv/bin/python"
  echo "Crea o activa el entorno virtual antes de ejecutar."
  exit 1
fi

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  echo "Otro pipeline ya esta en ejecucion. Se omite este run."
  exit 0
fi

cleanup_lock() {
  rm -rf "$LOCK_DIR"
}
trap cleanup_lock EXIT

echo "[RUN] Ejecutando pipeline automatico..."
echo "[RUN] Log: $LOG_FILE"

cd "$BASE_DIR"

{
  echo "[STEP] main.py"
  "$BASE_DIR/venv/bin/python" main.py

  echo "[STEP] cleanup_noisy_sources.py --apply"
  if ! "$BASE_DIR/venv/bin/python" scripts/cleanup_noisy_sources.py --apply; then
    echo "[WARN] Limpieza de fuentes ruido fallo; continua el run"
  fi

  echo "[STEP] build_review_dashboard.py --offers-limit $OFFERS_LIMIT"
  if ! "$BASE_DIR/venv/bin/python" scripts/build_review_dashboard.py --offers-limit "$OFFERS_LIMIT"; then
    echo "[WARN] Generacion de dashboard fallo; continua el run"
  fi

  echo "[STEP] email_alerts.py"
  if ! "$BASE_DIR/venv/bin/python" scripts/email_alerts.py; then
    echo "[WARN] Envio de alertas por email fallo; continua el run"
  fi

  echo "[STEP] upload_to_sheets.py"
  if ! "$BASE_DIR/venv/bin/python" scripts/upload_to_sheets.py; then
    echo "[WARN] Subida a Google Sheets fallo; continua el run"
  fi

  echo "[DONE] Run completado"
} 2>&1 | tee "$LOG_FILE"

ln -sf "$LOG_FILE" "$LATEST_LOG"
