"""fetch_finance_tips 카카오툴즈 응답. 의도별 금융생활지식 콘텐츠 목록."""

from __future__ import annotations

from kakao.common import (
    Widget,
    WidgetResponse,
    open_url_action,
    response,
    send_user_message_action,
)
from schemas.finance_tips_schemas import ContentItem

# category 키 → (표시명, 위젯 타이틀). CATEGORY_MAP 키와 1:1.
_CATEGORY_META: dict[str, tuple[str, str]] = {
    "trend": ("트렌드", "TREND"),
    "finance": ("금융", "FINANCE"),
    "card_tips": ("카드연구소", "CARD LAB"),
}
_CATEGORY_CYCLE = ["trend", "finance", "card_tips"]


def _display_name(category: str) -> str:
    return _CATEGORY_META.get(category, (category, category.upper()))[0]


def _widget_title(category: str) -> str:
    return _CATEGORY_META.get(category, (category, category.upper()))[1]


def _next_category(category: str) -> str:
    if category not in _CATEGORY_CYCLE:
        return _CATEGORY_CYCLE[0]
    return _CATEGORY_CYCLE[(_CATEGORY_CYCLE.index(category) + 1) % len(_CATEGORY_CYCLE)]


def financial_knowledge_list(
    category: str,
    items: list[ContentItem],
) -> WidgetResponse:
    display_name = _display_name(category)

    list_items: list[Widget] = [
        {
            "type": "ListViewItem",
            "children": [
                {
                    "type": "Col",
                    "gap": 2,
                    "align": "start",
                    "padding": {"x": 2, "y": 2},
                    "children": [
                        {
                            "type": "Text",
                            "value": _widget_title(category),
                            "size": "lg",
                            "weight": "semibold",
                            "textAlign": "start",
                        },
                        {
                            "type": "Caption",
                            "value": f"금융생활지식 ({display_name})",
                            "textAlign": "start",
                        },
                    ],
                }
            ],
        }
    ]
    for index, item in enumerate(items, start=1):
        list_items.append(_article_row(index, item))

    next_display = _display_name(_next_category(category))
    list_items.append(
        {
            "type": "ListViewItem",
            "children": [
                {
                    "type": "Button",
                    "label": "다른 카테고리 보기",
                    "variant": "outline",
                    "block": True,
                    "onClickAction": send_user_message_action(
                        f"<{next_display}> 금융생활지식 보여줘"
                    ),
                }
            ],
        }
    )

    widget = {"type": "ListView", "limit": 10, "children": list_items}

    lines = [f"### 금융생활지식 · {display_name}", ""]
    for index, item in enumerate(items, start=1):
        lines.append(f"{index}. [{item.title}]({item.url})")
    copy_text = "\n".join(lines) + "\n"
    return response(widget, copy_text)


def _article_row(index: int, item: ContentItem) -> Widget:
    return {
        "type": "ListViewItem",
        "key": item.url,
        "align": "start",
        "gap": 3,
        "onClickAction": open_url_action(item.url),
        "children": [
            {
                "type": "Text",
                "value": f"{index:02d}",
                "weight": "semibold",
                "width": 32,
                "textAlign": "start",
            },
            {
                "type": "Col",
                "flex": 1,
                "align": "start",
                "padding": {"x": 1},
                "children": [
                    {
                        "type": "Text",
                        "value": item.title,
                        "width": "100%",
                        "textAlign": "start",
                        "maxLines": 3,
                    }
                ],
            },
        ],
    }
