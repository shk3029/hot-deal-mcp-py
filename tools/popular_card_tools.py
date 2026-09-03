from __future__ import annotations

import traceback

from mcp.types import ToolAnnotations

from kakao.popular_card import popular_credit_card_list
from mci.mci_client import MciClient
from schemas.card_finder_tools_schemas import CardDetail, CardDetailResult
from tools.common import with_kakao

_TITLE = "신한카드 인기 TOP5"
_DESCRIPTION = (
    "Returns the current top five popular Shinhan Card(신한카드) products. Use when the "
    "user asks for popular, trending, best-selling, or most-issued cards. Returns the "
    "ranking in popularity order."
)


def register_popular_card_tools(mcp):
    client = MciClient()

    @mcp.tool(
        tags={"scope:admin", "scope:common", "scope:agca"},
        meta={"tool_code": "TL-COMM-006"},
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
    def fetch_popular_card(
        size: int = 5,
        sort: str = "date",
        tag: str = "best",
        annualFeeMin: int = 0,
        annualFeeMax: int = 5000000,
    ) -> CardDetailResult:
        """
        인기 신한카드 목록을 반환합니다.
        """
        try:
            data = {
                "SIZ": size,
                "QEE": sort,
                "TAG_VL": tag,
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
                return CardDetailResult(error="카드가 없습니다.")

            cards = [
                CardDetail(
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
            return with_kakao(result, popular_credit_card_list(cards))

        except Exception as e:
            print(f"[ERROR] {traceback.format_exc()}")
            return CardDetailResult(error=f"카드 조회 중 오류가 발생했습니다: {e}")
