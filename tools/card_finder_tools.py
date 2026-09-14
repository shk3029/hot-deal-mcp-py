from __future__ import annotations
import asyncio
import json
from pathlib import Path
from datetime import date, timedelta
from mci.mci_client import MciClient
from schemas.card_finder_tools_schemas import (
    Card,
    CardsResult
)
import logging
import re
from typing import Annotated, Any

from mcp.types import ToolAnnotations
from pydantic import Field

from domain.annual_fee_band import AnnualFeeBand
from domain.card_sort_order import CardSortOrder
from kakao.card_finder import credit_card_guide_list, industry_selector
from mci.card_client import create_card_client
from schemas.card_finder_tools_schemas import CardDetail
from tools.common import call_card_interface, source_logger, card_detail_from_mci, json_widget, log_tool_request
from domain.industry import Industry  



logger = logging.getLogger(__name__)

_TITLE = "소비 업종별 카드 안내 (선택 위젯)"
_ERROR_MESSAGE = "### 카드 정보를 불러오지 못했습니다.\n\n잠시 후 다시 시도해 주세요."
_DESCRIPTION = (
    "Recommends Shinhan Card(신한카드) credit cards based on the user's preferred spending "
    "category and annual-fee range. "
    "MUST be called for ANY card recommendation request, including vague requests like "
    "'카드 추천해줘', '나에게 맞는 카드', '좋은 카드 알려줘', '신한카드 추천' — "
    "even when no specific category or fee is mentioned. "
    "Use for credit card recommendations, comparisons, or category-specific benefits. "
    "Pass the closest supported category code as industry; "
    "omit it (set to null) when the user does not specify a category — this will show a category selector widget. "
    "Set annualFee to EXACTLY one of: 0~1만원, 1~2만원, 2~3만원, 3~4만원, 4~5만원, 5~10만원, 10만원이상, 제한없음. "
    "If the user mentions a fee above 10만원 or says '비싼', '고급', use 10만원 이상. "
    "Always set annualFee; use 제한없음 when the user does not specify a range. "
    "Recommend credit cards by default. Set cardType to 2 only when the user explicitly "
    "asks for a check card; youth category requests automatically return check cards. "
    "Set sort to 정확도순, 출시일순, 높은연회비순, or 낮은연회비순; "
    "default to 출시일순 when the user does not specify sorting."
)
_CREDIT_CARD_TYPE = 1
_CHECK_CARD_TYPE = 2
_MCI_SEARCH_SIZE = 30
_MAX_RESULTS = 5
_TOOL_NAME = "getCreditCardRecommendationsWithSelector"


def register_card_finder_tools(mcp: Any) -> None:
    client = create_card_client()

    @mcp.tool(
        name=_TOOL_NAME,
        tags={"scope:admin", "scope:common", "scope:agca"},
        meta={"tool_code": "TL-COMM-004"},
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
            Field(description=(
                "사용자가 할인이나 혜택을 원하는 업종에 해당하는 번호(1~24). "
                "업종을 명시하지 않은 경우 반드시 null로 설정 — 업종 선택 위젯이 표시됩니다. "
                "허용값: 1 어디서나, 2 주유, 3 대형마트, 4 편의점, 5 쇼핑, 6 영화/공연, 7 외식/배달, 8 카페, "
                "9 대중교통, 10 병원/약국, 11 공과금, 12 통신, 13 교육/육아, 14 레저, 15 항공/마일리지, "
                "16 공항/공항라운지, 17 뷰티, 18 간편결제, 19 구독, 20 여행/숙박, 21 금융, 22 할인, 23 적립, 24 청소년"
            )),
        ] = None,
        annualFee: Annotated[
            str | None,
            Field(description=(
                "사용자가 원하는 연회비 구간. "
                "반드시 아래 허용값 중 하나를 정확히 입력해야 합니다: "
                "0~1만원, 1~2만원, 2~3만원, 3~4만원, 4~5만원, 5~10만원, 10만원이상, 제한없음. "
                "언급이 없거나 상관없으면 반드시 제한없음으로 설정. "
                "10만원 초과 또는 고급/프리미엄 카드 요청 시 10만원 이상 사용. "
                "절대 허용값 외의 문자열을 사용하지 말 것."
            )),
        ] = None,
        cardType: Annotated[
            int | None,
            Field(description=(
                "카드 종류. 1은 신용카드, 2는 체크카드입니다. 사용자가 체크카드를 명시적으로 요청한 경우에만 2를 "
                "사용하고, 그 외에는 생략하거나 1을 사용합니다. 청소년 업종(24)은 값과 관계없이 체크카드로 조회됩니다."
            )),
        ] = None,
        sort: Annotated[
            str | None,
            Field(description=(
                "정렬 기준. "
                "허용값: 정확도순, 출시일순, 높은연회비순, 낮은연회비순. "
                "언급이 없으면 출시일순을 사용합니다. "
                "정확도순은 검색 적합도 기준, 출시일순은 최신 출시 카드부터, "
                "높은연회비순은 높은 연회비부터, 낮은연회비순은 낮은 연회비부터 정렬합니다."
            )),
        ] = None,
    ) -> str:
        print(f"[DEBUG] ▶ 툴 함수 진입! industry={industry!r}, annualFee={annualFee!r}, cardType={cardType!r}, sort={sort!r}")
        log_tool_request(
            _TOOL_NAME,
            {
                "industry": industry,
                "annualFee": annualFee,
                "cardType": cardType,
                "sort": sort,
            },
        )
        try:
            return json_widget(
                _recommend(client, industry, annualFee, cardType, sort),
                tool_name=_TOOL_NAME,
            )
        except Exception as exception:
            logger.exception("MCP 툴 처리 실패 - tool=getCreditCardRecommendationsWithSelector")
            raise RuntimeError(_ERROR_MESSAGE) from exception


