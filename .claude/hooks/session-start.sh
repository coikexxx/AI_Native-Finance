#!/bin/bash
set -euo pipefail

# Only run in remote (Claude Code on the web) environments
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"

echo "[session-start] Setting up AI Native Finance environment..."

# ── Backend: Python dependencies ──────────────────────────────────────────────
echo "[session-start] Installing backend Python dependencies..."
cd "$PROJECT_DIR/backend"

pip install --quiet --disable-pip-version-check \
  fastapi "uvicorn[standard]" anthropic \
  sqlalchemy aiosqlite apscheduler \
  networkx numpy pandas scipy \
  feedparser httpx \
  pydantic "pydantic-settings" python-dotenv \
  pytest pytest-asyncio \
  "python-multipart" beautifulsoup4 lxml \
  chromadb

# yfinance has a broken transitive dep (multitasking) in some build environments;
# fall back to apt package if pip build fails
pip install --quiet --disable-pip-version-check yfinance || \
  (apt-get install -y python3-multitasking 2>/dev/null && \
   pip install --quiet --disable-pip-version-check yfinance) || \
  echo "[session-start] WARNING: yfinance could not be installed; market data ingestion will be unavailable"

# Make backend importable from tests
echo 'export PYTHONPATH="$CLAUDE_PROJECT_DIR/backend"' >> "$CLAUDE_ENV_FILE"

# ── Frontend: Node dependencies ────────────────────────────────────────────────
echo "[session-start] Installing frontend Node dependencies..."
cd "$PROJECT_DIR/frontend"
npm install --prefer-offline --no-audit --no-fund

echo "[session-start] Setup complete."
