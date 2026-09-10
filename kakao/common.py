"""카카오툴즈 응답 공통 조각.

최상위 응답 형식은 ``{"widget": <위젯 또는 None>, "copy_text": <문자열>}`` 이다.
(기존 ``app/widgets`` 의 PlayMcpWidgetFactory 공용 헬퍼를 그대로 옮겨왔다.)
``status`` 는 카카오 쪽에서 자동으로 붙이므로 여기서는 넣지 않는다.
"""

from __future__ import annotations

from typing import Any

Widget = dict[str, Any]
WidgetResponse = dict[str, Any]

SELECTOR_BUTTONS_PER_ROW = 4
# 인기 카드 TOP10 차트 (인기카드 위젯의 "차트 보러가기" 버튼)
CARD_RANKING_URL = (
    "https://www.shinhancard.com/pconts/html/landing/2013846_2424.html?Tab=tab2"
)
# 카드 검색 화면 (카드 추천 위젯의 "더 많은 카드 보기" 버튼)
CARD_SEARCH_URL = (
    "https://www.shinhancard.com/mob/MOBFM039N/MOBFM039C01.shc?crustMenuId=ms467"
)

_CARD_HOST = "https://www.shinhancard.com"
_IMAGE_HOST = "https://cdn.www.shinhancard.com"


def response(widget: Widget | None, copy_text: str) -> WidgetResponse:
    return {"widget": widget, "copy_text": copy_text}


def absolute_url(path: str, *, image: bool = False) -> str:
    """상대 경로를 신한카드 절대 URL 로 바꾼다(MCI/목업 응답이 상대경로를 줄 때)."""
    if not path:
        return ""
    if path.startswith(("http://", "https://")):
        return path
    host = _IMAGE_HOST if image else _CARD_HOST
    return host + (path if path.startswith("/") else f"/{path}")


def format_won(amount: int) -> str:
    return f"{amount:,}원"


def annual_fee_range_label(minimum: int, maximum: int) -> str:
    if minimum <= 0 and maximum >= 5_000_000:
        return "제한없음"
    if minimum <= 0:
        return f"{maximum:,}원 이하"
    return f"{minimum:,}원 ~ {maximum:,}원"


def selector_button_rows(labels: list[str]) -> list[Widget]:
    rows: list[Widget] = []
    for index in range(0, len(labels), SELECTOR_BUTTONS_PER_ROW):
        buttons = [
            _selector_button(label)
            for label in labels[index : index + SELECTOR_BUTTONS_PER_ROW]
        ]
        rows.append({"type": "Row", "gap": 2, "children": buttons})
    return rows


def _selector_button(label: str) -> Widget:
    return {
        "type": "Button",
        "label": label,
        "onClickAction": send_user_message_action(label),
    }


def benefit_category_badge(category: str) -> Widget:
    return {
        "type": "Badge",
        "label": category,
        "color": "success",
        "variant": "soft",
    }


def send_user_message_action(text: str) -> Widget:
    return {
        "payload": {
            "target": {
                "type": "sendUserMessage",
                "properties": {"text": text},
            }
        }
    }


def open_url_action(url: str) -> Widget:
    return {"payload": {"target": {"url": url, "pcUrl": url}}}
