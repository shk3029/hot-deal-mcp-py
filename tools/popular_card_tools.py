"""feature/test 호환 인기 카드 TOP5 툴."""

from __future__ import annotations

import logging
from typing import Any

from mcp.types import ToolAnnotations

from kakao.popular_card import popular_credit_card_list
from mci.card_client import create_card_client
from tools.common import card_detail_from_mci, json_widget, log_tool_request

logger = logging.getLogger(__name__)

_TITLE = "신한카드 인기 TOP5"
_ERROR_MESSAGE = "### 인기 카드 정보를 불러오지 못했습니다.\n\n잠시 후 다시 시도해 주세요."
_DESCRIPTION = (
    "Returns the current top five popular Shinhan Card(신한카드) products. Use when the "
    "user asks for popular, trending, best-selling, or most-issued cards. This tool requires no "
    "parameters and returns the ranking in popularity order."
)
_TOOL_NAME = "getPopularCreditCards"


def register_popular_card_tools(mcp: Any) -> None:
    client = create_card_client()

    @mcp.tool(
        name=_TOOL_NAME,
        tags={"scope:admin", "scope:common", "scope:agca"},
        meta={"tool_code": "TL-COMM-006"},
        title=_TITLE,
        description=_DESCRIPTION,
        structured_output=False,
        annotations=ToolAnnotations(
            title=_TITLE,
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )
    def get_popular_credit_cards() -> str:
        log_tool_request(_TOOL_NAME, {})
        try:
            result = client.call_with_itf_id(
                "EGN00001",
                data={
                    "SIZ": 5,
                    "QEE": "date",
                    "TAG_VL": "best",
                    "AFE_MIN_VL": 0,
                    "AFE_MAX_VL": 5_000_000,
                },
                include_sensitive=True,
            )
            if not isinstance(result, dict) or not isinstance(result.get("GRID1", []), list):
                raise TypeError("MCI 인기 카드 응답 형식이 올바르지 않습니다.")
            cards = [
                card_detail_from_mci(item)
                for item in result.get("GRID1", [])
                if isinstance(item, dict)
            ]
            return json_widget(
                popular_credit_card_list(cards[:5]),
                tool_name=_TOOL_NAME,
            )
        except Exception as exception:
            logger.exception("MCP 툴 처리 실패 - tool=getPopularCreditCards")
            raise RuntimeError(_ERROR_MESSAGE) from exception
