#!/usr/bin/env bash
# =============================================================================
# SkyOps XP -- Universal Linux & macOS Launcher Script (run.sh)
# Operations & Real Airline Economy Platform for X-Plane 12
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PORT="${SKYOPS_PORT:-8000}"

echo "=================================================================="
echo "  ✈️  SkyOps XP -- Operations & Real Economy for X-Plane 12"
echo "=================================================================="

# 1. Detect Python 3
PYTHON_BIN=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
else
    echo "[ERROR / ERRORE] Python 3 not found on your system."
    echo "  • Ubuntu/Debian:  sudo apt update && sudo apt install python3 python3-venv python3-pip"
    echo "  • Arch/Manjaro:   sudo pacman -S python"
    echo "  • Fedora/RHEL:    sudo dnf install python3"
    echo "  • macOS:          brew install python"
    exit 1
fi

# 2. Check or create Virtual Environment (.venv)
if [ ! -f "backend/venv/bin/activate" ] && [ ! -f ".venv/bin/activate" ]; then
    echo "[INFO] Creating Python virtual environment .venv..."
    $PYTHON_BIN -m venv .venv || {
        echo "[ERROR] Failed to create venv. Make sure python3-venv is installed."
        exit 1
    }
    # shellcheck disable=SC1091
    source .venv/bin/activate
    echo "[INFO] Installing dependencies from backend/requirements.txt..."
    python -m pip install --upgrade pip
    pip install -r backend/requirements.txt
elif [ -f "backend/venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    source backend/venv/bin/activate
else
    # shellcheck disable=SC1091
    source .venv/bin/activate
fi

# 3. Check pre-built frontend dashboard
if [ ! -f "frontend/dist/index.html" ]; then
    if command -v npm >/dev/null 2>&1 && [ -d "frontend" ]; then
        echo "[INFO] Pre-built dashboard not found. Compiling via npm..."
        (cd frontend && npm install && npm run build)
    else
        echo "[WARNING] Pre-built frontend/dist not found. Some UI elements may be unavailable."
    fi
fi

# 4. Display local network IP for Tablet / iPad / Second Monitor Wi-Fi
LOCAL_IP="127.0.0.1"
if command -v ip >/dev/null 2>&1; then
    LOCAL_IP=$(ip route get 1.1.1.1 2>/dev/null | awk '{print $7}' || echo "127.0.0.1")
elif command -v ifconfig >/dev/null 2>&1; then
    LOCAL_IP=$(ifconfig 2>/dev/null | grep 'inet ' | grep -v '127.0.0.1' | awk '{print $2}' | head -n 1 || echo "127.0.0.1")
fi

echo ""
echo "------------------------------------------------------------------"
echo "  CONNESSIONI ATTIVE / ACTIVE CONNECTIONS:"
echo "  -> Tablet / iPad / Remote PC:  http://${LOCAL_IP}:${PORT}"
echo "  -> Local PC Browser:          http://127.0.0.1:${PORT}"
echo "  -> X-Plane 12 UDP:            127.0.0.1:49000 (Zero Plugins Required!)"
echo "------------------------------------------------------------------"
echo "  Press CTRL+C to stop the platform / Premi CTRL+C per arrestare."
echo "=================================================================="
echo ""

# 5. Start Uvicorn server
export PYTHONPATH="${SCRIPT_DIR}/backend"
cd backend
exec python -m uvicorn skyops_server:skyops_app --host 0.0.0.0 --port "${PORT}"
