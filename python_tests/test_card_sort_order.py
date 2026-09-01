import pytest

from app.domain.card_sort_order import CardSortOrder


def test_missing_sort_defaults_to_release_date() -> None:
    assert CardSortOrder.from_string(None) is CardSortOrder.RELEASE_DATE
    assert CardSortOrder.from_string(" ") is CardSortOrder.RELEASE_DATE


def test_parses_supported_sort_names_ignoring_spaces() -> None:
    assert CardSortOrder.from_string("출시일 순") is CardSortOrder.RELEASE_DATE
    assert CardSortOrder.from_string("연회비순") is CardSortOrder.ANNUAL_FEE


def test_rejects_unsupported_sort_name() -> None:
    with pytest.raises(ValueError):
        CardSortOrder.from_string("인기순")
