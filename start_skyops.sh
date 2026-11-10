#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR"

echo "=========================================================="
echo "          ✈️  AVVIO SKYOPS XP PER X-PLANE 12             "
echo "=========================================================="
echo "Directory di lavoro: $DIR"

# Controlla se la build del frontend esiste, altrimenti la compila
if [ ! -d "frontend/dist" ]; then
    echo "Compilazione dashboard web..."
    cd frontend && npm run build && cd ..
fi

LOCAL_IP=$(ip route get 1.1.1.1 2>/dev/null | awk '{print $7}' || echo "127.0.0.1")
echo "Avvio server operativo SkyOps XP su http://localhost:8000..."
echo "Accessibile anche da tablet o secondo schermo su http://${LOCAL_IP}:8000"
echo "Premi CTRL+C per arrestare."
echo "----------------------------------------------------------"

cd backend
export PYTHONPATH=.
venv/bin/uvicorn skyops_server:skyops_app --host 0.0.0.0 --port 8000
