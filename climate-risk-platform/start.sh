#!/bin/bash

# Start both backend and frontend from the climate-risk-platform/ directory
# Usage: cd climate-risk-platform && bash start.sh

trap "echo 'Stopping...'; kill 0" SIGINT

DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Starting backend..."
(cd "$DIR/backend" && uvicorn app.main:app --reload --port 8000) &

# Wait until backend responds
echo "Waiting for backend..."
for i in $(seq 1 30); do
  if curl -s http://localhost:8000/api/portfolios > /dev/null 2>&1; then
    echo "Backend ready."
    break
  fi
  sleep 1
done

echo "Starting frontend..."
(cd "$DIR/frontend" && npm run dev) &

echo ""
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:3000/dashboard"
echo ""

wait
