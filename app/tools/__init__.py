"""MCP 툴 등록.

``REGISTER_TOOLS`` 에 넣은 등록 함수만 서버에 실행된다. 특정 툴을 끄고 싶으면
이 리스트에서 빼면 되고, ``tools/list`` 에도 노출되지 않는다.

각 툴 모듈은 ``register_<모듈>_tools(mcp)`` 함수를 제공하고, 그 안에서
``@mcp.tool(...)`` 로 실제 툴 함수를 등록한다.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from app.tools.card_finer_tools import register_card_finer_tools
from app.tools.card_search_tools import register_card_search_tools
from app.tools.finance_tips_tools import register_finance_tips_tools
from app.tools.popular_card_tools import register_popular_card_tools

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

# 서버에 등록할 툴. 여기서 빼면 해당 툴은 비활성화된다.
REGISTER_TOOLS: list[Callable[["FastMCP"], None]] = [
    register_card_finer_tools,
    register_card_search_tools,
    register_finance_tips_tools,
    register_popular_card_tools,
]


def register_tools(mcp: "FastMCP") -> None:
    """``REGISTER_TOOLS`` 에 있는 등록 함수만 ``mcp`` 에 실행한다."""
    for register in REGISTER_TOOLS:
        register(mcp)
