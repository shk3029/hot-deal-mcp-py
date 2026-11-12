"""1건은 카드형, 2~5건은 목록형. 링크는 로컬 목업 랜딩으로 연결한다.

각 행은 왼쪽 썸네일, 오른쪽 요약(텍스트1)·제목(텍스트2), 맨 오른쪽 상세 이동(>) 버튼으로
구성하고, 목록 맨 마지막에 "더 많은 이벤트 보기" 버튼을 둔다.
"""
import os
from urllib.parse import quote
from kakao.common import Widget, response, open_url_action
from mci.event_client import Event


def mock_events_url(event_id: str | None = None) -> str:
    base = os.getenv("EVENT_MOCK_BASE_URL", "http://127.0.0.1:8765").rstrip("/")
    return base + "/mock-events" + ("/" + quote(event_id, safe="") if event_id else "")


def mock_thumbnail_url(event_id: str) -> str:
    return mock_events_url(event_id) + "/thumbnail.svg"


def _event_row_children(event: Event) -> list[Widget]:
    detail_url = mock_events_url(event.id)
    thumbnail = {"type": "Image", "src": event.thumbnail_url or mock_thumbnail_url(event.id),
                 "alt": f"{event.title} 썸네일", "width": 72, "height": 72,
                 "fit": "cover", "radius": "sm"}
    texts = {"type": "Col", "gap": 1, "flex": "auto", "children": [
        {"type": "Text", "value": event.description, "size": "sm",
         "weight": "semibold", "maxLines": 2},
        {"type": "Caption", "value": event.title, "maxLines": 1}]}
    detail = {"type": "Button", "label": "", "iconEnd": "chevron-right", "iconSize": "xl",
              "variant": "ghost", "uniform": True, "onClickAction": open_url_action(detail_url)}
    return [thumbnail, texts, detail]


def event_list(label: str, events: list[Event], *, notice: str | None = None):
    title = f"[목업] {label} 이벤트"
    warning = "개발 검증용 가상 데이터입니다. 실제 이벤트 또는 개인별 참여 가능 여부를 안내하는 것이 아닙니다."
    captions = [warning] + ([notice] if notice else [])
    if not events:
        captions.append("현재 진행 중인 이벤트가 없습니다.")
    intro = [{"type": "Text", "value": title, "size": "lg", "weight": "semibold"}]
    intro += [{"type": "Caption", "value": text} for text in captions]
    lines = [title, *captions]
    for event in events:
        lines.append(f"{event.description}\n{event.title}\n분류: {event.event_type}\n"
                     f"기간: {event.start_date} ~ {event.end_date}\n"
                     f"[자세히 보기 (목업)]({mock_events_url(event.id)})")
    more = {"type": "Button", "label": "더 많은 이벤트 보기", "variant": "outline", "block": True,
            "onClickAction": open_url_action(mock_events_url())}
    if len(events) == 1:
        row = {"type": "Row", "key": events[0].id, "gap": 3, "align": "center",
               "padding": {"y": 2}, "children": _event_row_children(events[0])}
        widget = {"type": "Card", "children": intro + [row, more]}
    elif events:
        rows = [{"type": "ListViewItem", "key": event.id, "gap": 3, "align": "center",
                 "onClickAction": open_url_action(mock_events_url(event.id)),
                 "children": _event_row_children(event)} for event in events]
        widget = {"type": "ListView", "limit": 7, "children":
            [{"type": "ListViewItem", "children": [{"type": "Col", "gap": 1, "children": intro}]}]
            + rows + [{"type": "ListViewItem", "children": [more]}]}
    else:
        widget = {"type": "Card", "children": intro + [more]}
    lines.append(f"[더 많은 이벤트 보기]({mock_events_url()})")
    return response(widget, "\n\n".join(lines))
