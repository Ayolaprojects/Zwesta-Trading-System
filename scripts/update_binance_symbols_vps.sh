#!/usr/bin/env bash
# Update BINANCE_SYMBOLS in the repo .env files and attempt to restart the backend.
# Usage: ./scripts/update_binance_symbols_vps.sh "BTCUSDT,ETHUSDT,BNBUSDT"

set -euo pipefail

SYMBOLS="$1"
TS=$(date +%Y%m%d%H%M%S)
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILES=("$ROOT_DIR/.env" "$ROOT_DIR/vps_app_package/vps_rdp_bundle/.env" "$ROOT_DIR/vps_rdp_bundle/.env")

echo "Updating BINANCE_SYMBOLS to: $SYMBOLS"

for f in "${ENV_FILES[@]}"; do
  if [ -f "$f" ]; then
    echo "Backing up $f -> ${f}.bak.$TS"
    cp "$f" "${f}.bak.$TS"
    if grep -q '^BINANCE_SYMBOLS=' "$f"; then
      sed -i -E "s|^BINANCE_SYMBOLS=.*|BINANCE_SYMBOLS=$SYMBOLS|" "$f"
    else
      echo "BINANCE_SYMBOLS=$SYMBOLS" >> "$f"
    fi
    echo "Updated $f"
  fi
done

echo "Attempting to restart backend using common methods..."

cd "$ROOT_DIR"

# 1) docker-compose
if [ -f docker-compose.yml ] || [ -f docker-compose.yaml ]; then
  if command -v docker-compose >/dev/null 2>&1; then
    echo "Found docker-compose.yml — restarting services via docker-compose"
    docker-compose down || true
    docker-compose up -d
    echo "docker-compose restart attempted"
    exit 0
  fi
fi

# 2) docker (try to find container running this repo)
if command -v docker >/dev/null 2>&1; then
  CONTAINERS=$(docker ps --format '{{.ID}} {{.Names}} {{.Image}}' | grep -i zwesta || true)
  if [ -n "$CONTAINERS" ]; then
    echo "Found containers related to zwesta, restarting them:"
    echo "$CONTAINERS"
    echo "$CONTAINERS" | awk '{print $1}' | xargs -r docker restart
    exit 0
  fi
fi

# 3) systemd: try to find a unit matching 'zwesta' or 'multi_broker'
if command -v systemctl >/dev/null 2>&1; then
  UNITS=$(systemctl list-units --type=service --all --no-pager | grep -Ei 'zwesta|multi_broker|backend' || true)
  if [ -n "$UNITS" ]; then
    echo "Found systemd units matching zwesta/multi_broker/backend. Listing:"
    echo "$UNITS"
    echo "$UNITS" | awk '{print $1}' | while read -r u; do
      echo "Restarting $u"
      sudo systemctl restart "$u" || echo "Failed restarting $u"
    done
    exit 0
  fi
fi

echo "No automated restart performed. Please restart your backend process manually."
echo "Common commands you may run on the VPS:" 
echo "  # docker-compose"
echo "  docker-compose down && docker-compose up -d"
echo "  # or restart a specific container"
echo "  docker restart <container-name>"
echo "  # or systemd (replace <service-name> with your service)
  sudo systemctl restart <service-name>"

exit 0
