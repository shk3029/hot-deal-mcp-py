import pytest

from app.domain.annual_fee_band import AnnualFeeBand
from app.domain.card_sort_order import CardSortOrder
from app.domain.credit_card_name import CREDIT_CARD_NAMES
from app.services.card_repository import CreditCardDataRepository


@pytest.fixture(scope="module")
def repository() -> CreditCardDataRepository:
    return CreditCardDataRepository()


def test_every_supported_card_name_has_an_exact_data_match(
    repository: CreditCardDataRepository,
) -> None:
    assert len(CREDIT_CARD_NAMES) == 81
    assert len(set(CREDIT_CARD_NAMES)) == 81
    for name in CREDIT_CARD_NAMES:
        assert repository.find_by_exact_title(name).title == name


def test_title_lookup_does_not_use_fuzzy_matching(
    repository: CreditCardDataRepository,
) -> None:
    with pytest.raises(ValueError):
        repository.find_by_exact_title("신한카드 sol트래블 체크")


def test_search_filters_by_benefit_code_and_annual_fee_band(
    repository: CreditCardDataRepository,
) -> None:
    cards = repository.search(
        5, AnnualFeeBand.TEN_THOUSAND_RANGE, 1, CardSortOrder.RELEASE_DATE, 3
    )
    assert len(cards) == 3
    for card in cards:
        assert "5" in card.benefit_codes
        assert 0 <= card.annual_fee <= 19_999
        assert card.card_type == 1


def test_search_filters_by_check_card_type(
    repository: CreditCardDataRepository,
) -> None:
    cards = repository.search(
        5, AnnualFeeBand.NO_LIMIT, 2, CardSortOrder.RELEASE_DATE, 100
    )
    assert cards
    assert all(card.card_type == 2 for card in cards)


def test_search_sorts_by_newest_release_date_by_default(
    repository: CreditCardDataRepository,
) -> None:
    cards = repository.search(
        5, AnnualFeeBand.NO_LIMIT, 1, CardSortOrder.RELEASE_DATE, 100
    )
    page_ids = [card.page_id for card in cards]
    assert page_ids == sorted(page_ids, reverse=True)


def test_search_sorts_by_lowest_annual_fee(
    repository: CreditCardDataRepository,
) -> None:
    cards = repository.search(
        5, AnnualFeeBand.NO_LIMIT, 1, CardSortOrder.ANNUAL_FEE, 100
    )
    fees = [card.annual_fee for card in cards]
    assert fees == sorted(fees)
