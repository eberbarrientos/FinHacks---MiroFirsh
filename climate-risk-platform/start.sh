#!/bin/bash
set -e

# ============================================================
# Climate Risk Platform — One-command startup
# Handles: Ollama + Llama model + Backend + Frontend
# Usage: cd climate-risk-platform && bash start.sh
# ============================================================

trap "echo ''; echo 'Shutting down...'; kill 0 2>/dev/null; exit 0" SIGINT SIGTERM

DIR="$(cd "$(dirname "$0")" && pwd)"
MODEL="llama3.2:3b"

echo "╔══════════════════════════════════════════════╗"
echo "║  Climate Risk Intelligence Platform          ║"
echo "║  MiroFish-powered Agent Cascade Simulation   ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ----------------------------------------------------------
# 1. Check / install Ollama
# ----------------------------------------------------------
if ! command -v ollama &>/dev/null; then
  echo "⏳ Installing Ollama..."
  if command -v brew &>/dev/null; then
    brew install ollama
  else
    echo "❌ Ollama not found. Install it: https://ollama.com/download"
    exit 1
  fi
fi
echo "✅ Ollama installed"

# ----------------------------------------------------------
# 2. Start Ollama server if not running
# ----------------------------------------------------------
if ! curl -s http://localhost:11434/api/tags &>/dev/null; then
  echo "⏳ Starting Ollama server..."
  OLLAMA_FLASH_ATTENTION=1 OLLAMA_KV_CACHE_TYPE=q8_0 ollama serve &>/dev/null &
  OLLAMA_PID=$!
  # Wait for it to be ready
  for i in $(seq 1 20); do
    if curl -s http://localhost:11434/api/tags &>/dev/null; then break; fi
    sleep 1
  done
  echo "✅ Ollama server running (pid $OLLAMA_PID)"
else
  echo "✅ Ollama server already running"
fi

# ----------------------------------------------------------
# 3. Pull model if not present
# ----------------------------------------------------------
if ! ollama list 2>/dev/null | grep -q "$MODEL"; then
  echo "⏳ Pulling $MODEL (this takes a minute on first run)..."
  ollama pull "$MODEL"
fi
echo "✅ Model $MODEL ready"

# ----------------------------------------------------------
# 4. Ensure .env exists with Ollama config
# ----------------------------------------------------------
ENV_FILE="$DIR/backend/.env"
if [ ! -f "$ENV_FILE" ] || ! grep -q "LLM_BASE_URL" "$ENV_FILE"; then
  echo "⏳ Creating backend/.env for local Llama..."
  cat > "$ENV_FILE" << 'EOF'
OPENAI_API_KEY=ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=llama3.2:3b
ALLOWED_ORIGINS=["http://localhost:3000"]
EOF
fi
echo "✅ Backend .env configured"

# ----------------------------------------------------------
# 5. Install dependencies if needed
# ----------------------------------------------------------
if [ ! -d "$DIR/backend/venv" ] && ! pip show fastapi &>/dev/null 2>&1; then
  echo "⏳ Installing backend dependencies..."
  pip install -r "$DIR/backend/requirements.txt" -q
  pip install python-dotenv openai -q
fi

if [ ! -d "$DIR/frontend/node_modules" ]; then
  echo "⏳ Installing frontend dependencies..."
  (cd "$DIR/frontend" && npm install --silent)
fi
echo "✅ Dependencies ready"

# ----------------------------------------------------------
# 6. Warm up the model (first call loads it into RAM)
# ----------------------------------------------------------
echo "⏳ Warming up $MODEL (loading into memory)..."
curl -s http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{\"model\":\"$MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}],\"max_tokens\":5}" \
  > /dev/null 2>&1 &
WARMUP_PID=$!

# ----------------------------------------------------------
# 7. Start backend
# ----------------------------------------------------------
echo "⏳ Starting backend..."
(cd "$DIR/backend" && uvicorn app.main:app --reload --port 8000) &
BACKEND_PID=$!

# Wait for backend
for i in $(seq 1 30); do
  if curl -s http://localhost:8000/api/portfolios > /dev/null 2>&1; then
    echo "✅ Backend ready (port 8000)"
    break
  fi
  sleep 1
done

# ----------------------------------------------------------
# 8. Start frontend
# ----------------------------------------------------------
echo "⏳ Starting frontend..."
(cd "$DIR/frontend" && npm run dev) &
FRONTEND_PID=$!

# Wait for model warmup to finish
wait $WARMUP_PID 2>/dev/null

echo ""
echo "════════════════════════════════════════════════"
echo "  🌐 Frontend:  http://localhost:3000/dashboard"
echo "  🔧 Backend:   http://localhost:8000"
echo "  🤖 LLM:       Ollama ($MODEL) on port 11434"
echo "════════════════════════════════════════════════"
echo "  Press Ctrl+C to stop everything"
echo ""

# ----------------------------------------------------------
# 9. Monitor Ollama — restart if it crashes
# ----------------------------------------------------------
while true; do
  sleep 15
  if ! curl -s http://localhost:11434/api/tags &>/dev/null; then
    echo "⚠️  Ollama crashed — restarting..."
    OLLAMA_FLASH_ATTENTION=1 OLLAMA_KV_CACHE_TYPE=q8_0 ollama serve &>/dev/null &
    sleep 3
    # Re-warm the model
    curl -s http://localhost:11434/v1/chat/completions \
      -H "Content-Type: application/json" \
      -d "{\"model\":\"$MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}],\"max_tokens\":5}" \
      > /dev/null 2>&1
    echo "✅ Ollama restarted"
  fi
done &

wait
