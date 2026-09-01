"""Java(Spring AI) 실서버 `tools/list` 응답과 완전 동일한지 회귀 검증.

`fixtures/java_tools_list.json` 은 Java `hot-deal-mcp` 서버(fresh `bootJar`)의
`tools/list` 결과에서 name / description / inputSchema / annotations / title 만 추린 것.
"""

import asyncio
import json
from pathlib import Path

import pytest

from app.mcp_server import mcp

_FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "java_tools_list.json").read_text("utf-8")
)

# Spring AI 전용 필드(MCP 스펙 아님). mcp.types.ToolAnnotations 에 없어 재현하지 않는다.
_SPRING_ONLY_ANNOTATION_KEYS = {"returnDirect"}


def _python_tools() -> dict:
    return {t.name: t for t in asyncio.run(mcp.list_tools())}


@pytest.fixture(scope="module")
def python_tools() -> dict:
    return _python_tools()


@pytest.mark.parametrize("tool_name", list(_FIXTURE))
def test_description_is_byte_identical(tool_name: str, python_tools: dict) -> None:
    assert python_tools[tool_name].description == _FIXTURE[tool_name]["description"]


@pytest.mark.parametrize("tool_name", list(_FIXTURE))
def test_input_schema_is_byte_identical(tool_name: str, python_tools: dict) -> None:
    expected = json.dumps(_FIXTURE[tool_name]["inputSchema"], ensure_ascii=False)
    actual = json.dumps(python_tools[tool_name].inputSchema, ensure_ascii=False)
    assert actual == expected


@pytest.mark.parametrize("tool_name", list(_FIXTURE))
def test_annotations_match(tool_name: str, python_tools: dict) -> None:
    expected = {
        k: v
        for k, v in (_FIXTURE[tool_name]["annotations"] or {}).items()
        if k not in _SPRING_ONLY_ANNOTATION_KEYS
    }
    tool = python_tools[tool_name]
    actual = tool.annotations.model_dump(exclude_none=True) if tool.annotations else {}
    assert actual == expected


@pytest.mark.parametrize("tool_name", list(_FIXTURE))
def test_top_level_title_matches(tool_name: str, python_tools: dict) -> None:
    assert python_tools[tool_name].title == _FIXTURE[tool_name]["title"]
