"""getPopularCreditCards — 신한카드 인기 TOP5 (파라미터 없음).

Java ``PopularCreditCardToolConfig`` 대응.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from mcp.types import ToolAnnotations

from app import deps
from app.tools.common import json_widget
from app.widgets import popular_card_widgets

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

_ERROR_MESSAGE = "### 인기 카드 정보를 불러오지 못했습니다.\n\n잠시 후 다시 시도해 주세요."
_TITLE = "신한카드 인기 TOP5"
_DESCRIPTION = (
    "Returns the current top five popular Shinhan Card(신한카드) products. Use when the "
    "user asks for popular, trending, best-selling, or most-issued cards. This tool requires no "
    "parameters and returns the ranking in popularity order."
)


def register_popular_card_tools(mcp: "FastMCP") -> None:
    @mcp.tool(
        name="getPopularCreditCards",
        title=_TITLE,
        description=_DESCRIPTION,
        annotations=ToolAnnotations(
            title=_TITLE,
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )
    def get_popular_credit_cards() -> str:
        """신한카드 발급량 상위 5개 상품을 순위 순으로 보여준다."""
        try:
            popular_cards = deps.popular_service.find_popular_cards()
            logger.info(
                "MCP 툴 호출 완료 - tool=getPopularCreditCards, count=%s",
                len(popular_cards),
            )
            return json_widget(popular_card_widgets.popular_credit_card_list(popular_cards))
        except Exception as exception:  # noqa: BLE001
            logger.exception("MCP 툴 처리 실패 - tool=getPopularCreditCards")
            raise RuntimeError(_ERROR_MESSAGE) from exception
