#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v uv >/dev/null 2>&1; then
    echo "uv가 필요합니다: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

PORT="${PORT:-8080}"
HOST="${HOST:-0.0.0.0}"

echo "🔥 Hot Deal MCP (Python/FastAPI) 시작 중..."
echo "🔌 MCP URL:      http://localhost:${PORT}/mcp"
echo "❤️  Health Check: http://localhost:${PORT}/health"
echo ""

exec uv run uvicorn app.main:app --host "$HOST" --port "$PORT"
