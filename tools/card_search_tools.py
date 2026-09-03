from __future__ import annotations

import traceback

from mcp.types import ToolAnnotations

from kakao.card_search import card_name_clarification, credit_card_detail
from mci.mci_client import MciClient
from schemas.card_finder_tools_schemas import CardDetail, CardDetailResult
from tools.common import with_kakao

_TITLE = "신한카드 상품 상세 조회"
_DESCRIPTION = (
    "Retrieves details for a specific Shinhan Card(신한카드) product. Use when the user "
    "asks about the benefits, annual fee, eligibility, or other details of a named card. "
    "Resolve the user's wording to one supported card name before calling."
)


def register_card_search_tools(mcp):
    client = MciClient()

    @mcp.tool(
        tags={"scope:admin", "scope:common", "scope:agca"},
        meta={"tool_code": "TL-COMM-005"},
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
    def fetch_card_search(
        size: int = 5,
        keyword: str = "",
        sort: str = "score",
        annualFeeMin: int = 0,
        annualFeeMax: int = 5000000,
    ) -> CardDetailResult:
        """
        키워드(카드명)로 신한카드 상품 한 장의 상세 정보를 조회합니다.
        """
        if not keyword or not keyword.strip():
            raise ValueError("keyword는 필수 입력값입니다.")

        try:
            data = {
                "MSG": keyword,
                "SIZ": size,
                "QEE": sort,
                "AFE_MIN_VL": annualFeeMin,
                "AFE_MAX_VL": annualFeeMax,
            }

            ret = client.call_with_itf_id("EGN00001", data=data, include_sensitive=True)

            print(f"[DEBUG] ret type: {type(ret)}")
            print(f"[DEBUG] ret value: {ret}")

            if not isinstance(ret, dict):
                return CardDetailResult(
                    error=f"카드 조회 결과를 가져오지 못했습니다. (ret type: {type(ret)})"
                )

            grid1 = ret.get("GRID1", [])

            print(f"[DEBUG] grid1: {grid1}")

            if not grid1:
                return with_kakao(
                    CardDetailResult(error="해당 카드를 찾지 못했습니다."),
                    card_name_clarification(),
                )

            cards = [
                CardDetail(
                    CRD_PD_PGE_N=item.get("CRD_PD_PGE_N", ""),
                    CRD_PD_NM=item.get("CRD_PD_NM", ""),
                    CRD_PD_DESC=item.get("CRD_PD_DESC", ""),
                    CRD_PD_URL=item.get("CRD_PD_URL", ""),
                    CRD_PD_IMG_URL=item.get("CRD_PD_IMG_URL", ""),
                    CRD_PD_AFE=item.get("CRD_PD_AFE", 0),
                    CRD_PD_BNF_CD=item.get("CRD_PD_BNF_CD", ""),
                    CRD_PD_BNF_NM1=item.get("CRD_PD_BNF_NM1", ""),
                    CRD_PD_BNF_NM2=item.get("CRD_PD_BNF_NM2", ""),
                    CRD_PD_BNF_NM3=item.get("CRD_PD_BNF_NM3", ""),
                    CRD_PD_BNF_DL1=item.get("CRD_PD_BNF_DL1", ""),
                    CRD_PD_BNF_DL2=item.get("CRD_PD_BNF_DL2", ""),
                    CRD_PD_BNF_DL3=item.get("CRD_PD_BNF_DL3", ""),
                )
                for item in grid1
            ]

            result = CardDetailResult(
                cards=cards, totalCount=ret.get("TO_CT", len(cards))
            )
            return with_kakao(result, credit_card_detail(cards[0]))

        except Exception as e:
            print(f"[ERROR] {traceback.format_exc()}")
            return CardDetailResult(error=f"카드 조회 중 오류가 발생했습니다: {e}")
