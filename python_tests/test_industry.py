import pytest

from app.domain.industry import Industry


def test_tool_search_supports_all_industries_while_widget_shows_only_selected() -> None:
    assert len(list(Industry)) == 24
    assert Industry.selector_display_names() == [
        "어디서나",
        "주유",
        "대형마트",
        "편의점",
        "쇼핑",
        "영화/공연",
        "외식/배달",
        "대중교통",
        "병원/약국",
        "통신",
        "교육/육아",
        "마일리지",
        "공항라운지",
        "여행/숙박",
    ]
    assert Industry.from_code(8) is Industry.CAFE
    assert Industry.from_code(24) is Industry.YOUTH


def test_widget_display_name_overrides() -> None:
    assert Industry.AIRLINE.widget_display_name == "마일리지"
    assert Industry.AIRPORT.widget_display_name == "공항라운지"
    assert Industry.SHOPPING.widget_display_name == "쇼핑"


def test_from_code_rejects_unknown() -> None:
    with pytest.raises(ValueError):
        Industry.from_code(99)
