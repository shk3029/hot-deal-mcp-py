"""목업 MCI 백엔드 (feature/mock 전용).

``mci/mock_data.json`` (신한카드 검색 데이터, elasticsearch 덤프 형태) 을 읽어
``EGN00001`` 인터페이스가 돌려주는 ``{"GRID1": [...], "TO_CT": n}`` 응답을 흉내낸다.
MCI 백엔드 없이 카카오툴즈에 붙여 테스트하기 위한 것.

``data`` 딕셔너리로 어떤 조회인지 구분한다.
- ``MSG``     : 카드명 검색 또는 "업종 카드종류" 추천 검색
- ``TAG_VL``  : 인기 카드 (`getPopularCreditCards`)
- ``CRD_BNF`` : 이전 fetch 계약과의 하위 호환용 업종 검색
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from domain.industry import Industry

_DATA_FILE = Path(__file__).resolve().parent / "mock_data.json"

_CHECK_CARD_TYPE = 2
_CREDIT_CARD_TYPE = 1
_SUPPORTED_ITF_IDS = frozenset({"EGN00001", "EGN00002"})

# 기존 PopularCreditCardService 의 목 스펙 (순서 = 랭킹).
_POPULAR_CARD_TITLES: list[str] = [
    "신한카드 Deep Oil",
    "신한카드 Mr.Life",
    "신한카드 Air One",
    "신한카드 Point Plan",
    "신한카드 SOL트래블 체크",
]


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _text(source: dict[str, Any], key: str) -> str:
    value = source.get(key)
    return str(value).strip() if value is not None else ""


class _Row:
    """mock_data.json 의 카드 한 건을 GRID1 항목 + 필터용 메타로 들고 있는다."""

    __slots__ = ("grid", "title", "page_id", "annual_fee", "card_type", "benefit_codes")

    def __init__(self, source: dict[str, Any]) -> None:
        title = _text(source, "pagetitle")
        page_id = _text(source, "pageid")
        annual_fee = _as_int(source.get("pvafeat"))
        card_type = source.get("cardType")
        benefit_codes = [
            str(code) for code in source.get("svtcd", []) if str(code).strip()
        ]

        self.title = title
        self.page_id = page_id
        self.annual_fee = annual_fee
        self.card_type = card_type if card_type in (1, 2) else _CREDIT_CARD_TYPE
        self.benefit_codes = benefit_codes

        self.grid: dict[str, Any] = {
            "CRD_PD_PGE_N": page_id,
            "CRD_PD_NM": title,
            "CRD_PD_DESC": _text(source, "pagecont"),
            "CRD_PD_URL": _text(source, "pageurl"),
            "CRD_PD_IMG_URL": _text(source, "thumbimgurl"),
            "CRD_PD_AFE": annual_fee,
            "CRD_PD_BNF_CD": ",".join(benefit_codes),
            "TAG_BST_VL": _text(source, "pdbstf"),
            "TAG_LAT_VL": _text(source, "pdpfrf"),
            "TAG_CSB_VL": _text(source, "pdcsbf"),
            "CRD_PD_BNF_NM1": _text(source, "svtpnm1"),
            "CRD_PD_BNF_NM2": _text(source, "svtpnm2"),
            "CRD_PD_BNF_NM3": _text(source, "svtpnm3"),
            "CRD_PD_BNF_DL1": _text(source, "svtptt1"),
            "CRD_PD_BNF_DL2": _text(source, "svtptt2"),
            "CRD_PD_BNF_DL3": _text(source, "svtptt3"),
        }


def _load_rows() -> list[_Row]:
    with _DATA_FILE.open(encoding="utf-8") as stream:
        document = json.load(stream)
    hits = document.get("hits", {}).get("hits")
    if not isinstance(hits, list):
        raise RuntimeError("mock_data.json 형식 오류: hits.hits 가 배열이 아닙니다.")
    return [_Row(hit.get("_source", {})) for hit in hits if hit.get("_source")]


def _sort_rows(rows: list[_Row], qee: str | None) -> None:
    """기존 CreditCardDataRepository._sort_in_place 와 동일한 안정 정렬.

    ``CardSortOrder.api_code`` 가 보내는 ``low_rate``/``high_rate`` 도 함께 처리한다.
    """
    normalized = (qee or "").strip().lower()
    if normalized in {"fee", "annualfee", "annual_fee", "afe", "연회비순", "low_rate"}:
        rows.sort(key=lambda row: row.title)
        rows.sort(key=lambda row: row.page_id, reverse=True)
        rows.sort(key=lambda row: row.annual_fee)
    elif normalized == "high_rate":
        rows.sort(key=lambda row: row.title)
        rows.sort(key=lambda row: row.page_id, reverse=True)
        rows.sort(key=lambda row: row.annual_fee, reverse=True)
    else:  # date / score / 출시일순 / 미지정
        rows.sort(key=lambda row: row.title)
        rows.sort(key=lambda row: row.annual_fee)
        rows.sort(key=lambda row: row.page_id, reverse=True)


class MockBackend:
    def __init__(self) -> None:
        self._rows = _load_rows()
        self._by_title = {row.title: row for row in self._rows}

    def call_with_itf_id(
        self,
        itf_id: str,
        data: Any | None = None,
        include_sensitive: bool = False,
    ) -> dict[str, Any]:
        if itf_id not in _SUPPORTED_ITF_IDS:
            return {"GRID1": [], "TO_CT": 0}

        query: dict[str, Any] = dict(data or {})
        size = _as_int(query.get("SIZ")) or 10
        sort = query.get("QEE")

        if str(query.get("MSG") or "").strip():
            return self._keyword_search(query["MSG"], size)
        if str(query.get("TAG_VL") or "").strip():
            return self._popular(size)
        if "CRD_BNF" in query:
            return self._benefit_search(query, size, sort)

        rows = list(self._rows)
        _sort_rows(rows, sort)
        return _grid(rows[:size], len(rows))

    def _keyword_search(self, keyword: Any, size: int) -> dict[str, Any]:
        needle = str(keyword).strip()
        # feature/test 추천 툴은 실제 MCI 검색과 동일하게 "업종 카드종류" 문장을 보낸다.
        for suffix, card_type in ((" 체크카드", _CHECK_CARD_TYPE), (" 신용카드", _CREDIT_CARD_TYPE)):
            if needle.endswith(suffix):
                industry = Industry.resolve(needle[: -len(suffix)])
                if industry is None:
                    return {"GRID1": [], "TO_CT": 0}
                rows = [
                    row
                    for row in self._rows
                    if str(industry.code) in row.benefit_codes and row.card_type == card_type
                ]
                return _grid(rows[:size], len(rows))
        exact = self._by_title.get(needle)
        if exact is not None:
            return _grid([exact], 1)
        matched = [row for row in self._rows if needle and needle in row.title]
        return _grid(matched[:size], len(matched))

    def _popular(self, size: int) -> dict[str, Any]:
        rows = [
            self._by_title[title]
            for title in _POPULAR_CARD_TITLES
            if title in self._by_title
        ]
        return _grid(rows[:size], len(rows))

    def _benefit_search(
        self, query: dict[str, Any], size: int, sort: str | None
    ) -> dict[str, Any]:
        industry = Industry.resolve(query.get("CRD_BNF"))
        if industry is None:
            return {"GRID1": [], "TO_CT": 0}

        fee_min = _as_int(query.get("AFE_MIN_VL"))
        fee_max = query.get("AFE_MAX_VL")
        fee_max = _as_int(fee_max) if fee_max is not None else 5_000_000
        if query.get("CRD_TP") is not None:
            card_type = _as_int(query["CRD_TP"]) or _CREDIT_CARD_TYPE
        else:
            card_type = (
                _CHECK_CARD_TYPE if industry is Industry.YOUTH else _CREDIT_CARD_TYPE
            )
        code = str(industry.code)

        matched = [
            row
            for row in self._rows
            if code in row.benefit_codes
            and fee_min <= row.annual_fee <= fee_max
            and row.card_type == card_type
        ]
        _sort_rows(matched, sort)
        return _grid(matched[:size], len(matched))


def _grid(rows: list[_Row], total: int) -> dict[str, Any]:
    return {"GRID1": [row.grid for row in rows], "TO_CT": total}