def _recommend(
    client: Any,
    industry_code: int | None,
    annual_fee: str | None,
    card_type: int | None,
    sort: str | None,
) -> dict[str, Any]:
    print(f"[DEBUG] annual_fee1: {annual_fee}")
    if industry_code is None:
        source_logger.info("tool=%s source=none status=selector", _TOOL_NAME)
        return industry_selector()
    try:
        industry = Industry.from_code(industry_code)
    except ValueError:
        source_logger.info("tool=%s source=none status=selector", _TOOL_NAME)
        return industry_selector()
    try:
        print(f"[DEBUG] annual_fee2: {annual_fee}")
        fee_band = AnnualFeeBand.from_string(annual_fee)
        print(f"[DEBUG] annual_fee3: {annual_fee}")
    except ValueError:
        fee_band = AnnualFeeBand.from_string("제한없음")  # ✅ 제한없음으로 fallback

    sort_order = CardSortOrder.from_string(sort)
    print(f"[DEBUG] sort 입력: {sort!r} → {sort_order} → {sort_order.api_code}")
    resolved_type = (
        _CHECK_CARD_TYPE
        if industry is Industry.YOUTH or card_type == _CHECK_CARD_TYPE
        else _CREDIT_CARD_TYPE
    )
    type_name = "체크카드" if resolved_type == _CHECK_CARD_TYPE else "신용카드"
    result = call_card_interface(client, tool_name=_TOOL_NAME, itf_id=
        "EGN00002",
        data={
            "CRD_BNF": str(industry.code),
            "CRD_TP": resolved_type,     
            "SIZ": _MCI_SEARCH_SIZE,
            "QEE": sort_order.api_code,
            "AFE_MIN_VL": fee_band.minimum,
            "AFE_MAX_VL": fee_band.maximum,
        },
        include_sensitive=True,
    )
    if not isinstance(result, dict) or not isinstance(result.get("GRID1", []), list):
        raise TypeError("MCI 카드 검색 응답 형식이 올바르지 않습니다.")

    cards = [
        card_detail_from_mci(item)
        for item in result.get("GRID1", [])
        if isinstance(item, dict)
    ]
    cards = [card for card in cards if _matches_industry(card, industry)]
    cards = [card for card in cards if _matches_card_type(card, resolved_type)]
    cards = [card for card in cards if fee_band.matches(card.CRD_PD_AFE)]
    # _sort_cards(cards, sort_order)
    return credit_card_guide_list(cards[:_MAX_RESULTS], industry, fee_band.display_name)


def _matches_industry(card: CardDetail, industry: Industry) -> bool:
    codes = {int(value) for value in re.findall(r"\d+", card.CRD_PD_BNF_CD)}
    return not codes or industry.code in codes


def _matches_card_type(card: CardDetail, card_type: int) -> bool:
    is_check = "체크" in card.CRD_PD_NM
    return is_check if card_type == _CHECK_CARD_TYPE else not is_check


# def _sort_cards(cards: list[CardDetail], order: CardSortOrder) -> None:
#     """
#     API(QEE)에서 이미 정렬된 결과를 반환하므로
#     클라이언트 재정렬은 page_number 기준 보조 정렬만 수행합니다.
#     연회비 정렬은 API에 위임하여 중복 정렬을 방지합니다.
#     """
#     def page_number(card: CardDetail) -> int:
#         digits = "".join(re.findall(r"\d+", card.CRD_PD_PGE_N))
#         return int(digits or 0)

#     # 동일 조건 내 카드명 알파벳순 보조 정렬 (안정 정렬 활용)
#     cards.sort(key=lambda card: card.CRD_PD_NM)

#     # 페이지 번호 기준 보조 정렬만 유지 (API 정렬 순서 최대한 보존)
#     cards.sort(key=page_number, reverse=True)
 

 
