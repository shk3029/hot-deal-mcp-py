from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class Card(BaseModel):
    CRD_PD_PGE_N:   str = ""
    CRD_PD_NM:      str = ""
    CRD_PD_DESC:    str = ""
    CRD_PD_URL:     str = ""
    CRD_PD_IMG_URL: str = ""
    CRD_PD_AFE:     int = 0
    CRD_PD_BNF_CD:  str = ""
    TAG_BST_VL:     str = ""
    TAG_LAT_VL:     str = ""
    TAG_CSB_VL:     str = ""


class CardDetail(Card):
    CRD_PD_BNF_NM1: str = ""
    CRD_PD_BNF_NM2: str = ""
    CRD_PD_BNF_NM3: str = ""
    CRD_PD_BNF_DL1: str = ""
    CRD_PD_BNF_DL2: str = ""
    CRD_PD_BNF_DL3: str = ""


class CardsResult(BaseModel):
    cards:      list[Card] = []
    totalCount: int = 0
    error:      str | None = None
    # 카카오툴즈 응답. 툴 결과 최상위에 그대로 실려 카카오 쪽에서 바로 렌더된다.
    widget:     dict[str, Any] | None = None
    copy_text:  str = ""


class CardDetailResult(BaseModel):
    cards:      list[CardDetail] = []
    totalCount: int = 0
    error:      str | None = None
    widget:     dict[str, Any] | None = None
    copy_text:  str = ""
