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

from domain.credit_card_name import CREDIT_CARD_NAMES, parameter_description
from kakao.card_search import card_name_clarification, credit_card_detail
from mci.card_client import create_card_client
from tools.common import card_detail_from_mci, json_widget, log_tool_request



logger = logging.getLogger(__name__)

_TITLE = "신한카드 상품 상세 조회"
_ERROR_MESSAGE = "### 카드 정보를 불러오지 못했습니다.\n\n잠시 후 다시 시도해 주세요."
_DESCRIPTION = (
    "Retrieves details for a specific Shinhan Card(신한카드) product. Use when the user "
    "asks about the benefits, annual fee, eligibility, or other details of a named card. "
    "Resolve the user's wording to one supported cardName value before calling."
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
                description=parameter_description(),
                json_schema_extra={"enum": CREDIT_CARD_NAMES},
            ),
        ],
    ) -> str:
        log_tool_request(_TOOL_NAME, {"cardName": cardName})
        try:
            result = client.call_with_itf_id(
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
            
            valid_cards = [
                card for card in cards
                if card.CRD_PD_NM.strip() in CREDIT_CARD_NAMES
            ]   
            
            # 2. 필터링 결과 확인d
            logger.info(
                "필터링 결과 - valid=%s / total=%d",
                [card.CRD_PD_NM.strip() for card in valid_cards],
                len(cards),
            )

            if not valid_cards:
                logger.info("지원하지 않는 카드 상품명 - MCI 응답 카드명=%s 이 CREDIT_CARD_NAMES에 없음",
                    [card.CRD_PD_NM for card in cards],
                )
                return json_widget(card_name_clarification(), tool_name=_TOOL_NAME)

            return json_widget(credit_card_detail(valid_cards[0]), tool_name=_TOOL_NAME)

        except Exception as exception:
            logger.exception("MCP 툴 처리 실패 - tool=getCreditCardDetail")
            raise RuntimeError(_ERROR_MESSAGE) from exception
