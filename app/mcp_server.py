"""PlayMCP 호환 MCP 서버.

Java(Spring AI) ``hot-deal-mcp`` 의 Tool 들을 공식 ``mcp`` SDK 의 FastMCP 로 포팅한다.
툴 정의는 ``app/tools/`` 아래 모듈에 있고, ``app/tools/__init__.py`` 의 ``REGISTER_TOOLS``
에 있는 것만 등록된다. Tool 응답은 모두 ``{"widget", "copy_text"}`` JSON 문자열이다.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from app.tools import register_tools

mcp = FastMCP(
    name="shinhan-credit-card-guide",
    instructions="신한카드 상품 추천과 카드 상세 정보를 PlayMCP 위젯 형식으로 제공합니다.",
    stateless_http=True,
    json_response=True,
    streamable_http_path="/mcp",
    host=os.getenv("HOST", "0.0.0.0"),
    port=int(os.getenv("PORT", "8080")),
)
# FastMCP 생성자에는 version 인자가 없어 initialize 응답의 serverInfo.version 을 직접 맞춘다.
mcp._mcp_server.version = "0.0.1"

register_tools(mcp)


def _match_spring_ai_schema(schema: dict[str, Any]) -> None:
    """Pydantic 이 만든 inputSchema 를 Java(Spring AI `JsonSchemaGenerator` /
    수동 `McpSchema.JsonSchema`) 가 내보내는 JSON 과 **바이트 단위로 동일**하게 재작성한다.

    Java 출력 규칙(실서버 `tools/list` 로 확인):
    - 루트 키 순서: ``type`` → ``properties`` → ``required`` → (상세 툴만) ``additionalProperties``
    - ``required`` 는 비어 있어도 항상 ``[]`` 로 존재
    - 프로퍼티 키 순서: ``type`` → (정수면) ``format: "int32"`` → ``description`` → (있으면) ``enum``
    - ``Optional[T]`` 은 ``anyOf``/``null``/``default`` 없이 ``{"type": T, ...}`` 로 노출하고
      단지 ``required`` 에서 뺀다
    - Pydantic 이 붙이는 ``title`` 은 모두 제거
    - ``additionalProperties: false`` 는 수동 스키마를 쓴 ``getCreditCardDetail`` 에만
    """
    source_props: dict[str, Any] = schema.get("properties") or {}
    rebuilt_props: dict[str, Any] = {}
    for name, prop in source_props.items():
        any_of = prop.get("anyOf")
        base_type = prop.get("type")
        if isinstance(any_of, list):
            base_type = next(
                (entry.get("type") for entry in any_of if entry.get("type") != "null"),
                base_type,
            )

        rebuilt: dict[str, Any] = {"type": base_type}
        if base_type == "integer":
            rebuilt["format"] = "int32"
        rebuilt["description"] = prop.get("description", "")
        if "enum" in prop:
            rebuilt["enum"] = prop["enum"]
        rebuilt_props[name] = rebuilt

    rebuilt_schema: dict[str, Any] = {
        "type": "object",
        "properties": rebuilt_props,
        "required": list(schema.get("required") or []),
    }
    if "cardName" in rebuilt_props:
        rebuilt_schema["additionalProperties"] = False

    schema.clear()
    schema.update(rebuilt_schema)


for _registered_tool in mcp._tool_manager.list_tools():
    _match_spring_ai_schema(_registered_tool.parameters)


def main() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
