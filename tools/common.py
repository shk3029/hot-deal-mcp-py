"""툴 모듈 공통 헬퍼."""
from __future__ import annotations

import json
import logging
from typing import Any

from schemas.card_finder_tools_schemas import CardDetail, PlayMcpWidgetResponse

audit_logger = logging.getLogger("mcp.tool.audit")


def log_tool_request(tool_name: str, arguments: dict[str, Any]) -> None:
    """인증 헤더 등 전송 계층 정보는 제외하고 툴 입력값만 기록한다."""

    audit_logger.info(
        "MCP tool request - tool=%s, arguments=%s",
        tool_name,
        json.dumps(arguments, ensure_ascii=False, separators=(",", ":")),
    )


def json_widget(payload: dict[str, Any], *, tool_name: str) -> str:
    """FastMCP가 단일 TextContent로 변환할 위젯 JSON 문자열을 반환한다."""

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
    return response_json


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


# Uvicorn의 기본 설정은 앱 INFO 로그를 출력하지 않으므로 전용 콘솔 로그를 둔다.
source_logger = logging.getLogger("mcp.tool.data_source")
if not source_logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    source_logger.addHandler(handler)
source_logger.setLevel(logging.INFO)
source_logger.propagate = False


def call_card_interface(client: Any, itf_id: str, *, tool_name: str,
                        data: dict[str, Any], include_sensitive: bool = False) -> dict[str, Any]:
    resolver = getattr(client, "data_source_for", None)
    source = resolver(itf_id, data) if resolver else {
        "MockMciClient": "mock", "MockCardClient": "mock",
        "EsCardClient": "es", "MciClient": "mci",
    }.get(type(client).__name__, type(client).__name__)
    try:
        result = client.call_with_itf_id(itf_id, data=data, include_sensitive=include_sensitive)
    except Exception:
        source_logger.info("tool=%s source=%s interface=%s status=error", tool_name, source, itf_id)
        raise
    source_logger.info("tool=%s source=%s interface=%s status=success", tool_name, source, itf_id)
    return result
