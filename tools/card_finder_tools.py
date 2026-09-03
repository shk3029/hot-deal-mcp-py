from __future__ import annotations

import traceback

from mcp.types import ToolAnnotations

from domain.industry import Industry
from kakao.card_finder import credit_card_guide_list, industry_selector
from kakao.common import annual_fee_range_label
from mci.mci_client import MciClient
from schemas.card_finder_tools_schemas import Card, CardsResult
from tools.common import with_kakao

_TITLE = "소비 업종별 카드 안내 (선택 위젯)"
_DESCRIPTION = (
    "Recommends Shinhan Card(신한카드) credit card benefit types based on the user's "
    "preferred spending category and annual-fee range. Use for credit card recommendations, "
    "comparisons, or category-specific benefits. Pass the closest supported category as "
    "benefitDetail; omit it when unclear to show a selector widget. Recommend credit cards "
    "by default. Youth category requests automatically return check cards. Set sort to date "
    "or fee; default to date when the user does not specify sorting."
)


def register_card_finder_tools(mcp):
    client = MciClient()

    @mcp.tool(
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
    def fetch_card_finder(
        size: int = 10,
        benefitDetail: str = "",
        sort: str = "date",
        annualFeeMin: int = 0,
        annualFeeMax: int = 5000000,
    ) -> CardsResult:
        """
        사용자의 조건(혜택 유형, 연회비 범위)에 맞는 신한카드 상품 목록을 조회합니다.
        """
        # benefitDetail 이 비었거나 업종으로 해석되지 않으면 업종 셀렉터를 띄운다.
        industry = Industry.resolve(benefitDetail)
        if industry is None:
            return with_kakao(CardsResult(), industry_selector())

        try:
            data = {
                "SIZ": size,
                "QEE": sort,
                "CRD_BNF": benefitDetail,
                "AFE_MIN_VL": annualFeeMin,
                "AFE_MAX_VL": annualFeeMax,
            }

            ret = client.call_with_itf_id("EGN00001", data=data, include_sensitive=True)

            print(f"[DEBUG] ret type: {type(ret)}")
            print(f"[DEBUG] ret value: {ret}")

            if not isinstance(ret, dict):
                return CardsResult(
                    error=f"카드 조회 결과를 가져오지 못했습니다. (ret type: {type(ret)})"
                )

            grid1 = ret.get("GRID1", [])

            print(f"[DEBUG] grid1: {grid1}")

            if not grid1:
                return with_kakao(
                    CardsResult(error="조건에 맞는 카드가 없습니다."), industry_selector()
                )

            cards = [
                Card(
                    CRD_PD_PGE_N=item.get("CRD_PD_PGE_N", ""),
                    CRD_PD_NM=item.get("CRD_PD_NM", ""),
                    CRD_PD_DESC=item.get("CRD_PD_DESC", ""),
                    CRD_PD_URL=item.get("CRD_PD_URL", ""),
                    CRD_PD_IMG_URL=item.get("CRD_PD_IMG_URL", ""),
                    CRD_PD_AFE=item.get("CRD_PD_AFE", 0),
                    CRD_PD_BNF_CD=item.get("CRD_PD_BNF_CD", ""),
                    TAG_BST_VL=item.get("TAG_BST_VL", ""),
                    TAG_LAT_VL=item.get("TAG_LAT_VL", ""),
                    TAG_CSB_VL=item.get("TAG_CSB_VL", ""),
                )
                for item in grid1
            ]

            result = CardsResult(cards=cards, totalCount=ret.get("TO_CT", len(cards)))
            return with_kakao(
                result,
                credit_card_guide_list(
                    cards,
                    industry,
                    annual_fee_range_label(annualFeeMin, annualFeeMax),
                ),
            )

        except Exception as e:
            print(f"[ERROR] {traceback.format_exc()}")
            return CardsResult(error=f"카드 조회 중 오류가 발생했습니다: {e}")
