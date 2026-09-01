import json

import pytest

from app import deps
from app.domain.credit_card_name import CREDIT_CARD_NAMES, parameter_description
from app.mcp_server import mcp

get_credit_card_detail = mcp._tool_manager.get_tool("getCreditCardDetail").fn


def _call(card_name: str) -> dict:
    return json.loads(get_credit_card_detail(card_name))


def test_parameter_description_lists_every_supported_card_name() -> None:
    assert len(CREDIT_CARD_NAMES) == 81
    description = parameter_description()
    assert description.startswith("Exact Shinhan Card(신한카드) product name.")
    for name in CREDIT_CARD_NAMES:
        assert name in description


def test_detail_call_returns_only_the_matched_card() -> None:
    payload = _call("신한카드 SOL트래블 체크")
    widget = payload["widget"]
    children = widget["children"]

    assert widget["type"] == "Card"

    header = children[0]
    assert header["type"] == "Row"
    card_image = header["children"][0]
    assert card_image["type"] == "Image"
    assert card_image["src"] == (
        "https://cdn.www.shinhancard.com/pconts/static/images/card/plate/BUBDGO_E5_v_f_s.webp"
    )
    assert card_image["width"] == 112
    assert card_image["height"] == 72

    card_summary = header["children"][1]
    assert card_summary["type"] == "Col"
    assert card_summary["children"][0]["value"] == "신한카드 SOL트래블 체크"
    assert card_summary["children"][1]["type"] == "Badge"
    assert card_summary["children"][1]["label"] == "연회비 0원"

    assert children[1]["type"] == "Divider"
    assert children[3]["type"] == "Row"
    assert children[3]["children"][1]["value"] == "해외 이용 수수료 · 면제"

    detail_button = children[-1]
    assert detail_button["type"] == "Button"
    assert detail_button["label"] == "자세히 보기"
    assert detail_button["onClickAction"]["payload"]["target"]["url"].startswith("https://")

    copy_text = payload["copy_text"]
    for fragment in ("신한카드 SOL트래블 체크", "연회비", "해외 이용 수수료 · 면제", "자세히 보기"):
        assert fragment in copy_text
    assert "신한 슈퍼SOL 체크" not in copy_text


def test_unknown_card_name_returns_clarification_widget() -> None:
    payload = _call("존재하지 않는 카드")
    assert payload["widget"]["type"] == "Card"
    assert "정확히 말씀해 주세요" in payload["copy_text"]


def test_blank_card_name_returns_clarification_widget() -> None:
    payload = _call("")
    assert payload["widget"]["type"] == "Card"
    assert "정확히 말씀해 주세요" in payload["copy_text"]


def test_unexpected_failure_returns_sanitized_message(monkeypatch) -> None:
    def _boom(*_args, **_kwargs):
        raise RuntimeError("internal details")

    monkeypatch.setattr(deps.guide_service, "find_card_detail", _boom)

    with pytest.raises(RuntimeError) as exc_info:
        _call("신한카드 SOL트래블 체크")
    assert str(exc_info.value) == (
        "### 카드 정보를 불러오지 못했습니다.\n\n잠시 후 다시 시도해 주세요."
    )
