"""신한카드 인기 TOP5. Java ``PopularCreditCardService`` 의 포팅."""

from __future__ import annotations

from dataclasses import dataclass

from app.services.card_repository import CreditCardDataRepository


@dataclass(frozen=True)
class _PopularCardSpec:
    rank: int
    card_name: str
    category: str


@dataclass(frozen=True)
class PopularCard:
    rank: int
    name: str
    category: str
    image_url: str


_MOCK_POPULAR_CARD_SPECS: list[_PopularCardSpec] = [
    _PopularCardSpec(1, "신한카드 Deep Oil", "주유"),
    _PopularCardSpec(2, "신한카드 Mr.Life", "어디서나"),
    _PopularCardSpec(3, "신한카드 Air One", "마일리지"),
    _PopularCardSpec(4, "신한카드 Point Plan", "어디서나"),
    _PopularCardSpec(5, "신한카드 SOL트래블 체크", "여행"),
]


class PopularCreditCardService:
    def __init__(self, card_repository: CreditCardDataRepository) -> None:
        self._card_repository = card_repository

    def find_popular_cards(self) -> list[PopularCard]:
        popular_cards: list[PopularCard] = []
        for spec in _MOCK_POPULAR_CARD_SPECS:
            card = self._card_repository.find_by_exact_title(spec.card_name)
            popular_cards.append(
                PopularCard(
                    rank=spec.rank,
                    name=card.title,
                    category=spec.category,
                    image_url=card.image_url,
                )
            )
        return popular_cards
