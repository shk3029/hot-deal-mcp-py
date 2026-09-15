#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

MCP_HOST="${MCP_HOST:-0.0.0.0}"
MCP_PORT="${MCP_PORT:-8080}"
COMMON_DATA_SOURCE="${CARD_DATA_SOURCE:-}"
MCP_DATA_SOURCE="${MCP_DATA_SOURCE:-${COMMON_DATA_SOURCE:-mci}}"

PREVIEW_HOST="${PREVIEW_HOST:-127.0.0.1}"
PREVIEW_PORT="${PREVIEW_PORT:-8765}"
PREVIEW_DATA_SOURCE="${PREVIEW_DATA_SOURCE:-${COMMON_DATA_SOURCE:-mock}}"

if [[ -x "$SCRIPT_DIR/.venv/bin/python" ]]; then
    PYTHON_BIN="$SCRIPT_DIR/.venv/bin/python"
elif command -v uv >/dev/null 2>&1; then
    PYTHON_BIN="uv"
else
    echo "실행 환경이 없습니다. 프로젝트에 .venv를 만들거나 uv를 설치해 주세요."
    echo "uv 설치: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

if [[ "$PYTHON_BIN" == "uv" ]]; then
    MCP_COMMAND=(uv run python -m uvicorn main:app --host "$MCP_HOST" --port "$MCP_PORT")
    PREVIEW_COMMAND=(uv run python -m uvicorn preview.app:app --host "$PREVIEW_HOST" --port "$PREVIEW_PORT")
else
    MCP_COMMAND=("$PYTHON_BIN" -m uvicorn main:app --host "$MCP_HOST" --port "$MCP_PORT")
    PREVIEW_COMMAND=("$PYTHON_BIN" -m uvicorn preview.app:app --host "$PREVIEW_HOST" --port "$PREVIEW_PORT")
fi

MCP_PID=""
PREVIEW_PID=""

stop_servers() {
    trap - EXIT INT TERM
    [[ -n "$MCP_PID" ]] && kill "$MCP_PID" 2>/dev/null || true
    [[ -n "$PREVIEW_PID" ]] && kill "$PREVIEW_PID" 2>/dev/null || true
    [[ -n "$MCP_PID" ]] && wait "$MCP_PID" 2>/dev/null || true
    [[ -n "$PREVIEW_PID" ]] && wait "$PREVIEW_PID" 2>/dev/null || true
}

trap stop_servers EXIT INT TERM

echo "Shinhan Card MCP + Widget Preview 시작 중..."
echo "MCP URL:       http://localhost:${MCP_PORT}/mcp (${MCP_DATA_SOURCE})"
echo "Preview URL:   http://${PREVIEW_HOST}:${PREVIEW_PORT} (${PREVIEW_DATA_SOURCE})"
echo "종료: Ctrl+C"
echo ""

CARD_DATA_SOURCE="$MCP_DATA_SOURCE" "${MCP_COMMAND[@]}" &
MCP_PID=$!

CARD_DATA_SOURCE="$PREVIEW_DATA_SOURCE" "${PREVIEW_COMMAND[@]}" &
PREVIEW_PID=$!

wait "$MCP_PID" "$PREVIEW_PID"
