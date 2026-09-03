"""카카오툴즈 호환 MCP 서버.

툴 정의는 ``tools/`` 아래 모듈에 있고, ``tools/__init__.py`` 의 ``REGISTER_TOOLS``
에 있는 것만 등록된다. 각 툴은 결과 모델 최상위에 ``widget`` / ``copy_text`` (카카오툴즈
응답) 를 실어 돌려준다.
"""

from __future__ import annotations

import logging
import os

from mcp.server.fastmcp import FastMCP

from tools import register_tools

mcp = FastMCP(
    name="shinhan-credit-card-guide",
    instructions="신한카드 상품 추천과 카드 상세 정보를 카카오툴즈 위젯 형식으로 제공합니다.",
    stateless_http=True,
    json_response=True,
    streamable_http_path="/mcp",
    host=os.getenv("HOST", "0.0.0.0"),
    port=int(os.getenv("PORT", "8080")),
)
# FastMCP 생성자에는 version 인자가 없어 initialize 응답의 serverInfo.version 을 직접 맞춘다.
mcp._mcp_server.version = "0.0.1"

# 사내 스타일 `@mcp.tool(tags={"scope:..."})` 지원.
# 공식 mcp SDK 의 FastMCP.tool 에는 tags 인자가 없어 meta["tags"] 로 접어 넣는다.
_fastmcp_tool = mcp.tool


def _tool(*args, tags: set[str] | None = None, meta: dict | None = None, **kwargs):
    merged_meta = dict(meta or {})
    if tags:
        merged_meta.setdefault("tags", sorted(tags))
    return _fastmcp_tool(*args, meta=merged_meta, **kwargs)


mcp.tool = _tool

register_tools(mcp)


def main() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
