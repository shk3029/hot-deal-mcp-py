"""fetch_popular_card 카카오툴즈 응답. 인기 TOP5 랭킹 카드."""

from __future__ import annotations

from domain.industry import Industry
from kakao.common import (
    CARD_RANKING_URL,
    Widget,
    WidgetResponse,
    absolute_url,
    benefit_category_badge,
    open_url_action,
    response,
    send_user_message_action,
)
from schemas.card_finder_tools_schemas import CardDetail


def popular_credit_card_list(cards: list[CardDetail]) -> WidgetResponse:
    ranked = list(enumerate(cards, start=1))

    children: list[Widget] = [
        {
            "type": "Text",
            "value": "추천 TOP5",
            "size": "lg",
            "weight": "semibold",
        },
        {"type": "Caption", "value": "신한카드에서 추천해드리는 카드예요!"},
        {
            "type": "Col",
            "gap": 4,
            "padding": {"x": 2, "y": 3},
            "children": [_popular_credit_card_row(rank, card) for rank, card in ranked],
        },
        {
            "type": "Button",
            "label": "신한카드 TOP10 차트 보러가기",
            "variant": "outline",
            "block": True,
            "onClickAction": open_url_action(CARD_RANKING_URL),
        },
    ]
    widget = {"type": "Card", "children": children}

    lines = ["### 추천 TOP5", "", "신한카드에서 추천해드리는 카드예요!", ""]
    for rank, card in ranked:
        lines.append(f"{rank}. **{card.CRD_PD_NM}** · {_category(card)}")
    copy_text = "\n".join(lines) + "\n"
    copy_text += f"\n[신한카드 TOP10 차트 보러가기]({CARD_RANKING_URL})"
    return response(widget, copy_text)


def _category(card: CardDetail) -> str:
    for raw_code in card.CRD_PD_BNF_CD.split(","):
        code = raw_code.strip()
        if not code:
            continue
        try:
            return Industry.from_code(int(code)).widget_display_name
        except ValueError:
            continue
    return "신한카드"


def _popular_credit_card_row(rank: int, card: CardDetail) -> Widget:
    rank_label = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, str(rank))
    rank_size = "xl" if rank <= 3 else "lg"
    card_image = {
        "type": "Image",
        "src": absolute_url(card.CRD_PD_IMG_URL, image=True),
        "alt": f"{card.CRD_PD_NM} 카드 이미지",
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
                "value": card.CRD_PD_NM,
                "size": "sm",
                "weight": "semibold",
                "maxLines": 2,
            },
            {
                "type": "Row",
                "gap": 2,
                "children": [benefit_category_badge(_category(card))],
            },
        ],
    }
    click_indicator = {
        "type": "Button",
        "label": "",
        "iconEnd": "chevron-right",
        "iconSize": "xl",
        "variant": "ghost",
        "uniform": True,
        "onClickAction": send_user_message_action(f"{card.CRD_PD_NM} 혜택 알려줘"),
    }
    return {
        "type": "Row",
        "key": card.CRD_PD_NM,
        "gap": 4,
        "align": "center",
        "padding": {"y": 2},
        "children": [
            {
                "type": "Text",
                "value": rank_label,
                "size": rank_size,
                "weight": "semibold",
                "width": 32,
                "textAlign": "center",
            },
            card_image,
            card_details,
            click_indicator,
        ],
    }
