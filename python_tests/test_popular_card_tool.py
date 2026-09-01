import json

import pytest

from app import deps
from app.mcp_server import mcp

get_popular_credit_cards = mcp._tool_manager.get_tool("getPopularCreditCards").fn


def _card_name(row: dict) -> str:
    return row["children"][2]["children"][0]["value"]


def test_returns_promised_five_cards_in_ranking_order() -> None:
    payload = json.loads(get_popular_credit_cards())
    children = payload["widget"]["children"]

    assert len(children) == 4
    assert "인기 TOP5" in children[0]["value"]

    card_rows = children[2]["children"]
    assert len(card_rows) == 5
    assert _card_name(card_rows[0]) == "신한카드 Deep Oil"
    assert _card_name(card_rows[1]) == "신한카드 Mr.Life"
    assert _card_name(card_rows[2]) == "신한카드 Air One"
    assert _card_name(card_rows[3]) == "신한카드 Point Plan"
    assert _card_name(card_rows[4]) == "신한카드 SOL트래블 체크"

    assert card_rows[0]["children"][0]["value"] == "🥇"
    assert card_rows[1]["children"][0]["value"] == "🥈"
    assert card_rows[2]["children"][0]["value"] == "🥉"
    assert card_rows[3]["children"][0]["value"] == "4"
    assert card_rows[4]["children"][0]["value"] == "5"

    for row in card_rows:
        assert row["children"][1]["type"] == "Image"
        assert row["children"][1]["src"].startswith("https://")
        assert row["children"][2]["children"][1]["children"][0]["type"] == "Badge"

    assert card_rows[0]["children"][1]["src"] == (
        "https://cdn.www.shinhancard.com/pconts/static/images/card/plate/BIABE0_E5_v_f_s.webp"
    )
    assert children[3]["type"] == "Button"
    assert children[3]["label"] == "신한카드 TOP10 차트 보러가기"

    copy_text = payload["copy_text"]
    for fragment in (
        "1. **신한카드 Deep Oil**",
        "2. **신한카드 Mr.Life**",
        "3. **신한카드 Air One**",
        "4. **신한카드 Point Plan**",
        "5. **신한카드 SOL트래블 체크**",
    ):
        assert fragment in copy_text


def test_unexpected_failure_returns_sanitized_message(monkeypatch) -> None:
    def _boom(*_args, **_kwargs):
        raise RuntimeError("internal details")

    monkeypatch.setattr(deps.popular_service, "find_popular_cards", _boom)

    with pytest.raises(RuntimeError) as exc_info:
        get_popular_credit_cards()
    assert str(exc_info.value) == (
        "### 인기 카드 정보를 불러오지 못했습니다.\n\n잠시 후 다시 시도해 주세요."
    )
