"""기획서의 선택 필터·브랜드 우선·0/1/다건 분기를 EGN00003 연동으로 구현한다."""
from __future__ import annotations
import json
import logging
from typing import Annotated, Any
from mcp.types import ToolAnnotations
from pydantic import Field
from domain.event_brand import BRAND_DESCRIPTION, BRAND_NAMES, BRAND_NAME_SET
from domain.event_type import EVENT_TYPE_CODES, EVENT_TYPE_DESCRIPTION, EVENT_TYPE_NAMES
from kakao.events import event_list
from mci.card_client import CardClient, create_card_client
from mci.event_client import EVENT_ITF_ID, Event, event_request, parse_events, today_kst
from tools.common import json_widget, log_tool_request

logger = logging.getLogger(__name__)
_TOOL_NAME = "getBrandEvents"
_TITLE = "신한카드 이벤트 조회"
_LIMIT = 5
_FALLBACK_NOTICE = "요청 조건에 맞는 진행 중인 이벤트가 없어 전체 최신 이벤트를 안내합니다."
_ERROR_MESSAGE = "### 이벤트 정보를 불러오지 못했습니다.\n\n잠시 후 다시 시도해 주세요."
_DESCRIPTION = (
    "Lists ongoing Shinhan Card(신한카드) events, newest first, up to five. "
    "Use for any event(이벤트) question. Both event_type and brand are optional: "
    "omit both for general, latest, or this-month requests. "
    "A supported brand overrides event_type; never combine them to exclude other categories. "
    "Examples: 여행 이벤트 -> event_type=여행숙박; SOL LINK 체크카드 -> brand=SOL LINK 체크카드; "
    "스타벅스 -> brand=스타벅스; 슈퍼SOL -> brand=슈퍼SOL. "
    "Do not guess unsupported brands or map 학원비 to 청소년; omit unsupported filters. "
    "No matches falls back to general events with a notice. No personal eligibility determination."
)


def _search(client: CardClient, **filters: Any) -> list[Event]:
    data = event_request(**filters)
    result = client.call_with_itf_id(EVENT_ITF_ID, data=data, include_sensitive=True)
    events = parse_events(result, today=today_kst())
    grid = result.get("GRID1") or []
    logger.info("%s 요청=%s 응답=%d건 진행중=%d건", EVENT_ITF_ID,
                json.dumps(data, ensure_ascii=False), len(grid), len(events))
    return events


def find_events(client: CardClient, brand: str | None, event_type: str | None
                ) -> tuple[str, list[Event], str | None]:
    """(라벨, 최대 5건, 안내문구). brand 우선, 0건이면 조건 없이 재조회해 폴백한다."""
    if brand is not None:
        if brand in BRAND_NAME_SET:
            events = _search(client, keyword=brand)
            if events:
                return brand, events[:_LIMIT], None
    elif event_type is not None:
        if event_type in EVENT_TYPE_CODES:
            events = _search(client, category_code=EVENT_TYPE_CODES[event_type])
            if events:
                return event_type, events[:_LIMIT], None
    notice = _FALLBACK_NOTICE if brand is not None or event_type is not None else None
    return "전체 최신", _search(client)[:_LIMIT], notice


def register_event_tools(mcp: Any) -> None:
    client = create_card_client()

    @mcp.tool(name=_TOOL_NAME, tags={"scope:admin", "scope:common", "scope:agca"},
        title=_TITLE, description=_DESCRIPTION, annotations=ToolAnnotations(title=_TITLE,
            readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False))
    def get_brand_events(
        brand: Annotated[str | None, Field(description=BRAND_DESCRIPTION,
            json_schema_extra={"enum": BRAND_NAMES})] = None,
        event_type: Annotated[str | None, Field(description=EVENT_TYPE_DESCRIPTION,
            json_schema_extra={"enum": EVENT_TYPE_NAMES})] = None,
    ) -> str:
        log_tool_request(_TOOL_NAME, {"brand": brand, "event_type": event_type})
        try:
            label, events, notice = find_events(client, brand, event_type)
            return json_widget(event_list(label, events, notice=notice), tool_name=_TOOL_NAME)
        except Exception as exception:
            logger.exception("MCP 툴 처리 실패 - tool=%s", _TOOL_NAME)
            raise RuntimeError(_ERROR_MESSAGE) from exception
