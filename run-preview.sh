#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PREVIEW_PORT="${PREVIEW_PORT:-8765}"
PREVIEW_HOST="${PREVIEW_HOST:-127.0.0.1}"
CARD_DATA_SOURCE="${CARD_DATA_SOURCE:-mock}"
export CARD_DATA_SOURCE

echo "Shinhan Card Widget Preview 시작 중..."
echo "Preview URL: http://${PREVIEW_HOST}:${PREVIEW_PORT}"
echo "Data source: ${CARD_DATA_SOURCE}"
echo ""

if [[ -x "$SCRIPT_DIR/.venv/bin/python" ]]; then
    exec "$SCRIPT_DIR/.venv/bin/python" -m uvicorn \
        preview.app:app --host "$PREVIEW_HOST" --port "$PREVIEW_PORT"
elif command -v uv >/dev/null 2>&1; then
    exec uv run python -m uvicorn \
        preview.app:app --host "$PREVIEW_HOST" --port "$PREVIEW_PORT"
else
    echo "실행 환경이 없습니다. 프로젝트에 .venv를 만들거나 uv를 설치해 주세요."
    echo "uv 설치: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi
