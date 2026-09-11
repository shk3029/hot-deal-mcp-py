"""LOCAL STUB — 실제 사내 OpenTelemetry 연동으로 교체 필요.

이 저장소에는 opentelemetry 관련 패키지가 설치돼 있지 않아, 로컬 개발 시
``main.py``의 import/호출이 깨지지 않도록 아무 계측도 붙이지 않는 no-op으로
대체했다.
"""

from __future__ import annotations

from typing import Any


def setup_otel(app: Any, service_name: str) -> None:
    return None
