"""카드 조회 클라이언트 선택과 외부 개발용 목업 구현."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Protocol

from domain.industry import Industry

logger = logging.getLogger(__name__)

_DATA_SOURCE_ENV = "CARD_DATA_SOURCE"
_MOCK_SOURCE = "mock"
_MCI_SOURCE = "mci"


class CardClient(Protocol):
    def call_with_itf_id(
            self,
            itf_id: str,
            *,
            data: dict[str, Any],
            include_sensitive: bool = False,
    ) -> dict[str, Any]: ...


def create_card_client() -> CardClient:
    """``CARD_DATA_SOURCE`` 값에 맞는 카드 데이터 클라이언트를 생성한다.
    기본값은 실제 ``mci``이다. 외부망/로컬에서 ``mock``을 명시한 경우에만
    목업 모듈을 지연 로딩하므로 MCI 설정 파일 없이 실행할 수 있다.
    """
    source = os.getenv(_DATA_SOURCE_ENV, _MCI_SOURCE).strip().lower()
    if source == _MCI_SOURCE:
        from mci.mci_client import MciClient
        client: CardClient = MciClient()
    elif source == _MOCK_SOURCE:
        # 기존 feature/mock 동작과 목 데이터를 그대로 사용한다.
        from mci.mock_client import MockMciClient
        client = MockMciClient()
    else:
        raise RuntimeError(
            f"{_DATA_SOURCE_ENV}는 '{_MOCK_SOURCE}' 또는 '{_MCI_SOURCE}'여야 합니다: {source!r}"

        )
    logger.info("Card data source selected: %s", source)
    return client

class MockCardClient:

    def __init__(self, data_path: Path | None = None) -> None:
        path = data_path or Path(__file__).with_name("card_mock_data.json")
        payload = json.loads(path.read_text(encoding="utf-8"))
        self._cards = [hit["_source"] for hit in payload["hits"]["hits"]]

    def call_with_itf_id(
            self,
            itf_id: str,
            *,
            data: dict[str, Any],
            include_sensitive: bool = False,
    ) -> dict[str, Any]:
        del include_sensitive
        if itf_id != "EGN00002":
            raise ValueError(f"지원하지 않는 목업 인터페이스입니다: {itf_id}")
        cards = list(self._cards)
        cards = self._filter_by_annual_fee(cards, data)
        if data.get("MSG"):
            cards = self._search_by_keyword(cards, str(data["MSG"]))
        elif data.get("CRD_BNF"):
            cards = self._filter_by_benefit(cards, data["CRD_BNF"])
        elif data.get("TAG_VL"):
            cards = self._filter_by_tag(cards, str(data["TAG_VL"]))
        cards = self._sort(cards, str(data.get("QEE", "date")))
        total_count = len(cards)
        size = max(0, int(data.get("SIZ", 5)))
        return {
            "GRID1": [self._to_mci_card(card) for card in cards[:size]],
            "TO_CT": total_count,
        }

    @staticmethod
    def _filter_by_annual_fee(
            cards: list[dict[str, Any]], data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        minimum = int(data.get("AFE_MIN_VL", 0))
        maximum = int(data.get("AFE_MAX_VL", 5_000_000))
        return [card for card in cards if minimum <= int(card["pvafeat"]) <= maximum]

    @staticmethod
    def _search_by_keyword(
            cards: list[dict[str, Any]], keyword: str
    ) -> list[dict[str, Any]]:
        normalized = keyword.strip().casefold()
        if not normalized:
            return []
        exact = [card for card in cards if card["pagetitle"].strip().casefold() == normalized]
        if exact:
            return exact
        return [
            card
            for card in cards
            if normalized in card["pagetitle"].casefold()
               or normalized in str(card.get("sh_keyword", "")).casefold()
        ]

    @staticmethod
    def _filter_by_benefit(
            cards: list[dict[str, Any]], benefit: object
    ) -> list[dict[str, Any]]:
        industry = Industry.resolve(benefit)
        if industry is None:
            return []
        card_type = 2 if industry is Industry.YOUTH else 1
        code = str(industry.code)
        return [
            card
            for card in cards
            if code in card.get("svtcd", []) and int(card.get("cardType", 1)) == card_type
        ]


    @staticmethod
    def _filter_by_tag(
            cards: list[dict[str, Any]], tag: str
    ) -> list[dict[str, Any]]:
        field = {
            "best": "pdbstf",
            "latest": "pdpfrf",
            "cashback": "pdcsbf",
        }.get(tag.strip().lower())

        return cards if field is None else [card for card in cards if card.get(field) == "Y"]

    @staticmethod
    def _sort(cards: list[dict[str, Any]], sort: str) -> list[dict[str, Any]]:
        if sort.strip().lower() in {"fee", "annualfee", "연회비순"}:
            return sorted(cards, key=lambda card: (int(card["pvafeat"]), -int(card["pageid"])))
        return sorted(cards, key=lambda card: card["pageid"], reverse=True)

    @staticmethod
    def _to_mci_card(card: dict[str, Any]) -> dict[str, Any]:
        return {
            "CRD_PD_PGE_N": card.get("pageid", ""),
            "CRD_PD_NM": card.get("pagetitle", "").strip(),
            "CRD_PD_DESC": card.get("pagecont", ""),
            "CRD_PD_URL": card.get("pageurl", card.get("url", "")),
            "CRD_PD_IMG_URL": card.get("thumbimgurl", ""),
            "CRD_PD_AFE": card.get("pvafeat", 0),
            "CRD_PD_BNF_CD": ",".join(card.get("svtcd", [])),
            "TAG_BST_VL": card.get("pdbstf", ""),
            "TAG_LAT_VL": card.get("pdpfrf", ""),
            "TAG_CSB_VL": card.get("pdcsbf", ""),
            "CRD_PD_BNF_NM1": card.get("svtpnm1", ""),
            "CRD_PD_BNF_NM2": card.get("svtpnm2", ""),
            "CRD_PD_BNF_NM3": card.get("svtpnm3", ""),
            "CRD_PD_BNF_DL1": card.get("svtptt1", ""),
            "CRD_PD_BNF_DL2": card.get("svtptt2", ""),
            "CRD_PD_BNF_DL3": card.get("svtptt3", ""),
        }