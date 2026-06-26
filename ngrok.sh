#!/usr/bin/bash
set -euo pipefail

[ "$(id -u)" -eq 0 ] || { echo "ERROR: Run with sudo"; exit 1; }

TOKEN="2WeJeyY1giZpwEpia2HpTcy1bqp_5QLd8XCK2EEAGw2NGdJNG"
PROTO="${1:-${NGROK_PROTO:-http}}"
HOST="${2:-${NGROK_HOST:-localhost}}"
PORT="${3:-${NGROK_PORT:-8000}}"

[[ "$PROTO" =~ ^(http|tcp|tls)$ ]] || { echo "Use: http/tcp/tls"; exit 1; }
[[ "$PORT" =~ ^[0-9]+$ ]] || { echo "Invalid port"; exit 1; }

if ! command -v ngrok >/dev/null 2>&1; then
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -qq
  apt-get install -y -qq curl ca-certificates gnupg
  curl -fsSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
    | gpg --batch --yes --dearmor -o /usr/share/keyrings/ngrok.gpg
  echo "deb [signed-by=/usr/share/keyrings/ngrok.gpg] https://ngrok-agent.s3.amazonaws.com buster main" \
    > /etc/apt/sources.list.d/ngrok.list
  apt-get update -qq
  apt-get install -y -qq ngrok
fi

LOG="/tmp/ngrok-${PROTO}-${PORT}.log"
nohup ngrok "$PROTO" --authtoken "$TOKEN" "$HOST:$PORT" > "$LOG" 2>&1 &
PID="$!"

for _ in $(seq 1 30); do
  URL="$(curl -fsS http://127.0.0.1:4040/api/tunnels 2>/dev/null \
    | grep -o '"public_url":"[^"]*"' \
    | head -n1 \
    | cut -d'"' -f4 || true)"
  [ -n "$URL" ] && break
  sleep 1
done

[ -n "${URL:-}" ] || { echo "ERROR: ngrok started pid=$PID but forwarding URL not ready. Log: $LOG"; exit 1; }
echo "PID: $PID - Forwarding: $URL"
