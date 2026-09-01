"""getPopularCreditCards 응답 위젯.

인기 TOP5 랭킹 카드. Java ``PlayMcpWidgetFactory`` 대응.
"""

from __future__ import annotations

from app.services.popular_card_service import PopularCard
from app.widgets.common import (
    MORE_CARDS_URL,
    Widget,
    WidgetResponse,
    benefit_category_badge,
    open_url_action,
    response,
)


def popular_credit_card_list(popular_cards: list[PopularCard]) -> WidgetResponse:
    children: list[Widget] = [
        {
            "type": "Text",
            "value": "🔥 인기 TOP5",
            "size": "lg",
            "weight": "semibold",
        },
        {"type": "Caption", "value": "신한카드에서 발급량이 가장 많은 카드예요"},
        {
            "type": "Col",
            "gap": 4,
            "padding": {"x": 2, "y": 3},
            "children": [_popular_credit_card_row(card) for card in popular_cards],
        },
        {
            "type": "Button",
            "label": "신한카드 TOP10 차트 보러가기",
            "variant": "outline",
            "block": True,
            "onClickAction": open_url_action(MORE_CARDS_URL),
        },
    ]
    widget = {"type": "Card", "children": children}

    lines = ["### 🔥 인기 TOP5", "", "신한카드에서 발급량이 가장 많은 카드예요.", ""]
    for card in popular_cards:
        lines.append(f"{card.rank}. **{card.name}** · {card.category}")
    copy_text = "\n".join(lines) + "\n"
    copy_text += f"\n[신한카드 TOP10 차트 보러가기]({MORE_CARDS_URL})"
    return response(widget, copy_text)


def _popular_credit_card_row(card: PopularCard) -> Widget:
    rank_label = {1: "🥇", 2: "🥈", 3: "🥉"}.get(card.rank, str(card.rank))
    card_image = {
        "type": "Image",
        "src": card.image_url,
        "alt": f"{card.name} 카드 이미지",
        "width": 112,
        "height": 72,
        "fit": "contain",
        "radius": "sm",
    }
    card_details = {
        "type": "Col",
        "gap": 2,
        "flex": "auto",
        "children": [
            {
                "type": "Text",
                "value": card.name,
                "size": "sm",
                "weight": "semibold",
                "maxLines": 2,
            },
            {
                "type": "Row",
                "gap": 2,
                "children": [benefit_category_badge(card.category)],
            },
        ],
    }
    return {
        "type": "Row",
        "key": card.name,
        "gap": 4,
        "align": "center",
        "padding": {"y": 2},
        "children": [
            {
                "type": "Text",
                "value": rank_label,
                "size": "lg",
                "weight": "semibold",
            },
            card_image,
            card_details,
        ],
    }
