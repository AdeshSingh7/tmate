#!/usr/bin/env bash
set -euo pipefail

START=0
[ "${1:-}" = "--start" ] && START=1 && shift
TOKEN="${NGROK_AUTHTOKEN:-2WeJeyY1giZpwEpia2HpTcy1bqp_5QLd8XCK2EEAGw2NGdJNG}"
PORT="${1:-${NGROK_PORT:-8000}}"
LOG="${TMPDIR:-/tmp}/ngrok-setup.log"
CFG="${XDG_CONFIG_HOME:-$HOME/.config}/ngrok/ngrok.yml"
SUDO=""
[ "$(id -u)" -ne 0 ] && SUDO="sudo"

echo "Port ${PORT} configure ho raha hai..."
exec >"$LOG" 2>&1

export DEBIAN_FRONTEND=noninteractive
if ! command -v ngrok >/dev/null 2>&1; then
  $SUDO apt-get update -qq
  $SUDO apt-get install -y -qq curl ca-certificates gnupg
  curl -fsSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
    | $SUDO gpg --batch --yes --dearmor -o /usr/share/keyrings/ngrok.gpg
  echo "deb [signed-by=/usr/share/keyrings/ngrok.gpg] https://ngrok-agent.s3.amazonaws.com buster main" \
    | $SUDO tee /etc/apt/sources.list.d/ngrok.list >/dev/null
  $SUDO apt-get update -qq
  $SUDO apt-get install -y -qq ngrok
fi

mkdir -p "$(dirname "$CFG")"
umask 077
cat >"$CFG" <<EOF
version: "3"
agent:
  authtoken: $TOKEN
tunnels:
  app:
    proto: http
    addr: $PORT
EOF

if [ "$START" -eq 1 ]; then
  exec ngrok start --config "$CFG" app
fi
