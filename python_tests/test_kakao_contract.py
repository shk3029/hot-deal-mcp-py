import asyncio
import json
import logging
import os
import sys
from types import SimpleNamespace

import pytest

from domain.annual_fee_band import AnnualFeeBand
from domain.card_sort_order import CardSortOrder
from domain.credit_card_name import CREDIT_CARD_NAMES
from mci.card_client import create_card_client
from mci.mock_client import MockMciClient

# 회귀 테스트는 내부 MCI 설정과 네트워크에 의존하지 않도록 목업을 명시한다.
os.environ.setdefault("CARD_DATA_SOURCE", "mock")

from main import _headers_for_log
from server import mcp
from tools.finance_tips.constants import CATEGORY_MAP


EXPECTED_NAMES = {
    "getCreditCardRecommendationsWithSelector",
    "getCreditCardDetail",
    "getPopularCreditCards",
    "getFinancialLifeKnowledgeArticles",
}


def listed_tools():
    return {tool.name: tool for tool in asyncio.run(mcp.list_tools())}


def call(name: str, *args):
    result = mcp._tool_manager.get_tool(name).fn(*args)
    assert isinstance(result, str)
    payload = json.loads(result)
    assert set(payload) == {"widget", "copy_text"}
    return payload


def test_feature_test_tool_names_and_codes_are_exposed():
    tools = listed_tools()
    assert set(tools) == EXPECTED_NAMES
    assert all(tool.outputSchema is None for tool in tools.values())
    assert tools["getCreditCardRecommendationsWithSelector"].meta["tool_code"] == "TL-COMM-004"
    assert tools["getCreditCardDetail"].meta["tool_code"] == "TL-COMM-005"
    assert tools["getPopularCreditCards"].meta["tool_code"] == "TL-COMM-006"
    assert tools["getFinancialLifeKnowledgeArticles"].meta["tool_code"] == "TL-COMM-007"


def test_feature_test_input_schemas_are_preserved():
    tools = listed_tools()
    recommendation = tools["getCreditCardRecommendationsWithSelector"].inputSchema
    assert list(recommendation["properties"]) == ["industry", "annualFee", "cardType", "sort"]
    assert recommendation["required"] == []
    assert recommendation["properties"]["industry"]["format"] == "int32"

    detail = tools["getCreditCardDetail"].inputSchema
    assert detail["required"] == ["cardName"]
    assert detail["additionalProperties"] is False
    assert detail["properties"]["cardName"]["enum"] == CREDIT_CARD_NAMES

    popular = tools["getPopularCreditCards"].inputSchema
    assert popular == {"type": "object", "properties": {}, "required": []}

    finance = tools["getFinancialLifeKnowledgeArticles"].inputSchema
    assert list(finance["properties"]) == ["category"]
    assert finance["required"] == []


def test_descriptions_match_latest_feature_test_intent():
    tools = listed_tools()
    assert "cardType to 2" in tools["getCreditCardRecommendationsWithSelector"].description
    assert "cardName value" in tools["getCreditCardDetail"].description
    assert "requires no parameters" in tools["getPopularCreditCards"].description
    assert "Shinhan Card(신한카드)" in tools["getFinancialLifeKnowledgeArticles"].description


def test_all_tools_return_only_kakao_widget_contract():
    assert call("getCreditCardRecommendationsWithSelector", None, None, None, None)["widget"]["type"] == "Card"
    assert call("getCreditCardRecommendationsWithSelector", 5, "제한없음", 2, "연회비순")["widget"]["type"] == "Card"
    assert call("getCreditCardDetail", "신한카드 Mr.Life")["widget"]["type"] == "Card"
    assert call("getPopularCreditCards")["widget"]["type"] == "Card"
    assert call("getFinancialLifeKnowledgeArticles", "카드연구소")["widget"]["type"] == "ListView"


def test_fastmcp_conversion_returns_only_text_content_without_structured_output():
    cases = {
        "getCreditCardRecommendationsWithSelector": {
            "industry": 2,
            "annualFee": "0~1만원대",
            "cardType": 1,
            "sort": "출시일순",
        },
        "getCreditCardDetail": {"cardName": "신한카드 Mr.Life"},
        "getPopularCreditCards": {},
        "getFinancialLifeKnowledgeArticles": {"category": "금융"},
    }

    for name, arguments in cases.items():
        tool = mcp._tool_manager.get_tool(name)
        converted = asyncio.run(tool.run(arguments, convert_result=True))

        assert isinstance(converted, list)
        assert len(converted) == 1
        assert converted[0].type == "text"
        assert set(json.loads(converted[0].text)) == {"widget", "copy_text"}


