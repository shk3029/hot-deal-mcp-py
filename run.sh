#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

usage() {
    cat <<'HELP'
사용법: bash run.sh [옵션]
  --card-source mock|mci            기본 카드 데이터 소스
  --card-search-source mock|mci|es  카드명 검색 데이터 소스
  -h, --help                       도움말

예시:
  bash run.sh --card-source mock --card-search-source es
  bash run.sh --card-source mock --card-search-source mock

실행 인자가 환경변수보다 우선합니다. 생략하면 기존 환경변수/기본값을 사용합니다.
ES 인증은 ES_PASSWORD 또는 ES_API_KEY, 인증서는 ES_CA_CERT로 설정합니다.
HELP
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --card-source|--card-search-source)
            option="$1"
            if [[ $# -lt 2 ]]; then
                echo "값이 필요합니다: $option" >&2
                exit 2
            fi
            case "$option:$2" in
                --card-source:mock|--card-source:mci)
                    export CARD_DATA_SOURCE="$2" ;;
                --card-search-source:mock|--card-search-source:mci|--card-search-source:es)
                    export CARD_SEARCH_DATA_SOURCE="$2" ;;
                *)
                    echo "지원하지 않는 값: $option $2" >&2
                    exit 2 ;;
            esac
            shift 2
            ;;
        -h|--help) usage; exit 0 ;;
        *) echo "알 수 없는 옵션: $1 (--help 참고)" >&2; exit 2 ;;
    esac
done

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
