#!/usr/bin/bash
set -Eeuo pipefail

TOKEN="2WeJeyY1giZpwEpia2HpTcy1bqp_5QLd8XCK2EEAGw2NGdJNG"

HOST="localhost"
PORT="8000"
START=0

CFG="/root/.config/ngrok/ngrok.yml"
KEYRING="/usr/share/keyrings/ngrok.gpg"
APT_LIST="/etc/apt/sources.list.d/ngrok.list"
ENDPOINT_NAME="app"

die() {
  echo "ERROR: $*" >&2
  exit 1
}

on_error() {
  local code="$?"
  echo "ERROR: Script failed at line ${BASH_LINENO[0]} with exit code ${code}" >&2
  exit "$code"
}

trap on_error ERR

if [ "$(id -u)" -ne 0 ]; then
  die "This script must be run as root. Example: sudo $0 --host localhost --port 8000 --start"
fi

while [ $# -gt 0 ]; do
  case "$1" in
    --host)
      [ $# -ge 2 ] || die "--host value is missing"
      [[ "${2:-}" != --* ]] || die "--host value is missing"
      HOST="$2"
      shift 2
      ;;
    --port)
      [ $# -ge 2 ] || die "--port value is missing"
      [[ "${2:-}" != --* ]] || die "--port value is missing"
      PORT="$2"
      shift 2
      ;;
    --start)
      START=1
      shift
      ;;
    -h|--help)
      echo "Usage: sudo $0 [--host HOST] [--port PORT] [--start]"
      echo "Default: host=localhost port=8000"
      exit 0
      ;;
    *)
      die "Unknown argument: $1"
      ;;
  esac
done

[ -n "$TOKEN" ] || die "TOKEN is empty"
[ "$TOKEN" != "PASTE_YOUR_FIXED_NGROK_TOKEN_HERE" ] || die "Please set the fixed TOKEN inside the script"

[ -n "$HOST" ] || die "HOST cannot be empty"
[[ "$HOST" != *"://"* ]] || die "Do not include http:// or https:// in HOST"
[[ "$HOST" != *"/"* ]] || die "Do not include path in HOST"
[[ "$HOST" != *" "* ]] || die "Spaces are not allowed in HOST"

[[ "$PORT" =~ ^[0-9]+$ ]] || die "Invalid port: $PORT"
[ "$PORT" -ge 1 ] && [ "$PORT" -le 65535 ] || die "Port must be between 1 and 65535"

install_ngrok() {
  echo "ngrok is not installed. Installing ngrok..."

  export DEBIAN_FRONTEND=noninteractive

  apt-get update -qq
  apt-get install -y -qq curl ca-certificates gnupg

  mkdir -p /usr/share/keyrings

  curl -fsSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
    | gpg --batch --yes --dearmor -o "$KEYRING"

  echo "deb [signed-by=${KEYRING}] https://ngrok-agent.s3.amazonaws.com buster main" > "$APT_LIST"

  apt-get update -qq
  apt-get install -y -qq ngrok

  command -v ngrok >/dev/null 2>&1 || die "ngrok installation failed"

  echo "ngrok installed successfully"
}

if ! command -v ngrok >/dev/null 2>&1; then
  install_ngrok
fi

mkdir -p "$(dirname "$CFG")"
chmod 700 "$(dirname "$CFG")"
umask 077

cat > "$CFG" <<EOF
version: 3

agent:
  authtoken: ${TOKEN}
  update_check: false
  console_ui: false
  log: false
  web_addr: false

endpoints:
  - name: ${ENDPOINT_NAME}
    upstream:
      url: http://${HOST}:${PORT}
EOF

chmod 600 "$CFG"

echo "ngrok config updated: $CFG"
echo "Forwarding target: http://${HOST}:${PORT}"

if [ "$START" -eq 1 ]; then
  echo "Starting ngrok tunnel..."
  exec ngrok start --config "$CFG" "$ENDPOINT_NAME"
fi

echo "Config is ready"
echo "Start command:"
echo "sudo $0 --host ${HOST} --port ${PORT} --start"
