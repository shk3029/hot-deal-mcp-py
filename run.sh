#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PORT="${PORT:-8080}"
HOST="${HOST:-0.0.0.0}"

echo "🔥 Hot Deal MCP (Python/FastAPI) 시작 중..."
echo "🔌 MCP URL:      http://localhost:${PORT}/mcp"
echo "❤️  Health Check: http://localhost:${PORT}/health"
echo ""

if [[ -x "$SCRIPT_DIR/.venv/bin/uvicorn" ]]; then
    exec "$SCRIPT_DIR/.venv/bin/uvicorn" main:app --host "$HOST" --port "$PORT"
elif command -v uv >/dev/null 2>&1; then
    exec uv run uvicorn main:app --host "$HOST" --port "$PORT"
else
    echo "실행 환경이 없습니다. 프로젝트에 .venv를 만들거나 uv를 설치해 주세요."
    echo "uv 설치: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi
