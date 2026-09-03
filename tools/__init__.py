"""MCP 툴 등록.

``REGISTER_TOOLS`` 에 넣은 등록 함수만 서버에 실행된다. 특정 툴을 끄고 싶으면
이 리스트에서 빼면 되고, ``tools/list`` 에도 노출되지 않는다.
"""

from __future__ import annotations

from tools.card_finder_tools import register_card_finder_tools
from tools.card_search_tools import register_card_search_tools
from tools.finance_tips_tools import register_finance_tips_tools
from tools.popular_card_tools import register_popular_card_tools

REGISTER_TOOLS = [
    register_card_finder_tools,
    register_card_search_tools,
    register_popular_card_tools,
    register_finance_tips_tools,
]


def register_tools(mcp) -> None:
    for register in REGISTER_TOOLS:
        register(mcp)
