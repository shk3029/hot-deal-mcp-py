from __future__ import annotations
import asyncio
import json
from pathlib import Path
from datetime import date, timedelta
from mci.mci_client import MciClient


import logging
from typing import Annotated, Any

from mcp.types import ToolAnnotations
from pydantic import Field

from kakao.card_search import card_name_clarification, credit_card_detail
from mci.card_client import create_card_client
from tools.common import call_card_interface, source_logger, card_detail_from_mci, json_widget, log_tool_request



logger = logging.getLogger(__name__)

_TITLE = "신한카드 상품 상세 조회"
_ERROR_MESSAGE = "### 카드 정보를 불러오지 못했습니다.\n\n잠시 후 다시 시도해 주세요."
_DESCRIPTION = (
    "Retrieves details for a specific Shinhan Card(신한카드) product. Use when the user "
    "asks about the benefits, annual fee, eligibility, or other details of a named card. "
    "Pass the user-provided product name, preserving symbols such as +. "
    "Never replace a Plus product with a check card or a different product."
)
_TOOL_NAME = "getCreditCardDetail"


def register_card_search_tools(mcp: Any) -> None:
    client = create_card_client()

    @mcp.tool(
        name=_TOOL_NAME,
        tags={"scope:admin", "scope:common", "scope:agca"},
        meta={"tool_code": "TL-COMM-005"},
        description=_DESCRIPTION,
        annotations=ToolAnnotations(
            title=_TITLE,
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )
    def get_credit_card_detail(
        cardName: Annotated[
            str,
            Field(
                description="조회할 카드명. + 등 상품명 기호를 그대로 보존하고 다른 상품명으로 대체하지 마세요.",
            ),
        ],
    ) -> str:
        log_tool_request(_TOOL_NAME, {"cardName": cardName})
        try:
            result = call_card_interface(client, tool_name=_TOOL_NAME, itf_id=
                "EGN00002",
                data={
                    "MSG": cardName,
                    "SIZ": 5,
                    "QEE": "score",
                    "AFE_MIN_VL": 0,
                    "AFE_MAX_VL": 5_000_000,
                },
                include_sensitive=True,
            )
            if not isinstance(result, dict) or not isinstance(result.get("GRID1", []), list):
                raise TypeError("MCI 카드 상세 응답 형식이 올바르지 않습니다.")
            cards = [
                card_detail_from_mci(item)
                for item in result.get("GRID1", [])
                if isinstance(item, dict)
            ]
            
            logger.info(
                "MCI 응답 카드명 목록 - raw=%s",
                [repr(card.CRD_PD_NM) for card in cards]  # repr()로 공백/특수문자 노출
            )
            
            # 상품 기호는 보존하고 공백/대소문자 차이만 허용한다.
            normalize_name = lambda name: "".join(name.split()).casefold().replace("＋", "+")
            exact_cards = [card for card in cards
                           if normalize_name(card.CRD_PD_NM) == normalize_name(cardName)]
            if len(exact_cards) == 1:
                selected = exact_cards[0]
            elif len(cards) == 1 and result.get("TO_CT") == 1:
                selected = cards[0]
            else:
                return json_widget(card_name_clarification(), tool_name=_TOOL_NAME)
            return json_widget(credit_card_detail(selected), tool_name=_TOOL_NAME)

        except Exception as exception:
            logger.exception("MCP 툴 처리 실패 - tool=getCreditCardDetail")
            raise RuntimeError(_ERROR_MESSAGE) from exception
