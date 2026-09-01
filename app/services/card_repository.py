"""``data.json`` 을 읽어 카드 데이터를 조회한다.

Java ``CreditCardDataRepository`` 의 포팅. 키워드 검색은 하지 않고, ``svtcd``(업종코드)
와 ``pvafeat``(연회비, 원), ``cardType`` 필터 + 정렬만 사용한다.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.domain.annual_fee_band import AnnualFeeBand
from app.domain.card_sort_order import CardSortOrder

_DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "data.json"
_CARD_HOST = "https://www.shinhancard.com"
_IMAGE_HOST = "https://cdn.www.shinhancard.com"


@dataclass(frozen=True)
class CardData:
    title: str
    page_id: str
    annual_fee: int
    card_type: int
    benefit_codes: list[str]
    benefits: list[str]
    summary: str
    detail_page_url: str
    image_url: str


class CreditCardDataRepository:
    def __init__(self, data_file: Path | None = None) -> None:
        self._cards = _load_cards(data_file or _DATA_FILE)
        self._cards_by_exact_title = _index_by_exact_title(self._cards)

    def search(
        self,
        industry_code: int,
        annual_fee_band: AnnualFeeBand,
        card_type: int,
        sort_order: CardSortOrder,
        limit: int,
    ) -> list[CardData]:
        category_code = str(industry_code)
        matched = [
            card
            for card in self._cards
            if category_code in card.benefit_codes
            and annual_fee_band.matches(card.annual_fee)
            and card.card_type == card_type
        ]
        _sort_in_place(matched, sort_order)
        return matched[:limit]

    def find_by_exact_title(self, title: str | None) -> CardData:
        if title is None:
            raise ValueError("카드 이름을 입력해주세요.")
        card = self._cards_by_exact_title.get(title.strip())
        if card is None:
            raise ValueError(f"지원하지 않는 카드 이름입니다: {title}")
        return card

    @property
    def cards(self) -> list[CardData]:
        return list(self._cards)


def _sort_in_place(cards: list[CardData], sort_order: CardSortOrder) -> None:
    """Java ``comparatorFor`` 와 동일한 결과가 되도록 안정 정렬을 겹쳐 쓴다.

    RELEASE_DATE: page_id 내림차순 → annual_fee 오름차순 → title 오름차순
    ANNUAL_FEE:   annual_fee 오름차순 → page_id 내림차순 → title 오름차순
    """
    if sort_order is CardSortOrder.RELEASE_DATE:
        cards.sort(key=lambda card: card.title)
        cards.sort(key=lambda card: card.annual_fee)
        cards.sort(key=lambda card: card.page_id, reverse=True)
    else:
        cards.sort(key=lambda card: card.title)
        cards.sort(key=lambda card: card.page_id, reverse=True)
        cards.sort(key=lambda card: card.annual_fee)


def _load_cards(data_file: Path) -> list[CardData]:
    try:
        with data_file.open(encoding="utf-8") as stream:
            document = json.load(stream)
    except OSError as exc:  # pragma: no cover - 파일 배포 누락 방어
        raise RuntimeError("data.json을 불러오지 못했습니다.") from exc

    hits = document.get("hits", {}).get("hits")
    if not isinstance(hits, list):
        raise RuntimeError("data.json의 hits.hits가 배열이 아닙니다.")
    return [_to_card_data(hit.get("_source", {})) for hit in hits]


def _index_by_exact_title(cards: list[CardData]) -> dict[str, CardData]:
    index: dict[str, CardData] = {}
    for card in cards:
        if card.title in index:
            raise RuntimeError(f"중복 카드명입니다: {card.title}")
        index[card.title] = card
    return index


def _to_card_data(source: dict[str, Any]) -> CardData:
    title = _required_text(source, "pagetitle").strip()

    benefits: list[str] = []
    for index in (1, 2, 3):
        name = _text(source, f"svtpnm{index}")
        description = _text(source, f"svtptt{index}")
        if name and description:
            benefits.append(f"{name} · {description}")
        elif name:
            benefits.append(name)
        elif description:
            benefits.append(description)

    return CardData(
        title=title,
        page_id=_required_text(source, "pageid"),
        annual_fee=_as_int(source.get("pvafeat")),
        card_type=_required_card_type(source),
        benefit_codes=[str(code) for code in source.get("svtcd", [])]
        if isinstance(source.get("svtcd"), list)
        else [],
        benefits=benefits,
        summary=_text(source, "pagecont"),
        detail_page_url=_absolute_url(_CARD_HOST, _required_text(source, "pageurl")),
        image_url=_absolute_url(_IMAGE_HOST, _required_text(source, "thumbimgurl")),
    )


def _text(source: dict[str, Any], field_name: str) -> str:
    value = source.get(field_name)
    return str(value).strip() if value is not None else ""


def _required_text(source: dict[str, Any], field_name: str) -> str:
    value = _text(source, field_name)
    if not value:
        raise RuntimeError(f"data.json 필수 필드가 비어 있습니다: {field_name}")
    return value


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _required_card_type(source: dict[str, Any]) -> int:
    card_type = source.get("cardType")
    if card_type not in (1, 2):
        raise RuntimeError("data.json의 cardType은 1 또는 2여야 합니다.")
    return card_type


def _absolute_url(host: str, path: str) -> str:
    if path.startswith(("http://", "https://")):
        return path
    return host + (path if path.startswith("/") else f"/{path}")