def test_empty_card_result_shows_guidance_and_more_cards_button():
    message = (
        "원하는 카드를 찾지 못하셨나요? '더 많은 카드 보기'를 눌러 "
        "신한카드에서 직접 찾아보세요"
    )
    widget_message = (
        "원하는 카드를 찾지 못하셨나요?\n"
        "'더 많은 카드 보기'를 눌러 신한카드에서 직접 찾아보세요"
    )
    payload = call(
        "getCreditCardRecommendationsWithSelector",
        15,
        "0~1만원대",
        1,
        "연회비순",
    )

    card_list, more_cards_button = payload["widget"]["children"]
    assert card_list["children"][0]["value"] == widget_message
    assert more_cards_button["label"] == "더 많은 카드 보기"
    assert more_cards_button["onClickAction"]["payload"]["target"]["url"]
    assert message in payload["copy_text"]
    assert "[더 많은 카드 보기]" in payload["copy_text"]


def test_popular_card_rows_open_the_same_card_detail_prompt_as_search_results():
    payload = call("getPopularCreditCards")
    rows = payload["widget"]["children"][2]["children"]

    assert rows
    for row in rows:
        card_name = row["key"]
        detail_button = row["children"][-1]
        assert detail_button["type"] == "Button"
        assert detail_button["label"] == ">"
        assert detail_button["onClickAction"] == {
            "payload": {
                "target": {
                    "type": "sendUserMessage",
                    "properties": {"text": f"{card_name} 혜택 알려줘"},
                }
            }
        }


def test_restored_domain_normalization():
    assert AnnualFeeBand.from_string(None) is AnnualFeeBand.NO_LIMIT
    assert AnnualFeeBand.from_string("3만원대") is AnnualFeeBand.THIRTY_THOUSAND_RANGE
    assert CardSortOrder.from_string(None) is CardSortOrder.RELEASE_DATE
    assert len(CREDIT_CARD_NAMES) == 81


def test_shinhan_card_blog_urls_use_working_www_host():
    for contents in CATEGORY_MAP.values():
        for item in contents:
            if "shinhancardblog.com" in item.value.url:
                assert item.value.url.startswith("https://www.shinhancardblog.com/")


def test_tool_request_and_response_are_logged(caplog):
    with caplog.at_level(logging.INFO, logger="mcp.tool.audit"):
        call("getFinancialLifeKnowledgeArticles", "금융")

    messages = [record.getMessage() for record in caplog.records]
    assert any(
        'MCP tool request - tool=getFinancialLifeKnowledgeArticles, arguments={"category":"금융"}'
        == message
        for message in messages
    )
    assert any(
        message.startswith(
            "MCP tool response - tool=getFinancialLifeKnowledgeArticles, response="
        )
        and '"widget"' in message
        and '"copy_text"' in message
        for message in messages
    )


def test_card_data_source_uses_mock_only_when_explicit(monkeypatch):
    monkeypatch.setenv("CARD_DATA_SOURCE", "mock")

    assert isinstance(create_card_client(), MockMciClient)


def test_card_data_source_defaults_to_real_mci(monkeypatch):
    class FakeMciClient:
        pass

    monkeypatch.delenv("CARD_DATA_SOURCE", raising=False)
    monkeypatch.setitem(
        sys.modules,
        "mci.mci_client",
        SimpleNamespace(MciClient=FakeMciClient),
    )

    assert isinstance(create_card_client(), FakeMciClient)


def test_card_data_source_selects_real_mci_lazily(monkeypatch):
    class FakeMciClient:
        pass

    monkeypatch.setenv("CARD_DATA_SOURCE", "mci")
    monkeypatch.setitem(
        sys.modules,
        "mci.mci_client",
        SimpleNamespace(MciClient=FakeMciClient),
    )

    assert isinstance(create_card_client(), FakeMciClient)


def test_card_data_source_rejects_unknown_value(monkeypatch):
    monkeypatch.setenv("CARD_DATA_SOURCE", "unknown")

    with pytest.raises(RuntimeError, match="CARD_DATA_SOURCE"):
        create_card_client()


def test_http_header_logging_redacts_credentials():
    headers = _headers_for_log(
        {
            "content-type": "application/json",
            "accept": "application/json, text/event-stream",
            "authorization": "Bearer secret-value",
            "cookie": "session=secret-value",
            "x-api-key": "secret-value",
            "x-kakao-signature": "secret-value",
        }
    )

    assert headers["content-type"] == "application/json"
    assert headers["accept"] == "application/json, text/event-stream"
    assert headers["authorization"] == "<redacted>"
    assert headers["cookie"] == "<redacted>"
    assert headers["x-api-key"] == "<redacted>"
    assert headers["x-kakao-signature"] == "<redacted>"
