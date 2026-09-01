"""getCreditCardRecommendationsWithSelector — 소비 업종/연회비 조건으로 카드 추천.

Java ``McpToolConfig`` 대응.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated, Any

from mcp.types import ToolAnnotations
from pydantic import Field

from app import deps
from app.domain.annual_fee_band import AnnualFeeBand
from app.domain.card_sort_order import CardSortOrder
from app.domain.industry import Industry
from app.tools.common import json_widget
from app.widgets import card_finer_widgets

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

_CHECK_CARD_TYPE = 2
_CREDIT_CARD_TYPE = 1
_ERROR_MESSAGE = "### 카드 정보를 불러오지 못했습니다.\n\n잠시 후 다시 시도해 주세요."
_TITLE = "소비 업종별 카드 안내 (선택 위젯)"

_DESCRIPTION = (
    "Recommends Shinhan Card(신한카드) credit card benefit types based on the user's "
    "preferred spending category and annual-fee range. Use for credit card recommendations, "
    "comparisons, or category-specific benefits. Pass the closest supported category code as "
    "industry; omit it when unclear to show a selector widget. Set annualFee to 0~1만원대, "
    "2~3만원대, or 제한없음; use 제한없음 when the user does not specify a range. Recommend "
    "credit cards by default. Set cardType to 2 only when the user explicitly asks for a check "
    "card; youth category requests automatically return check cards. Set sort to 출시일순 or "
    "연회비순; default to 출시일순 when the user does not specify sorting."
)


def register_card_finer_tools(mcp: "FastMCP") -> None:
    @mcp.tool(
        name="getCreditCardRecommendationsWithSelector",
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
    def get_credit_card_recommendations_with_selector(
        industry: Annotated[
            int | None,
            Field(
                description=(
                    "사용자가 할인이나 혜택을 원하는 업종에 해당하는 번호(1~24). "
                    "허용값: 1 어디서나, 2 주유, 3 대형마트, 4 편의점, 5 쇼핑, 6 영화/공연, 7 외식/배달, 8 카페, "
                    "9 대중교통, 10 병원/약국, 11 공과금, 12 통신, 13 교육/육아, 14 레저, 15 항공/마일리지, "
                    "16 공항/공항라운지, 17 뷰티, 18 간편결제, 19 구독, 20 여행/숙박, 21 금융, 22 할인, 23 적립, 24 청소년"
                )
            ),
        ] = None,
        annualFee: Annotated[  # noqa: N803 - PlayMCP 스키마 파라미터명 유지
            str | None,
            Field(
                description=(
                    "사용자가 원하는 연회비 구간. '3만원대'는 2~3만원대로 변환합니다. "
                    "허용값: 0~1만원대, 2~3만원대, 제한없음. 언급이 없거나 상관없으면 제한없음"
                )
            ),
        ] = None,
        cardType: Annotated[  # noqa: N803 - PlayMCP 스키마 파라미터명 유지
            int | None,
            Field(
                description=(
                    "카드 종류. 1은 신용카드, 2는 체크카드입니다. 사용자가 체크카드를 명시적으로 요청한 경우에만 2를 "
                    "사용하고, 그 외에는 생략하거나 1을 사용합니다. 청소년 업종(24)은 값과 관계없이 체크카드로 조회됩니다."
                )
            ),
        ] = None,
        sort: Annotated[
            str | None,
            Field(
                description=(
                    "정렬 기준. 허용값: 출시일순, 연회비순. 언급이 없으면 출시일순을 사용합니다. "
                    "출시일순은 최신 출시 카드부터, 연회비순은 낮은 연회비부터 정렬합니다."
                )
            ),
        ] = None,
    ) -> str:
        """소비 업종/연회비 조건으로 신한카드 혜택 유형을 추천한다(PlayMCP 위젯)."""
        logger.info(
            "MCP 툴 파라미터 - tool=getCreditCardRecommendationsWithSelector, "
            "industry=%s, annualFee=%s, cardType=%s, sort=%s",
            industry,
            annualFee,
            cardType,
            sort,
        )
        try:
            return json_widget(
                _recommend_credit_cards(industry, annualFee, cardType, sort)
            )
        except Exception as exception:  # noqa: BLE001 - Java 와 동일하게 메시지를 무해화
            logger.exception(
                "MCP 툴 처리 실패 - tool=getCreditCardRecommendationsWithSelector"
            )
            raise RuntimeError(_ERROR_MESSAGE) from exception


def _recommend_credit_cards(
    industry: int | None,
    annual_fee: str | None,
    card_type: int | None,
    sort: str | None,
) -> dict[str, Any]:
    if industry is None:
        return card_finer_widgets.industry_selector()
    try:
        parsed_industry = Industry.from_code(industry)
    except ValueError:
        return card_finer_widgets.industry_selector()

    try:
        parsed_annual_fee = AnnualFeeBand.from_string(annual_fee)
    except ValueError:
        return card_finer_widgets.annual_fee_selector()

    parsed_sort_order = CardSortOrder.from_string(sort)

    resolved_card_type = _resolve_card_type(parsed_industry, card_type)
    guides = deps.guide_service.find_guides(
        parsed_industry.code,
        parsed_annual_fee,
        resolved_card_type,
        parsed_sort_order,
    )
    return card_finer_widgets.credit_card_guide_list(
        guides, parsed_industry, parsed_annual_fee
    )


def _resolve_card_type(industry: Industry, requested_card_type: int | None) -> int:
    if industry is Industry.YOUTH or requested_card_type == _CHECK_CARD_TYPE:
        return _CHECK_CARD_TYPE
    return _CREDIT_CARD_TYPE
