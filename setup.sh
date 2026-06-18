#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════
#  KiahBao.AI — Full Stack Launcher 🏡 仔包
#  Usage:  bash setup.sh
# ═══════════════════════════════════════════════════════
set -e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${CYAN}[KiahBao]${NC} $*"; }
ok()    { echo -e "${GREEN}[✓]${NC} $*"; }
warn()  { echo -e "${YELLOW}[!]${NC} $*"; }
error() { echo -e "${RED}[✗]${NC} $*"; exit 1; }

echo ""
echo "🏡 ═══════════════════════════════════════════════════ 🏡"
echo "         KiahBao.AI (仔包) — Startup Script"
echo "🏡 ═══════════════════════════════════════════════════ 🏡"
echo ""

# ── Step 1: Ollama Model Build ────────────────────────────
info "Step 1/4 — Building custom Ollama model 'kiahbao-ai'…"
if ollama list | grep -q "kiahbao-ai"; then
  ok "kiahbao-ai model already exists in Ollama."
else
  ollama create kiahbao-ai -f router/Modelfile
  ok "kiahbao-ai model created successfully!"
fi
echo ""

# ── Step 2: Python Virtual Environment ───────────────────
info "Step 2/4 — Setting up Python virtual environment…"
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  ok "Virtual environment created at .venv/"
else
  ok "Virtual environment already exists."
fi

source .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
ok "Python dependencies installed."
echo ""

# ── Step 3: Run Tests ─────────────────────────────────────
info "Step 3/4 — Running test suite…"
python -m pytest tests/ -v --tb=short 2>&1 || warn "Some tests failed — check output above. Continuing anyway."
echo ""

# ── Step 4: Web Dependencies ──────────────────────────────
info "Step 4/4 — Installing Next.js frontend dependencies…"
cd web
if [ ! -d "node_modules" ]; then
  npm install
else
  ok "Node modules already present."
fi
cd "$ROOT"
echo ""

# ── Launch ────────────────────────────────────────────────
ok "All setup steps complete! Launching KiahBao.AI..."
echo ""
echo "  🔗 FastAPI Backend:  http://localhost:8000"
echo "  🔗 API Docs:         http://localhost:8000/api/docs"
echo "  🔗 Next.js Frontend: http://localhost:3000"
echo ""
echo "  Press Ctrl+C to stop both servers."
echo ""

# Start FastAPI in background
source .venv/bin/activate
python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload &
FASTAPI_PID=$!

# Start Next.js
cd web
npm run dev &
NEXTJS_PID=$!
cd "$ROOT"

# Trap Ctrl+C to clean up both
cleanup() {
  echo ""
  info "Shutting down servers…"
  kill $FASTAPI_PID 2>/dev/null || true
  kill $NEXTJS_PID  2>/dev/null || true
  ok "Bye bye! No need to kiah, see you next time 👋"
}
trap cleanup INT TERM

wait
