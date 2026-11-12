"""기획 검증용 이벤트 목업. 실제 API 규격이나 실제 행사 데이터가 아니다."""
from __future__ import annotations
import os
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from pydantic import BaseModel, ConfigDict


def today_kst() -> date:
    return datetime.now(ZoneInfo("Asia/Seoul")).date()


class Event(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str
    brand: str
    event_type: str
    title: str
    description: str
    published_date: date
    start_date: date
    end_date: date
    # 실제 연동 시 이벤트 썸네일 URL. 없으면 위젯이 프리뷰 목업 썸네일을 사용한다.
    thumbnail_url: str | None = None


class MockEventClient:
    def list_events(self) -> list[Event]:
        today = today_kst()
        # 홈페이지 운영 분류를 추측하지 않고 기획 예시를 명시적으로 매핑한다.
        specs = [("sol-link", "SOL LINK 체크카드", "쇼핑문화"),
                 ("starbucks-shopping", "스타벅스", "쇼핑문화"),
                 ("starbucks-payment", "스타벅스", "카드결제")]
        specs += [(f"super-sol-{i}", "슈퍼SOL", "카드결제") for i in range(6)]
        specs += [(f"travel-{i}", b, "여행숙박") for i, b in enumerate(
            ["아고다", "트립닷컴", "시그니엘", "하얏트", "제주", "JCB"])]
        specs += [("discover", "디스커버", "앱테크"), ("school", "교원", "청소년")]
        # 목록 텍스트1(요약)로 쓰이는 분류별 가상 문구. 실제 혜택 조건이 아니다.
        summaries = {"쇼핑문화": "결제 시 최대 10% 캐시백 (목업)",
                     "카드결제": "이벤트 기간 결제 시 포인트 적립 (목업)",
                     "여행숙박": "예약 시 최대 15% 할인 (목업)",
                     "앱테크": "앱 참여하고 포인트 받기 (목업)",
                     "청소년": "자동납부 등록 시 혜택 제공 (목업)"}
        events = []
        for index, (key, brand, category) in enumerate(specs):
            events.append(Event(id=key, brand=brand, event_type=category,
                title=f"[목업] {brand} {category} 이벤트 {index + 1}",
                description=f"{brand} {summaries[category]}",
                published_date=today-timedelta(days=index),
                start_date=today-timedelta(days=30), end_date=today+timedelta(days=7)))
        return events


def create_event_client() -> MockEventClient:
    source = os.getenv("EVENT_DATA_SOURCE", "unconfigured").strip().lower()
    if source == "mock":
        return MockEventClient()
    raise RuntimeError("이벤트 API 미연동: 로컬 검증은 EVENT_DATA_SOURCE=mock을 지정하세요.")
