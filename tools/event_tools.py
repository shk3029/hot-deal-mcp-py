"""기획서의 선택 필터·브랜드 우선·0/1/다건 분기를 구현한다."""
from __future__ import annotations
import logging
from typing import Annotated, Any
from mcp.types import ToolAnnotations
from pydantic import Field
from domain.event_brand import BRAND_DESCRIPTION, BRAND_NAMES, BRAND_NAME_SET
from domain.event_type import EVENT_TYPE_DESCRIPTION, EVENT_TYPE_NAMES
from kakao.events import event_list
from mci.event_client import create_event_client, today_kst
from tools.common import json_widget, log_tool_request

logger = logging.getLogger(__name__)
_TOOL_NAME = "getBrandEvents"
_DESCRIPTION = (
    "Lists ongoing Shinhan Card(신한카드) events, newest first, up to five. "
    "Use for any event(이벤트) question. Both event_type and brand are optional: "
    "omit both for general, latest, or this-month requests. "
    "A supported brand overrides event_type; never combine them to exclude other categories. "
    "Examples: 여행 이벤트 -> event_type=여행숙박; SOL LINK 체크카드 -> brand=SOL LINK 체크카드; "
    "스타벅스 -> brand=스타벅스; 슈퍼SOL -> brand=슈퍼SOL. "
    "Do not guess unsupported brands or map 학원비 to 청소년; omit unsupported filters. "
    "No matches falls back to general events with a notice. No personal eligibility determination. "
    "Development only: returned events and detail pages are mock data, not real benefits."
)


def register_event_tools(mcp: Any) -> None:
    @mcp.tool(name=_TOOL_NAME, tags={"scope:admin", "scope:common", "scope:agca"},
        description=_DESCRIPTION, annotations=ToolAnnotations(title="신한카드 이벤트 조회 (목업)",
            readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False))
    def get_brand_events(
        brand: Annotated[str | None, Field(description=BRAND_DESCRIPTION,
            json_schema_extra={"enum": BRAND_NAMES})] = None,
        event_type: Annotated[str | None, Field(description=EVENT_TYPE_DESCRIPTION,
            json_schema_extra={"enum": EVENT_TYPE_NAMES})] = None,
    ) -> str:
        log_tool_request(_TOOL_NAME, {"brand": brand, "event_type": event_type})
        try:
            today = today_kst()
            current = sorted(
                [event for event in create_event_client().list_events()
                 if event.start_date <= today <= event.end_date],
                key=lambda event: (event.published_date, event.id), reverse=True)
            notice = None
            label = "전체 최신"
            if brand is not None:
                matching = [e for e in current if e.brand == brand] if brand in BRAND_NAME_SET else []
                label = brand if brand in BRAND_NAME_SET else "브랜드 검색"
            elif event_type is not None:
                matching = [e for e in current if e.event_type == event_type] if event_type in EVENT_TYPE_NAMES else []
                label = event_type if event_type in EVENT_TYPE_NAMES else "분류 검색"
            else:
                matching = current
            if not matching and (brand is not None or event_type is not None):
                matching = current
                notice = "요청 조건에 맞는 진행 중인 이벤트가 없어 전체 최신 이벤트를 안내합니다."
                label = "전체 최신"
            return json_widget(event_list(label, matching[:5], notice=notice), tool_name=_TOOL_NAME)
        except Exception as exception:
            logger.exception("이벤트 조회 실패")
            raise RuntimeError("이벤트 정보를 불러올 수 없습니다. 개발 환경에서 EVENT_DATA_SOURCE=mock을 확인하세요.") from exception
