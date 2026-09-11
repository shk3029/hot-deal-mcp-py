"""LOCAL STUB — 실제 사내 scope 필터링 로직으로 교체 필요.

로컬 실행만 되면 되므로 아무 것도 막지 않는 최소 구현.
"""

from __future__ import annotations

from typing import Any

from fastmcp.server.middleware import Middleware


class ScopeFilterMiddleware(Middleware):
    def __init__(self, conf: Any) -> None:
        pass
