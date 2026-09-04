"""툴 모듈 공통 헬퍼."""

from __future__ import annotations

import json
import logging
from typing import Any

from mcp.types import CallToolResult, TextContent
from schemas.card_finder_tools_schemas import CardDetail, PlayMcpWidgetResponse

audit_logger = logging.getLogger("mcp.tool.audit")


def log_tool_request(tool_name: str, arguments: dict[str, Any]) -> None:
    """인증 헤더 등 전송 계층 정보는 제외하고 툴 입력값만 기록한다."""

    audit_logger.info(
        "MCP tool request - tool=%s, arguments=%s",
        tool_name,
        json.dumps(arguments, ensure_ascii=False, separators=(",", ":")),
    )


def json_widget(payload: dict[str, Any], *, tool_name: str) -> CallToolResult:
    """위젯 JSON을 structuredContent 없이 MCP text content로 반환한다."""

    validated = PlayMcpWidgetResponse.model_validate(payload)
    response_json = json.dumps(
        validated.model_dump(),
        ensure_ascii=False,
        separators=(",", ":"),
    )
    audit_logger.info(
        "MCP tool response - tool=%s, response=%s",
        tool_name,
        response_json,
    )
    return CallToolResult(
        content=[
            TextContent(
                type="text",
                text=response_json,
            )
        ],
        isError=False,
    )


def card_detail_from_mci(item: dict[str, Any]) -> CardDetail:
    """EGN00001 GRID1 한 건을 위젯용 카드 모델로 변환한다."""

    def text_value(key: str) -> str:
        value = item.get(key)
        return "" if value is None else str(value).strip()

    def int_value(key: str) -> int:
        try:
            return int(item.get(key) or 0)
        except (TypeError, ValueError):
            return 0

    return CardDetail(
        CRD_PD_PGE_N=text_value("CRD_PD_PGE_N"),
        CRD_PD_NM=text_value("CRD_PD_NM"),
        CRD_PD_DESC=text_value("CRD_PD_DESC"),
        CRD_PD_URL=text_value("CRD_PD_URL"),
        CRD_PD_IMG_URL=text_value("CRD_PD_IMG_URL"),
        CRD_PD_AFE=int_value("CRD_PD_AFE"),
        CRD_PD_BNF_CD=text_value("CRD_PD_BNF_CD"),
        TAG_BST_VL=text_value("TAG_BST_VL"),
        TAG_LAT_VL=text_value("TAG_LAT_VL"),
        TAG_CSB_VL=text_value("TAG_CSB_VL"),
        CRD_PD_BNF_NM1=text_value("CRD_PD_BNF_NM1"),
        CRD_PD_BNF_NM2=text_value("CRD_PD_BNF_NM2"),
        CRD_PD_BNF_NM3=text_value("CRD_PD_BNF_NM3"),
        CRD_PD_BNF_DL1=text_value("CRD_PD_BNF_DL1"),
        CRD_PD_BNF_DL2=text_value("CRD_PD_BNF_DL2"),
        CRD_PD_BNF_DL3=text_value("CRD_PD_BNF_DL3"),
    )
