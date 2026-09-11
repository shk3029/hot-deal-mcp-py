"""LOCAL STUB — 실제 사내 인증 키 검증 로직으로 교체 필요.

로컬 실행만 되면 되므로 검증 없이 통과시키는 최소 구현.
"""

from __future__ import annotations

from starlette.types import ASGIApp, Receive, Scope, Send


class RequireInferAuthKey:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        await self.app(scope, receive, send)
