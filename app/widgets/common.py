"""위젯 모듈 공통 타입/조각.

Java ``PlayMcpWidgetFactory`` 의 공용 헬퍼(응답 래퍼, 셀렉터 버튼, onClickAction 2종,
공통 배지)에 대응한다. 최상위 응답 형식은
``{"widget": <위젯 또는 None>, "copy_text": <문자열>}`` 이다(Java ``PlayMcpWidgetResponse``).
``status`` 는 PlayMCP 가 자동으로 붙이므로 여기서는 넣지 않는다.
"""

from __future__ import annotations

from typing import Any

Widget = dict[str, Any]
WidgetResponse = dict[str, Any]

SELECTOR_BUTTONS_PER_ROW = 4
MORE_CARDS_URL = (
    "https://www.shinhancard.com/pconts/html/landing/2013846_2424.html?Tab=tab2"
    "&utm_source=naver_mo&utm_medium=brandsearch_sa"
    "&utm_campaign=main&utm_content=news"
)


def response(widget: Widget | None, copy_text: str) -> WidgetResponse:
    return {"widget": widget, "copy_text": copy_text}


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
