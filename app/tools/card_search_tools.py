"""getCreditCardDetail — 지정한 신한카드 한 장의 상세 조회.

Java ``CreditCardDetailToolConfig`` 대응. Java 는 이 툴만 수동 스키마라
최상위 title 이 비어 있고 annotations.title 에만 값이 있다.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated

from mcp.types import ToolAnnotations
from pydantic import Field

from app import deps
from app.domain.credit_card_name import CREDIT_CARD_NAMES, parameter_description
from app.tools.common import json_widget
from app.widgets import card_search_widgets

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

_ERROR_MESSAGE = "### 카드 정보를 불러오지 못했습니다.\n\n잠시 후 다시 시도해 주세요."
_TITLE = "신한카드 상품 상세 조회"
_DESCRIPTION = (
    "Retrieves details for a specific Shinhan Card(신한카드) product. Use when the user "
    "asks about the benefits, annual fee, eligibility, or other details of a named card. "
    "Resolve the user's wording to one supported cardName value before calling."
)


def register_card_search_tools(mcp: "FastMCP") -> None:
    @mcp.tool(
        name="getCreditCardDetail",
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
        cardName: Annotated[  # noqa: N803 - PlayMCP 스키마 파라미터명 유지
            str,
            Field(
                description=parameter_description(),
                json_schema_extra={"enum": CREDIT_CARD_NAMES},
            ),
        ],
    ) -> str:
        """지정한 신한카드 한 장의 혜택/연회비 상세를 위젯으로 보여준다."""
        logger.info("MCP 툴 파라미터 - tool=getCreditCardDetail, cardName=%s", cardName)
        try:
            try:
                detail = deps.guide_service.find_card_detail(cardName)
                payload = card_search_widgets.credit_card_detail(detail)
            except ValueError:
                payload = card_search_widgets.card_name_clarification()
            return json_widget(payload)
        except Exception as exception:  # noqa: BLE001
            logger.exception("MCP 툴 처리 실패 - tool=getCreditCardDetail")
            raise RuntimeError(_ERROR_MESSAGE) from exception
