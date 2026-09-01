"""툴 모듈 공통 헬퍼."""

from __future__ import annotations

import json
from typing import Any


def json_widget(payload: dict[str, Any]) -> str:
    """PlayMCP 위젯 응답(dict)을 text content 로 넣을 JSON 문자열로 직렬화한다."""
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
