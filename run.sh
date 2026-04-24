#!/usr/bin/env bash
# One-command starter. From the project folder:
#   chmod +x run.sh    (only needed once)
#   ./run.sh
set -e

# Create virtualenv if it doesn't exist
if [ ! -d ".venv" ]; then
  echo "Creating virtualenv..."
  python3 -m venv .venv
fi

# Activate it
# shellcheck disable=SC1091
source .venv/bin/activate

# Install deps (idempotent — skips if already installed)
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Start the server
echo ""
echo "==========================================="
echo "  IntentFlow starting..."
echo "  Chat UI:     http://localhost:8000/ui"
echo "  API docs:    http://localhost:8000/docs"
echo "  Press Ctrl+C to stop."
echo "==========================================="
echo ""
uvicorn main:app --reload
