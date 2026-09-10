"""카카오툴즈 호환 MCP 서버.

툴 정의는 ``tools/`` 아래 모듈에 있고, ``tools/__init__.py`` 의 ``REGISTER_TOOLS``
에 있는 것만 등록된다. 각 툴은 결과 모델 최상위에 ``widget`` / ``copy_text`` (카카오툴즈
응답) 를 실어 돌려준다.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from fastmcp import FastMCP
from fastmcp.tools import Tool

from tools import register_tools

mcp = FastMCP(
    name="shinhan-credit-card-guide",
    instructions="신한카드 상품 추천과 카드 상세 정보를 카카오툴즈 위젯 형식으로 제공합니다.",
    version="0.0.1",
)


def _match_spring_ai_schema(schema: dict[str, Any]) -> None:
    """Pydantic 입력 스키마를 feature/test의 Spring MCP 형태로 정규화한다."""

    source_properties: dict[str, Any] = schema.get("properties") or {}
    properties: dict[str, Any] = {}
    for name, source in source_properties.items():
        base_type = source.get("type")
        if isinstance(source.get("anyOf"), list):
            base_type = next(
                (
                    entry.get("type")
                    for entry in source["anyOf"]
                    if entry.get("type") != "null"
                ),
                base_type,
            )
        prop: dict[str, Any] = {"type": base_type}
        if base_type == "integer":
            prop["format"] = "int32"
        prop["description"] = source.get("description", "")
        if "enum" in source:
            prop["enum"] = source["enum"]
        properties[name] = prop

    normalized: dict[str, Any] = {
        "type": "object",
        "properties": properties,
        "required": list(schema.get("required") or []),
    }
    if "cardName" in properties:
        normalized["additionalProperties"] = False
    schema.clear()
    schema.update(normalized)


# 등록 시 기존 Spring AI 입력 스키마 계약을 유지한다.
def _tool(**kwargs):

    def register(fn):
        tool = Tool.from_function(fn, **kwargs)
        _match_spring_ai_schema(tool.parameters)
        mcp.add_tool(tool)
        return fn

    return register


mcp.tool = _tool
register_tools(mcp)


def main() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    mcp.run(
        transport="http",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8080")),
        path="/mcp",
        stateless_http=True,
        json_response=True,
    )


if __name__ == "__main__":
    main()
