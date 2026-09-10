"""FastAPI 진입점. ``fastmcp`` 의 streamable-HTTP ASGI 앱을 마운트한다.

- ``POST /mcp``  : MCP (streamable HTTP, stateless + JSON 응답)
- ``GET  /health``: 헬스 체크
"""

from __future__ import annotations

import logging
import os
import json
from contextlib import asynccontextmanager
from typing import AsyncIterator, Mapping

from fastapi import FastAPI, Request, Response

from server import mcp

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

_SENSITIVE_HEADER_MARKERS = (
    "authorization",
    "cookie",
    "token",
    "api-key",
    "apikey",
    "signature",
    "secret",
)


def _headers_for_log(headers: Mapping[str, str]) -> dict[str, str]:
    """연동 확인에 필요한 헤더 이름은 보존하고 인증값은 마스킹한다."""

    return {
        name: (
            "<redacted>"
            if any(marker in name.lower() for marker in _SENSITIVE_HEADER_MARKERS)
            else value
        )
        for name, value in headers.items()
    }


mcp_app = mcp.http_app(path="/mcp", stateless_http=True, json_response=True)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # 마운트된 하위 앱의 lifespan 은 부모가 자동 실행하지 않으므로 직접 구동한다.
    async with mcp_app.lifespan(mcp_app):
        yield


app = FastAPI(
    title="shinhan-credit-card-guide",
    version="0.0.1",
    lifespan=lifespan,
)


@app.middleware("http")
async def log_mcp_http_headers(request: Request, call_next) -> Response:
    if not request.url.path.startswith("/mcp"):
        return await call_next(request)

    logger.info(
        "MCP HTTP request headers - method=%s, path=%s, headers=%s",
        request.method,
        request.url.path,
        json.dumps(
            _headers_for_log(request.headers),
            ensure_ascii=False,
            separators=(",", ":"),
        ),
    )
    response = await call_next(request)
    logger.info(
        "MCP HTTP response headers - status=%s, headers=%s",
        response.status_code,
        json.dumps(
            _headers_for_log(response.headers),
            ensure_ascii=False,
            separators=(",", ":"),
        ),
    )
    if response.headers.get("content-type", "").split(";", 1)[0] == "application/json":
        body_iterator = response.body_iterator

        async def log_response_body():
            chunks = []
            async for chunk in body_iterator:
                chunks.append(chunk.encode("utf-8") if isinstance(chunk, str) else chunk)
                yield chunk
            body = b"".join(chunks)
            if body:
                try:
                    formatted = json.dumps(json.loads(body), ensure_ascii=False, indent=2)
                except (ValueError, UnicodeDecodeError):
                    formatted = body.decode("utf-8", errors="replace")
                logger.info(
                    "MCP HTTP response body - method=%s, path=%s, status=%s\n%s",
                    request.method,
                    request.url.path,
                    response.status_code,
                    formatted,
                )

        response.body_iterator = log_response_body()
    return response


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "UP"}


# MCP 하위 앱이 /mcp 경로를 제공하므로 루트에 마운트한다.
app.mount("/", mcp_app)
