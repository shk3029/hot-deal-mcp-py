"""FastAPI 진입점. 공식 ``mcp`` SDK 의 streamable-HTTP ASGI 앱을 마운트한다.

- ``POST /mcp``  : MCP (streamable HTTP, stateless + JSON 응답)
- ``GET  /health``: 헬스 체크
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from server import mcp

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(levelname)s - %(message)s",
)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # 마운트된 하위 앱의 lifespan 은 부모가 자동 실행하지 않으므로 직접 구동한다.
    async with mcp.session_manager.run():
        yield


app = FastAPI(
    title="shinhan-credit-card-guide",
    version="0.0.1",
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "UP"}


# streamable_http_app() 자체가 streamable_http_path(=/mcp)에서 서비스하므로 루트에 마운트한다.
app.mount("/", mcp.streamable_http_app())
