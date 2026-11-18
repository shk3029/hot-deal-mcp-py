"""EGN00003 목업 응답. 실제 행사 데이터가 아니라 기획서 시나리오 검증용이다.

응답 필드 영문명은 I/F 정의서에서 잘려 보이는 부분을 임의로 채운 가칭이다.
파서는 접두어로 찾으므로 가칭이어도 동작한다.
"""
from __future__ import annotations

import os
from datetime import timedelta
from typing import Any
from urllib.parse import quote

from domain.event_type import EVENT_TYPE_CODES
from mci.event_client import today_kst

_CODE_TO_TYPE = {str(code): name for name, code in EVENT_TYPE_CODES.items()}
_SUMMARIES = {"쇼핑문화": "결제 시 최대 10% 캐시백",
              "카드결제": "이벤트 기간 결제 시 포인트 적립",
              "여행숙박": "예약 시 최대 15% 할인",
              "앱테크": "앱 참여하고 포인트 받기",
              "청소년": "자동납부 등록 시 혜택 제공"}


def mock_events_url(event_id: str | None = None) -> str:
    base = os.getenv("EVENT_MOCK_BASE_URL", "http://127.0.0.1:8765").rstrip("/")
    return base + "/mock-events" + ("/" + quote(event_id, safe="") if event_id else "")


def _specs() -> list[tuple[str, str, str]]:
    specs = [("sol-link", "SOL LINK 체크카드", "쇼핑문화"),
             ("starbucks-shopping", "스타벅스", "쇼핑문화"),
             ("starbucks-payment", "스타벅스", "카드결제")]
    specs += [(f"super-sol-{i}", "슈퍼SOL", "카드결제") for i in range(6)]
    specs += [(f"travel-{i}", b, "여행숙박") for i, b in enumerate(
        ["아고다", "트립닷컴", "시그니엘", "하얏트", "제주", "JCB"])]
    specs += [("discover", "디스커버", "앱테크"), ("school", "교원", "청소년")]
    return specs


def mock_event_rows() -> list[dict[str, Any]]:
    """now_event 순서(최신 먼저)의 GRID1 행. 기간 필터 검증용으로 종료·예정 행도 섞는다."""
    today = today_kst()
    rows = []
    for index, (key, brand, category) in enumerate(_specs()):
        rows.append(_row(key, brand, category, today - timedelta(days=30 - index),
                         today + timedelta(days=7)))
    rows.insert(1, _row("ended", "스타벅스", "쇼핑문화", today - timedelta(days=60),
                        today - timedelta(days=1)))
    rows.insert(2, _row("upcoming", "슈퍼SOL", "카드결제", today + timedelta(days=1),
                        today + timedelta(days=30)))
    return rows


def _row(key: str, brand: str, category: str, start, end) -> dict[str, Any]:
    return {
        "MOB_WB_EVT_RCN": key,
        "HPG_EVT_CTG_IMG_URL": mock_events_url(key) + "/thumbnail.svg",
        "HPG_EVT_DL_PGE_URL": mock_events_url(key),
        "MOB_WB_EVT_TXT": f"[목업] {brand} {_SUMMARIES[category]}",
        "MOB_WB_BNF_CTG": category,
        "MOB_WB_EVT_NM": f"[목업] {brand} {category} 이벤트",
        "MOB_WB_EVT_STD": start.strftime("%Y%m%d"),
        "MOB_WB_EVT_EDD": end.strftime("%Y%m%d"),
        "DIS_F": "Y",
        "_brand": brand,
    }


def search_events(data: dict[str, Any]) -> dict[str, Any]:
    """MSG 키워드(브랜드명 포함 검색) → CAG_CD 분류 → 전체 순으로 흉내낸다."""
    rows = mock_event_rows()
    keyword = str(data.get("MSG") or "").strip()
    category = _CODE_TO_TYPE.get(str(data.get("CAG_CD") or "").strip())
    if keyword:
        rows = [r for r in rows if keyword in r["_brand"] or keyword in r["MOB_WB_EVT_NM"]]
    elif str(data.get("CAG_CD") or "").strip():
        rows = [r for r in rows if r["MOB_WB_BNF_CTG"] == category]
    grid = [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows[:100]]
    return {"TO_CT": len(rows), "GRID1_CT": len(grid), "GRID1": grid}
