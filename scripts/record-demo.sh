#!/usr/bin/env bash
# Record a demo GIF of the QKD Playground web UI.
#
# This script:
#   1. Starts the backend and frontend dev servers
#   2. Waits for both to be healthy
#   3. Runs the Playwright recording script
#   4. Cleans up servers
#
# Prerequisites: uv, yarn, ffmpeg, npx
# First-time setup: npx playwright install chromium
#
# Usage: bash scripts/record-demo.sh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  echo "🧹 Cleaning up..."
  [ -n "$BACKEND_PID" ] && kill "$BACKEND_PID" 2>/dev/null || true
  [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null || true
  wait 2>/dev/null || true
}
trap cleanup EXIT

# --- Start backend ---
echo "🚀 Starting backend..."
cd "$ROOT_DIR/backend"
uv run uvicorn qkd_playground.api.app:create_app --factory --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "⏳ Waiting for backend..."
for i in $(seq 1 30); do
  if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo "   ✅ Backend ready"
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "   ❌ Backend failed to start"
    exit 1
  fi
  sleep 1
done

# --- Start frontend ---
echo "🚀 Starting frontend..."
cd "$ROOT_DIR/frontend"
yarn dev --host 0.0.0.0 --port 5173 &
FRONTEND_PID=$!

echo "⏳ Waiting for frontend..."
for i in $(seq 1 30); do
  if curl -sf http://localhost:5173 > /dev/null 2>&1; then
    echo "   ✅ Frontend ready"
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "   ❌ Frontend failed to start"
    exit 1
  fi
  sleep 1
done

# --- Record demo ---
echo ""
echo "🎬 Recording demo..."
cd "$ROOT_DIR"
npx tsx scripts/record-demo.ts

echo ""
echo "🎉 Done! GIF saved to docs/assets/demo.gif"
