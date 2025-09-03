#!/usr/bin/env bash
#
# Startet die Inventarsystem-Dienste.
# Versucht zuerst systemd-Services zu starten (Gunicorn und optional Nginx).
# Fallback: startet Gunicorn lokal in einem (vorhandenen) venv und schreibt eine PID-Datei nach .run/gunicorn.pid
#
# Umgebungsvariablen:
#   INVENTAR_SERVICE           Default: inventarsystem-gunicorn.service
#   INVENTAR_NGINX_SERVICE     Default: inventarsystem-nginx.service
#   VENV_PATH                  Pfad zum Python venv (Default: ./venv)
#   GUNICORN_BIND              Bind-Adresse (Default: 127.0.0.1:8000)
#   GUNICORN_WORKERS           Anzahl Worker (Default: 3)
#   GUNICORN_MODULE            WSGI App Modul (Default: Python.user:app)

set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# .env einlesen (kann Service-Namen und Gunicorn-Optionen überschreiben)
if [[ -f "$SCRIPT_DIR/.env" ]]; then
  set +u
  set -a
  # shellcheck disable=SC1090
  . "$SCRIPT_DIR/.env"
  set +a
  set -u
fi

SERVICE_GUNICORN=${INVENTAR_SERVICE:-inventarsystem-gunicorn.service}
SERVICE_NGINX=${INVENTAR_NGINX_SERVICE:-inventarsystem-nginx.service}
VENV_PATH=${VENV_PATH:-"$SCRIPT_DIR/venv"}
GUNICORN_BIND=${GUNICORN_BIND:-127.0.0.1:8000}
GUNICORN_WORKERS=${GUNICORN_WORKERS:-3}
GUNICORN_MODULE=${GUNICORN_MODULE:-Python.wsgi:app}
RUN_DIR="$SCRIPT_DIR/.run"
PID_FILE="$RUN_DIR/gunicorn.pid"
LOG_DIR="$SCRIPT_DIR/.logs"
GUNICORN_LOG="$LOG_DIR/gunicorn.log"

mkdir -p "$RUN_DIR" "$LOG_DIR"

USE_SUDO=""
if [[ $EUID -ne 0 ]]; then
  if command -v sudo >/dev/null 2>&1; then
    USE_SUDO="sudo"
  fi
fi

info()  { echo -e "\e[34m[INFO]\e[0m  $*"; }
warn()  { echo -e "\e[33m[WARN]\e[0m  $*"; }
err()   { echo -e "\e[31m[ERROR]\e[0m $*"; }
ok()    { echo -e "\e[32m[DONE]\e[0m  $*"; }

have_systemctl() { command -v systemctl >/dev/null 2>&1; }

try_start_service() {
  local svc="$1"
  if have_systemctl; then
    info "Starte Service: $svc"
    if $USE_SUDO systemctl start "$svc"; then
      ok "Service gestartet: $svc"
      return 0
    else
      warn "Service konnte nicht gestartet werden: $svc"
      return 1
    fi
  else
    warn "systemctl nicht verfügbar (kein systemd?). Überspringe $svc."
    return 1
  fi
}

start_local_gunicorn() {
  info "Starte Gunicorn lokal (Fallback)"
  local gunicorn_bin="$VENV_PATH/bin/gunicorn"
  if [[ ! -x "$gunicorn_bin" ]]; then
    err "Gunicorn nicht gefunden unter $gunicorn_bin. Bitte venv erstellen und Abhängigkeiten installieren (siehe install.sh)."
    return 1
  fi
  # Wenn noch ein alter Prozess läuft, abbrechen
  if [[ -f "$PID_FILE" ]]; then
    local pid
    pid=$(cat "$PID_FILE" 2>/dev/null || true)
    if [[ -n "${pid:-}" ]] && ps -p "$pid" >/dev/null 2>&1; then
      info "Gunicorn läuft bereits (PID $pid)."
      return 0
    else
      rm -f "$PID_FILE" || true
    fi
  fi

  # Starten im Hintergrund
  nohup "$gunicorn_bin" \
    --bind "$GUNICORN_BIND" \
    --workers "$GUNICORN_WORKERS" \
    --pid "$PID_FILE" \
    --access-logfile - \
    --error-logfile - \
    "$GUNICORN_MODULE" \
    > "$GUNICORN_LOG" 2>&1 &

  sleep 0.8
  if [[ -f "$PID_FILE" ]]; then
    local pid
    pid=$(cat "$PID_FILE")
    ok "Gunicorn lokal gestartet (PID $pid, Log: $GUNICORN_LOG)"
    return 0
  else
    err "Gunicorn konnte nicht gestartet werden. Prüfe Logs: $GUNICORN_LOG"
    return 1
  fi
}

main() {
  local rc=0
  info "Starte Inventarsystem…"
  # Versuche systemd-Services
  if ! try_start_service "$SERVICE_GUNICORN"; then
    warn "Starte lokalen Fallback für Gunicorn."
    start_local_gunicorn || rc=1
  fi

  # Nginx optional starten (fehlgeschlagenen Start nicht als fatal werten)
  try_start_service "$SERVICE_NGINX" || true

  if [[ $rc -eq 0 ]]; then
    ok "Startvorgang abgeschlossen."
  else
    err "Startvorgang abgeschlossen mit Fehlern."
  fi
  return $rc
}

main "$@"
