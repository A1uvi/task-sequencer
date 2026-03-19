#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
LOG_DIR="$ROOT/logs"
PID_DIR="$ROOT/.pids"

# ── colours ──────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; RESET='\033[0m'
ok()   { echo -e "${GREEN}✓${RESET} $*"; }
warn() { echo -e "${YELLOW}⚠${RESET}  $*"; }
die()  { echo -e "${RED}✗${RESET} $*" >&2; exit 1; }

# ── load .env ─────────────────────────────────────────────────────────────────
[[ -f "$ROOT/.env" ]] || die ".env not found — run: cp .env.example .env and fill in values"
set -a; source "$ROOT/.env"; set +a

# ── setup dirs ────────────────────────────────────────────────────────────────
mkdir -p "$LOG_DIR" "$PID_DIR"

# ── stop handler (Ctrl-C or ./start.sh stop) ─────────────────────────────────
stop_all() {
  echo ""
  echo "Stopping services..."
  for pidfile in "$PID_DIR"/*.pid; do
    [[ -f "$pidfile" ]] || continue
    name=$(basename "$pidfile" .pid)
    pid=$(cat "$pidfile")
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null && ok "Stopped $name (pid $pid)"
    fi
    rm -f "$pidfile"
  done
  echo "Done. Logs are in $LOG_DIR/"
}

if [[ "${1:-}" == "stop" ]]; then
  stop_all
  exit 0
fi

trap stop_all EXIT INT TERM

# ── 1. Docker (Postgres + Redis) ─────────────────────────────────────────────
echo ""
echo "▶ Starting infrastructure (Docker)..."
if ! docker info &>/dev/null; then
  warn "Docker daemon not running — attempting to start Docker Desktop..."
  open -a Docker
  for i in $(seq 1 20); do
    sleep 3
    docker info &>/dev/null && break
    [[ $i -eq 20 ]] && die "Docker did not start after 60s. Open Docker Desktop manually and re-run."
  done
fi

docker compose up -d postgres redis 2>&1 | grep -E "Started|Running|healthy|error" || true

# wait for postgres
for i in $(seq 1 15); do
  docker exec task-sequencer-postgres-1 pg_isready -U aiworkflow &>/dev/null && break
  sleep 2
  [[ $i -eq 15 ]] && die "Postgres did not become ready"
done
ok "Postgres ready"

# wait for redis
for i in $(seq 1 10); do
  docker exec task-sequencer-redis-1 redis-cli ping &>/dev/null && break
  sleep 1
  [[ $i -eq 10 ]] && die "Redis did not become ready"
done
ok "Redis ready"

# ── 2. Python venv ────────────────────────────────────────────────────────────
echo ""
echo "▶ Checking Python environment..."
VENV="$BACKEND/.venv"
if [[ ! -f "$VENV/bin/python" ]]; then
  warn "venv not found — creating..."
  python3 -m venv "$VENV"
fi

VENV_PY="$VENV/bin/python"
VENV_PIP="$VENV/bin/pip"

# install if any key package is missing
if ! "$VENV_PY" -c "import fastapi, sqlalchemy, uvicorn" &>/dev/null; then
  warn "Installing backend dependencies (first run may take a minute)..."
  "$VENV_PIP" install -q -e "$BACKEND/.[dev]" "pydantic[email]" python-multipart "bcrypt<4.0"
fi
ok "Python environment ready"

# ── 3. Migrations ─────────────────────────────────────────────────────────────
echo ""
echo "▶ Running database migrations..."
(cd "$BACKEND" && "$VENV/bin/alembic" upgrade head 2>&1) | grep -E "Running|up to date|error" || true
ok "Migrations up to date"

# ── 4. Frontend deps ─────────────────────────────────────────────────────────
echo ""
echo "▶ Checking frontend dependencies..."
if [[ ! -d "$FRONTEND/node_modules" ]]; then
  warn "node_modules not found — running npm install..."
  (cd "$FRONTEND" && npm install --silent)
fi
ok "Frontend dependencies ready"

# ── 5. Start API server ───────────────────────────────────────────────────────
echo ""
echo "▶ Starting API server..."
(cd "$BACKEND" && "$VENV/bin/uvicorn" main:app --host 0.0.0.0 --port 8000 --reload \
  >> "$LOG_DIR/api.log" 2>&1) &
echo $! > "$PID_DIR/api.pid"

# ── 6. Start Worker ───────────────────────────────────────────────────────────
echo "▶ Starting background worker..."
(cd "$BACKEND" && "$VENV_PY" -m app.worker.main \
  >> "$LOG_DIR/worker.log" 2>&1) &
echo $! > "$PID_DIR/worker.pid"

# ── 7. Start Frontend ─────────────────────────────────────────────────────────
echo "▶ Starting frontend dev server..."
(cd "$FRONTEND" && npm run dev \
  >> "$LOG_DIR/frontend.log" 2>&1) &
echo $! > "$PID_DIR/frontend.pid"

# ── 8. Wait for API to be ready ───────────────────────────────────────────────
echo ""
echo "Waiting for services to be ready..."
for i in $(seq 1 20); do
  sleep 2
  if curl -sf --max-time 2 http://localhost:8000/openapi.json &>/dev/null; then
    break
  fi
  [[ $i -eq 20 ]] && { warn "API did not start in time — check logs/api.log"; }
done

for i in $(seq 1 15); do
  sleep 1
  if curl -sf --max-time 2 http://localhost:5173 &>/dev/null; then
    break
  fi
done

# ── 9. Summary ────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "${GREEN}  AI Workflow Platform is running${RESET}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""
echo -e "  Frontend   →  ${GREEN}http://localhost:5173${RESET}"
echo -e "  API        →  ${GREEN}http://localhost:8000${RESET}"
echo -e "  Swagger    →  ${GREEN}http://localhost:8000/docs${RESET}"
echo ""
echo -e "  Logs       →  $LOG_DIR/"
echo -e "  Stop       →  Ctrl-C  or  ./start.sh stop"
echo ""

# ── 10. Tail logs (keep script alive) ─────────────────────────────────────────
wait
