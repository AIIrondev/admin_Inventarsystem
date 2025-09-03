#!/usr/bin/env bash
#
# Installiert Laufzeitumgebung und (optional) systemd-Services für das Inventarsystem.
# - Erstellt ein lokales Python-venv und installiert requirements.
# - Optional: erzeugt systemd-Units und aktiviert sie.
#
# Umgebungsvariablen:
#   VENV_PATH                  Pfad zum Python venv (Default: ./venv)
#   PY_BIN                     Python-Binary (Default: python3)
#   CREATE_SYSTEMD             "1" um systemd Units zu erstellen (Default: 0)
#   SERVICE_USER               Systemd-User (Default: current user)
#   SERVICE_GROUP              Systemd-Gruppe (Default: current user's primary group)
#   INVENTAR_SERVICE           Name der Gunicorn Unit (Default: inventarsystem-gunicorn.service)
#   INVENTAR_NGINX_SERVICE     Name der Nginx Unit (Default: inventarsystem-nginx.service)
#   GUNICORN_BIND              Bind-Adresse (Default: 127.0.0.1:8000)
#   GUNICORN_WORKERS           Anzahl Worker (Default: 3)
#   GUNICORN_MODULE            WSGI App Modul (Default: Python.user:app)

set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# .env einlesen (kann Pfade und Servicenamen überschreiben)
if [[ -f "$SCRIPT_DIR/.env" ]]; then
  set +u
  set -a
  # shellcheck disable=SC1090
  . "$SCRIPT_DIR/.env"
  set +a
  set -u
fi
VENV_PATH=${VENV_PATH:-"$SCRIPT_DIR/venv"}
PY_BIN=${PY_BIN:-python3}
CREATE_SYSTEMD=${CREATE_SYSTEMD:-0}
SERVICE_USER=${SERVICE_USER:-$(id -un)}
SERVICE_GROUP=${SERVICE_GROUP:-$(id -gn)}
SERVICE_GUNICORN=${INVENTAR_SERVICE:-inventarsystem-gunicorn.service}
SERVICE_NGINX=${INVENTAR_NGINX_SERVICE:-inventarsystem-nginx.service}
GUNICORN_BIND=${GUNICORN_BIND:-127.0.0.1:8000}
GUNICORN_WORKERS=${GUNICORN_WORKERS:-3}
GUNICORN_MODULE=${GUNICORN_MODULE:-Python.user:app}

info()  { echo -e "\e[34m[INFO]\e[0m  $*"; }
warn()  { echo -e "\e[33m[WARN]\e[0m  $*"; }
err()   { echo -e "\e[31m[ERROR]\e[0m $*"; }
ok()    { echo -e "\e[32m[DONE]\e[0m  $*"; }

create_venv() {
  info "Erstelle venv unter $VENV_PATH"
  "$PY_BIN" -m venv "$VENV_PATH"
  # Aktiviere venv subshell
  source "$VENV_PATH/bin/activate"
  pip install --upgrade pip
  if [[ -f "$SCRIPT_DIR/Python/requirements.txt" ]]; then
    pip install -r "$SCRIPT_DIR/Python/requirements.txt"
  else
    warn "requirements.txt nicht gefunden. Überspringe Paketinstallation."
  fi
  deactivate
  ok "venv erstellt und Abhängigkeiten installiert"
}

create_systemd_units() {
  if ! command -v systemctl >/dev/null 2>&1; then
    warn "systemctl nicht verfügbar. Überspringe Erstellung von systemd Units."
    return 0
  fi
  local unit_dir="/etc/systemd/system"
  local app_dir="$SCRIPT_DIR"
  local exec_start="$VENV_PATH/bin/gunicorn --workers $GUNICORN_WORKERS --bind $GUNICORN_BIND $GUNICORN_MODULE"

  info "Erzeuge systemd Unit: $SERVICE_GUNICORN"
  sudo tee "$unit_dir/$SERVICE_GUNICORN" >/dev/null <<EOF
[Unit]
Description=Inventarsystem Gunicorn Service
After=network.target

[Service]
User=$SERVICE_USER
Group=$SERVICE_GROUP
WorkingDirectory=$app_dir
Environment="PATH=$VENV_PATH/bin"
ExecStart=$exec_start
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

  info "Erzeuge systemd Unit: $SERVICE_NGINX"
  sudo tee "$unit_dir/$SERVICE_NGINX" >/dev/null <<EOF
[Unit]
Description=Inventarsystem Nginx (Proxy) Service
After=network.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/bin/true
ExecStop=/bin/true

[Install]
WantedBy=multi-user.target
EOF

  info "Aktiviere und lade Units"
  sudo systemctl daemon-reload
  sudo systemctl enable "$SERVICE_GUNICORN" || true
  sudo systemctl enable "$SERVICE_NGINX" || true
  ok "systemd Units erstellt"
}

main() {
  create_venv
  if [[ "$CREATE_SYSTEMD" == "1" ]]; then
    create_systemd_units
  else
    info "Überspringe systemd-Setup (CREATE_SYSTEMD=1 setzen, um zu aktivieren)."
  fi
  ok "Installation abgeschlossen. Nutze start.sh zum Starten."
}

main "$@"
