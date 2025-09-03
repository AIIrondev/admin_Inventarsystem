#!/usr/bin/env bash
#
# Stoppt die Inventarsystem-Dienste (Gunicorn und Nginx) kontrolliert.
# Unterstützt Umgebungsvariablen zur Anpassung der Servicenamen:
#   INVENTAR_SERVICE          (default: inventarsystem-gunicorn.service)
#   INVENTAR_NGINX_SERVICE    (default: inventarsystem-nginx.service)
# Zusätzlich: Stoppt ggf. einen lokal gestarteten Gunicorn-Prozess über PID-Datei .run/gunicorn.pid
#
# Aufrufbeispiele:
#   bash stop.sh
#   INVENTAR_SERVICE=my-gunicorn.service bash stop.sh
#   INVENTAR_SERVICE=foo.service INVENTAR_NGINX_SERVICE=bar.service sudo bash stop.sh

set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# .env einlesen (setzt ggf. INVENTAR_SERVICE / INVENTAR_NGINX_SERVICE)
if [[ -f "$SCRIPT_DIR/.env" ]]; then
	# Exportiere Variablen innerhalb .env automatisch
	set +u
	set -a
	# shellcheck disable=SC1090
	. "$SCRIPT_DIR/.env"
	set +a
	set -u
fi

SERVICE_GUNICORN=${INVENTAR_SERVICE:-inventarsystem-gunicorn.service}
SERVICE_NGINX=${INVENTAR_NGINX_SERVICE:-inventarsystem-nginx.service}

PID_DIR="$SCRIPT_DIR/.run"
PID_FILE="$PID_DIR/gunicorn.pid"

USE_SUDO=""
if [[ $EUID -ne 0 ]]; then
	# sudo nur verwenden, wenn verfügbar
	if command -v sudo >/dev/null 2>&1; then
		USE_SUDO="sudo"
	fi
fi

info()  { echo -e "\e[34m[INFO]\e[0m  $*"; }
warn()  { echo -e "\e[33m[WARN]\e[0m  $*"; }
err()   { echo -e "\e[31m[ERROR]\e[0m $*"; }
ok()    { echo -e "\e[32m[DONE]\e[0m  $*"; }

have_systemctl() { command -v systemctl >/dev/null 2>&1; }

service_exists() {
	local svc="$1"
	if have_systemctl; then
		$USE_SUDO systemctl list-unit-files | grep -q "^${svc//\/\\}[[:space:]]" && return 0 || return 1
	fi
	return 1
}

is_active() {
	local svc="$1"
	if have_systemctl; then
		local state
		state=$(systemctl is-active "$svc" 2>/dev/null || true)
		[[ "$state" == "active" ]] && return 0 || return 1
	fi
	return 1
}

stop_service() {
	local svc="$1"
	if ! have_systemctl; then
		warn "systemctl nicht verfügbar. Überspringe ${svc}."
		return 0
	fi
	if ! service_exists "$svc"; then
		warn "Dienst nicht gefunden: $svc"
		return 0
	fi

	if is_active "$svc"; then
		info "Stoppe Dienst: $svc"
		if ! $USE_SUDO systemctl stop "$svc"; then
			err "Stop fehlgeschlagen: $svc"
			return 1
		fi
		# Wartet bis inaktiv oder Timeout
		local tries=0 max=20
		while is_active "$svc" && (( tries < max )); do
			sleep 0.5
			((tries++))
		done
		if is_active "$svc"; then
			warn "Dienst $svc ist noch aktiv nach Timeout. Versuche force-stop (kill)."
			$USE_SUDO systemctl kill "$svc" || true
			sleep 0.5
		fi
		if ! is_active "$svc"; then
			ok "Gestoppt: $svc"
		else
			err "Konnte $svc nicht beenden."
			return 1
		fi
	else
		info "Dienst bereits inaktiv: $svc"
	fi
}

stop_local_gunicorn() {
	if [[ -f "$PID_FILE" ]]; then
		local pid
		pid=$(cat "$PID_FILE" 2>/dev/null || true)
		if [[ -n "${pid:-}" ]] && ps -p "$pid" >/dev/null 2>&1; then
			info "Beende lokalen Gunicorn (PID $pid)"
			kill -TERM "$pid" || true
			# Warten bis Prozess endet
			local tries=0 max=20
			while ps -p "$pid" >/dev/null 2>&1 && (( tries < max )); do
				sleep 0.5
				((tries++))
			done
			if ps -p "$pid" >/dev/null 2>&1; then
				warn "Gunicorn reagiert nicht, sende KILL"
				kill -KILL "$pid" || true
			fi
			rm -f "$PID_FILE" || true
			ok "Lokaler Gunicorn gestoppt"
		else
			warn "PID-Datei vorhanden, aber Prozess läuft nicht. Entferne PID-Datei."
			rm -f "$PID_FILE" || true
		fi
	else
		info "Keine lokale Gunicorn-PID-Datei gefunden ($PID_FILE)."
	fi
}

main() {
	info "Beende Inventarsystem-Dienste…"
	local rc=0

	stop_service "$SERVICE_GUNICORN" || rc=1
	# Nginx optional: nicht alle Setups nutzen einen eigenen Nginx-Dienstnamen
	stop_service "$SERVICE_NGINX" || rc=1

	# Fallback: lokalen Gunicorn stoppen, falls start.sh ohne systemd genutzt wurde
	stop_local_gunicorn || rc=1

	if [[ $rc -eq 0 ]]; then
		ok "Alle relevanten Dienste sind gestoppt."
	else
		err "Einige Dienste konnten nicht korrekt beendet werden."
	fi
	return $rc
}

main "$@"
