import json

import pytest

from app import deps
from app.mcp_server import mcp
from app.widgets.common import MORE_CARDS_URL as _MORE_CARDS_URL

get_credit_card_recommendations_with_selector = mcp._tool_manager.get_tool(
    "getCreditCardRecommendationsWithSelector"
).fn


def _call(industry=None, annual_fee=None, card_type=None, sort=None) -> dict:
    return json.loads(
        get_credit_card_recommendations_with_selector(industry, annual_fee, card_type, sort)
    )


def test_recommendation_returns_curated_widget_and_markdown_copy_text() -> None:
    payload = _call(5, "0~1만원대")
    widget = payload["widget"]

    assert widget["type"] == "Card"
    assert "size" not in widget
    assert len(widget["children"]) == 2

    card_list = widget["children"][0]
    assert card_list["type"] == "Col"
    assert card_list["gap"] == 4
    assert len(card_list["children"]) == 5

    first_card = card_list["children"][0]
    assert first_card["type"] == "Row"
    assert first_card["gap"] == 4
    assert first_card["padding"]["y"] == 2
    assert first_card["align"] == "center"
    assert len(first_card["children"]) == 3

    click_indicator = first_card["children"][2]
    assert click_indicator["type"] == "Button"
    assert click_indicator["label"] == ">"
    assert click_indicator["variant"] == "ghost"

    detail_rows = first_card["children"][1]["children"]
    assert len(detail_rows) == 3
    first_card_name = detail_rows[0]["value"]
    assert first_card_name

    annual_fee_row = detail_rows[1]
    assert annual_fee_row["type"] == "Row"
    assert len(annual_fee_row["children"]) == 1
    label = annual_fee_row["children"][0]["label"]
    assert label.startswith("연회비 ") and label.endswith("원")

    benefit_category_row = detail_rows[2]
    assert benefit_category_row["type"] == "Row"
    assert benefit_category_row["children"][0]["label"] == "쇼핑"
    assert 1 <= len(benefit_category_row["children"]) <= 3
    assert "특화" not in json.dumps(detail_rows, ensure_ascii=False)

    target = click_indicator["onClickAction"]["payload"]["target"]
    assert target["type"] == "sendUserMessage"
    assert target["properties"]["text"] == f"{first_card_name} 혜택 알려줘"

    more_cards_button = widget["children"][1]
    assert more_cards_button["type"] == "Button"
    assert more_cards_button["label"] == "더 많은 카드 보기"
    assert more_cards_button["onClickAction"]["payload"]["target"]["url"] == _MORE_CARDS_URL

    assert "쇼핑" in payload["copy_text"]
    assert "0~1만원대" in payload["copy_text"]
    assert "체크" not in payload["copy_text"]


def test_explicit_check_card_request_returns_check_cards() -> None:
    payload = _call(5, "제한없음", 2)
    rows = payload["widget"]["children"][0]["children"]
    assert rows
    for row in rows:
        assert "체크" in row["children"][1]["children"][0]["value"]


def test_youth_category_returns_check_cards_even_when_credit_card_type_requested() -> None:
    payload = _call(24, "제한없음", 1)
    assert "신한카드 처음 체크" in payload["copy_text"]


def test_missing_industry_returns_selector_widget() -> None:
    payload = _call(None, "제한없음")
    widget = payload["widget"]

    assert widget["type"] == "Card"
    assert "업종" in widget["children"][0]["value"]

    first_row = widget["children"][1]
    assert first_row["type"] == "Row"
    assert [button["label"] for button in first_row["children"]] == [
        "어디서나",
        "주유",
        "대형마트",
        "편의점",
    ]
    assert len(widget["children"]) == 5
    last_row = widget["children"][4]
    assert [button["label"] for button in last_row["children"]] == ["공항라운지", "여행/숙박"]
    assert payload["copy_text"] == "원하시는 업종을 선택해 주세요."


def test_annual_fee_selector_places_up_to_four_buttons_per_row() -> None:
    payload = _call(5, "지원하지 않는 구간")
    children = payload["widget"]["children"]
    assert children[1]["type"] == "Row"
    assert len(children[1]["children"]) == 3
    assert len(children) == 2


def test_missing_annual_fee_defaults_to_no_limit() -> None:
    payload = _call(15, None)
    card_list = payload["widget"]["children"][0]
    assert 1 <= len(card_list["children"]) <= 5
    assert "항공" in payload["copy_text"]
    assert "제한없음" in payload["copy_text"]

    category_badge = card_list["children"][0]["children"][1]["children"][2]["children"][0]
    assert category_badge["label"] == "마일리지"


def test_category_hidden_from_selector_is_rendered_as_recommendation_badge() -> None:
    payload = _call(11, "제한없음")
    first_card_badges = (
        payload["widget"]["children"][0]["children"][0]["children"][1]["children"][2][
            "children"
        ]
    )
    assert first_card_badges
    assert first_card_badges[0]["label"] == "공과금"


def test_unexpected_failure_returns_only_sanitized_message(monkeypatch) -> None:
    def _boom(*_args, **_kwargs):
        raise RuntimeError("internal database details")

    monkeypatch.setattr(deps.guide_service, "find_guides", _boom)

    with pytest.raises(RuntimeError) as exc_info:
        _call(5, "제한없음")
    assert str(exc_info.value) == (
        "### 카드 정보를 불러오지 못했습니다.\n\n잠시 후 다시 시도해 주세요."
    )
