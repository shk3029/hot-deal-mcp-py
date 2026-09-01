import asyncio

from fastapi.testclient import TestClient

from app.domain.credit_card_name import CREDIT_CARD_NAMES
from app.main import app
from app.mcp_server import mcp

_EXPECTED_TOOLS = {
    "getCreditCardRecommendationsWithSelector",
    "getCreditCardDetail",
    "getPopularCreditCards",
    "getFinancialLifeKnowledgeArticles",
}


def _list_tools() -> dict:
    tools = asyncio.run(mcp.list_tools())
    return {tool.name: tool for tool in tools}


def test_all_four_tools_are_registered() -> None:
    tools = _list_tools()
    assert set(tools) == _EXPECTED_TOOLS


def test_server_identity_matches_java() -> None:
    assert mcp.name == "shinhan-credit-card-guide"
    assert mcp._mcp_server.version == "0.0.1"


def test_tool_metadata_follows_playmcp_requirements() -> None:
    tools = _list_tools()
    for tool in tools.values():
        assert tool.description is not None
        assert len(tool.description) <= 1024
        annotations = tool.annotations
        assert annotations is not None
        assert annotations.readOnlyHint is True
        assert annotations.destructiveHint is False
        assert annotations.idempotentHint is True
        assert annotations.openWorldHint is False

    assert "Shinhan Card(신한카드)" in tools["getCreditCardRecommendationsWithSelector"].description
    assert "Shinhan Card(신한카드)" in tools["getCreditCardDetail"].description
    assert "top five" in tools["getPopularCreditCards"].description
    assert "requires no parameters" in tools["getPopularCreditCards"].description
    financial_description = tools["getFinancialLifeKnowledgeArticles"].description
    for fragment in ("consumer trends", "practical money knowledge", "smart card usage"):
        assert fragment in financial_description


def test_card_detail_schema_uses_card_name_enum_as_single_source_of_truth() -> None:
    schema = _list_tools()["getCreditCardDetail"].inputSchema
    assert schema["required"] == ["cardName"]
    card_name = schema["properties"]["cardName"]
    assert card_name["type"] == "string"
    assert card_name["enum"] == CREDIT_CARD_NAMES


def test_popular_tool_takes_no_required_parameters() -> None:
    schema = _list_tools()["getPopularCreditCards"].inputSchema
    assert not schema.get("required")
    assert not schema.get("properties")


def test_schemas_match_spring_ai_style_wrapper() -> None:
    # 설명/이름/enum 은 Java 와 동일. 래퍼도 Spring AI 형태(anyOf-null / pydantic title 없음)로 맞춤.
    for tool in _list_tools().values():
        schema = tool.inputSchema
        assert "title" not in schema
        for name, prop in (schema.get("properties") or {}).items():
            assert "title" not in prop, name
            assert "anyOf" not in prop, name
            assert "default" not in prop, name
            assert prop.get("type") in {"string", "integer"}, name


def test_optional_params_are_not_required_and_keep_their_type() -> None:
    recommendation = _list_tools()["getCreditCardRecommendationsWithSelector"].inputSchema
    assert not recommendation.get("required")
    props = recommendation["properties"]
    assert list(props) == ["industry", "annualFee", "cardType", "sort"]
    assert props["industry"]["type"] == "integer"
    assert props["cardType"]["type"] == "integer"
    assert props["annualFee"]["type"] == "string"
    assert props["sort"]["type"] == "string"

    category = _list_tools()["getFinancialLifeKnowledgeArticles"].inputSchema
    assert not category.get("required")
    assert list(category["properties"]) == ["category"]
    assert category["properties"]["category"]["type"] == "string"


def test_http_app_serves_health_and_mounts_mcp() -> None:
    # mcp 세션 매니저 lifespan 은 프로세스당 1회만 구동 가능하므로 TestClient 도 1회만 연다.
    with TestClient(app) as client:
        health = client.get("/health")
        # streamable HTTP 는 GET 을 허용하지 않으므로(405/406) 마운트 여부만 확인한다.
        mcp_response = client.get("/mcp")

    assert health.status_code == 200
    assert health.json() == {"status": "UP"}
    assert mcp_response.status_code != 404
