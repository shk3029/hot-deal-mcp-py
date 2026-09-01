import json

import pytest

from app import deps
from app.mcp_server import mcp

get_financial_life_knowledge_articles = mcp._tool_manager.get_tool(
    "getFinancialLifeKnowledgeArticles"
).fn


def _call(category=None) -> dict:
    return json.loads(get_financial_life_knowledge_articles(category))


def _assert_article(row: dict, title: str, url: str) -> None:
    title_text = row["children"][1]["children"][0]
    assert row["type"] == "ListViewItem"
    assert title_text["value"] == title
    assert title_text["textAlign"] == "start"
    assert title_text["maxLines"] == 3
    assert row["onClickAction"]["payload"]["target"]["url"] == url


def test_trend_intent_returns_five_clickable_trend_articles() -> None:
    payload = _call("트렌드")
    widget = payload["widget"]
    children = widget["children"]

    assert widget["type"] == "ListView"
    assert len(children) == 7
    assert children[0]["children"][0]["children"][0]["value"] == "TREND"
    _assert_article(
        children[1],
        "데이터로 살펴본 2026 여행 트렌드",
        "https://www.shinhancardblog.com/1432",
    )
    assert (
        children[6]["children"][0]["onClickAction"]["payload"]["target"]["properties"][
            "text"
        ]
        == "금융 금융생활지식 보여줘"
    )


def test_finance_intent_returns_three_finance_articles() -> None:
    payload = _call("금융")
    children = payload["widget"]["children"]

    assert children[0]["children"][0]["children"][0]["value"] == "FINANCE"
    assert len(children) == 5
    _assert_article(
        children[3],
        "새로워진 신한 슈퍼 SOL! 가입하고 런칭 이벤트 혜택 받는 방법",
        "https://www.shinhancardblog.com/1434",
    )


def test_card_tips_intent_returns_five_card_lab_articles() -> None:
    payload = _call("카드 연구소")
    children = payload["widget"]["children"]

    assert children[0]["children"][0]["children"][0]["value"] == "CARD LAB"
    assert len(children) == 7
    _assert_article(
        children[5],
        "[쏠깃한 카드 연구소] 사장님 지갑 쏠쏠해지는 Npay biz 신한카드",
        "https://www.shinhancardblog.com/1407",
    )


def test_default_category_is_trend() -> None:
    payload = _call(None)
    assert payload["widget"]["children"][0]["children"][0]["children"][0]["value"] == "TREND"
    assert "### 금융생활지식 · 트렌드" in payload["copy_text"]


def test_unexpected_failure_returns_sanitized_message(monkeypatch) -> None:
    def _boom(*_args, **_kwargs):
        raise RuntimeError("internal details")

    monkeypatch.setattr(deps.financial_service, "find_articles", _boom)

    with pytest.raises(RuntimeError) as exc_info:
        _call("트렌드")
    assert str(exc_info.value) == (
        "### 금융생활지식을 불러오지 못했습니다.\n\n잠시 후 다시 시도해 주세요."
    )
