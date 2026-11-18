"""이벤트 목록 위젯. 1건은 카드형, 2~5건은 목록형, 0건은 안내 카드.

각 행은 왼쪽 썸네일, 오른쪽 요약(텍스트1)·제목(텍스트2), 맨 오른쪽 상세 이동(>) 버튼으로
구성하고, 목록 맨 마지막에 "더 많은 이벤트 보기" 버튼을 둔다.
1건 카드형은 > 대신 "자세히 보기" 버튼만 두고 "더 많은 이벤트 보기"는 넣지 않는다.
"""
from __future__ import annotations

import os

from kakao.common import (Widget, WidgetResponse, absolute_url, add_card_referrer,
                          open_url_action, response)
from mci.event_client import Event

# 신한카드 진행 중 이벤트 목록. 로컬 목업 랜딩 등으로 바꿀 때는 EVENT_LIST_URL 로 덮어쓴다.
_DEFAULT_EVENT_LIST_URL = "https://www.shinhancard.com/mob/MOBFM829N/MOBFM829R03.shc?sourcePage=R01"


def event_list_url() -> str:
    return add_card_referrer(os.getenv("EVENT_LIST_URL", _DEFAULT_EVENT_LIST_URL))


def _detail_url(event: Event) -> str:
    """상세페이지 절대 URL + 카카오 유입 식별자(param=fr_kkt)."""
    return add_card_referrer(absolute_url(event.detail_url))


def _event_row_children(event: Event, *, chevron: bool = True) -> list[Widget]:
    thumbnail = {"type": "Image", "src": absolute_url(event.thumbnail_url, image=True),
                 "alt": f"{event.title} 썸네일", "width": 72, "height": 72,
                 "fit": "cover", "radius": "sm"}
    texts = {"type": "Col", "gap": 1, "flex": "auto", "children": [
        {"type": "Text", "value": event.description or event.title, "size": "sm",
         "weight": "semibold", "maxLines": 2},
        {"type": "Caption", "value": event.title, "maxLines": 1}]}
    detail = {"type": "Button", "label": "", "iconEnd": "chevron-right", "iconSize": "xl",
              "variant": "ghost", "uniform": True,
              "onClickAction": open_url_action(_detail_url(event))}
    return [thumbnail, texts, detail] if chevron else [thumbnail, texts]


def event_list(label: str, events: list[Event], *, notice: str | None = None) -> WidgetResponse:
    title = f"{label} 이벤트"
    captions = [notice] if notice else []
    if not events:
        captions.append("현재 진행 중인 이벤트가 없습니다.")
    intro = [{"type": "Text", "value": title, "size": "lg", "weight": "semibold"}]
    intro += [{"type": "Caption", "value": text} for text in captions]
    more_url = event_list_url()
    more = {"type": "Button", "label": "더 많은 이벤트 보기", "variant": "outline", "block": True,
            "onClickAction": open_url_action(more_url)}
    if len(events) == 1:
        # 카드형은 > 대신 "자세히 보기" 버튼으로 상세페이지에 이동한다.
        event = events[0]
        row = {"type": "Row", "key": event.id, "gap": 3, "align": "center",
               "padding": {"y": 2}, "children": _event_row_children(event, chevron=False)}
        detail = {"type": "Button", "label": "자세히 보기", "block": True,
                  "onClickAction": open_url_action(_detail_url(event))}
        widget = {"type": "Card", "children": intro + [row, detail]}
    elif events:
        rows = [{"type": "ListViewItem", "key": event.id, "gap": 3, "align": "center",
                 "onClickAction": open_url_action(_detail_url(event)),
                 "children": _event_row_children(event)} for event in events]
        widget = {"type": "ListView", "limit": 7, "children":
            [{"type": "ListViewItem", "children": [{"type": "Col", "gap": 1, "children": intro}]}]
            + rows + [{"type": "ListViewItem", "children": [more]}]}
    else:
        widget = {"type": "Card", "children": intro + [more]}

    lines = [f"### {title}", *captions, ""]
    for index, event in enumerate(events, start=1):
        lines.append(f"{index}. [{event.title}]({_detail_url(event)}) · "
                     f"{event.description} ({event.start_date} ~ {event.end_date})")
    if len(events) != 1:
        lines.append(f"\n[더 많은 이벤트 보기]({more_url})")
    return response(widget, "\n".join(lines))
