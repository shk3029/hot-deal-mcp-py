"""EGN00003 [Kakao] 이벤트 검색데이터 요청·응답 변환.

요청: CHL=sol-hpg, CAG=event, QEE=now_event 고정. brand 는 MSG(키워드 검색),
event_type 은 CAG_CD(홈페이지 분류 숫자코드)로 보낸다.
응답: GRID1 각 행을 ``Event`` 로 바꾸고, 시작일~종료일에 오늘이 포함된 것만 남긴다.
"""
from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)

EVENT_ITF_ID = "EGN00003"
_CHANNEL = "sol-hpg"
_CATEGORY = "event"
_SORT = "now_event"

# GRID1 응답 필드. I/F 정의서 화면에서 영문명 뒤쪽이 잘려 보여 접두어로 찾는다.
# 전체 영문명이 확정되면 FIELD_PREFIXES 값을 전체 이름으로 바꾸면 된다(접두어 = 전체명도 동작).
FIELD_PREFIXES = {
    "id": "MOB_WB_EVT_R",            # 모바일웹이벤트접수번호
    "thumbnail_url": "HPG_EVT_CTG_I",  # 홈페이지이벤트목록이미지
    "detail_url": "HPG_EVT_DL_PG",     # 홈페이지이벤트상세페이지
    "description": "MOB_WB_EVT_T",     # 모바일웹이벤트내용
    "category": "MOB_WB_BNF_C",        # 모바일웹혜택카테고리
    "title": "MOB_WB_EVT_N",           # 모바일웹이벤트명
    "start_date": "MOB_WB_EVT_S",      # 모바일웹이벤트시작일
    "end_date": "MOB_WB_EVT_E",        # 모바일웹이벤트종료일
}


def today_kst() -> date:
    return datetime.now(ZoneInfo("Asia/Seoul")).date()


class Event(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str
    title: str
    description: str
    category: str
    start_date: date
    end_date: date
    thumbnail_url: str
    detail_url: str


def event_request(*, keyword: str = "", category_code: int | None = None) -> dict[str, str]:
    return {
        "CHL": _CHANNEL,
        "CAG": _CATEGORY,
        "MSG": keyword,
        "CAG_CD": "" if category_code is None else str(category_code),
        "QEE": _SORT,
    }


def _field(row: dict[str, Any], prefix: str) -> str:
    value = row.get(prefix)
    if value is None:
        value = next((v for k, v in row.items() if k.startswith(prefix)), None)
    return "" if value is None else str(value).strip()


def _yyyymmdd(value: str) -> date | None:
    digits = value.replace("-", "").replace(".", "")
    if len(digits) != 8 or not digits.isdigit():
        return None
    try:
        return datetime.strptime(digits, "%Y%m%d").date()
    except ValueError:
        return None


def parse_events(result: Any, *, today: date) -> list[Event]:
    """GRID1 을 MCI 순서(now_event) 그대로 변환하고 진행 기간 밖이거나 날짜가 깨진 행은 뺀다."""
    if not isinstance(result, dict) or not isinstance(result.get("GRID1", []), list):
        raise TypeError("MCI 이벤트 응답 형식이 올바르지 않습니다.")
    events: list[Event] = []
    for row in result.get("GRID1", []):
        if not isinstance(row, dict):
            continue
        values = {name: _field(row, prefix) for name, prefix in FIELD_PREFIXES.items()}
        start, end = _yyyymmdd(values["start_date"]), _yyyymmdd(values["end_date"])
        if start is None or end is None or not values["title"]:
            logger.warning("이벤트 행 제외(필수값/날짜 오류) - id=%s", values["id"])
            continue
        if not start <= today <= end:
            continue
        events.append(Event(**{**values, "start_date": start, "end_date": end}))
    return events
