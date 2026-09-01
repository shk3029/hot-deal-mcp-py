"""카드 추천/상세 도메인 서비스. Java ``CreditCardGuideService`` 의 포팅."""

from __future__ import annotations

import random
from dataclasses import dataclass

from app.domain.annual_fee_band import AnnualFeeBand
from app.domain.card_sort_order import CardSortOrder
from app.domain.credit_card_name import resolve_card_name
from app.domain.industry import Industry
from app.services.card_repository import CreditCardDataRepository

_MAX_SEARCH_RESULTS = 5


@dataclass(frozen=True)
class CardGuide:
    issuer: str
    name: str
    annual_fee: str
    benefit_categories: list[str]
    benefits: list[str]
    image_url: str


@dataclass(frozen=True)
class CardDetail:
    issuer: str
    name: str
    annual_fee: str
    benefits: list[str]
    detail_page_url: str
    image_url: str


class CreditCardGuideService:
    def __init__(self, card_repository: CreditCardDataRepository) -> None:
        self._card_repository = card_repository

    def find_guides(
        self,
        industry_code: int,
        annual_fee_band: AnnualFeeBand,
        card_type: int,
        sort_order: CardSortOrder,
    ) -> list[CardGuide]:
        industry = Industry.from_code(industry_code)
        cards = self._card_repository.search(
            industry_code,
            annual_fee_band,
            card_type,
            sort_order,
            _MAX_SEARCH_RESULTS,
        )
        return [
            CardGuide(
                issuer="신한카드",
                name=card.title,
                annual_fee=_format_annual_fee(card.annual_fee),
                benefit_categories=_benefit_categories(industry, card.benefit_codes),
                benefits=card.benefits,
                image_url=card.image_url,
            )
            for card in cards
        ]

    def find_card_detail(self, card_name: str | None) -> CardDetail:
        exact_card_name = resolve_card_name(card_name)
        card = self._card_repository.find_by_exact_title(exact_card_name)
        return CardDetail(
            issuer="신한카드",
            name=card.title,
            annual_fee=_format_annual_fee(card.annual_fee),
            benefits=card.benefits,
            detail_page_url=card.detail_page_url,
            image_url=card.image_url,
        )


def _benefit_categories(
    searched_industry: Industry,
    card_benefit_codes: list[str],
) -> list[str]:
    other_categories: list[str] = []
    for benefit_code in card_benefit_codes:
        try:
            industry = Industry.from_code(int(benefit_code))
        except ValueError:
            # 알 수 없는 코드는 위젯에 노출하지 않는다.
            continue
        name = industry.widget_display_name
        if industry is not searched_industry and name not in other_categories:
            other_categories.append(name)

    random.shuffle(other_categories)
    return [searched_industry.widget_display_name, *other_categories[:2]]


def _format_annual_fee(annual_fee: int) -> str:
    return f"{annual_fee:,}원"
