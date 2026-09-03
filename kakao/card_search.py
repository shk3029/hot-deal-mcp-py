"""fetch_card_search 카카오툴즈 응답.

카드명 되묻기 + 카드 한 장 상세.
"""

from __future__ import annotations

from kakao.common import (
    Widget,
    WidgetResponse,
    absolute_url,
    format_won,
    open_url_action,
    response,
)
from schemas.card_finder_tools_schemas import CardDetail


def card_name_clarification() -> WidgetResponse:
    message = "조회할 신한카드 상품명을 정확히 말씀해 주세요."
    widget = {"type": "Card", "children": [{"type": "Text", "value": message}]}
    return response(widget, message)


def credit_card_detail(card: CardDetail) -> WidgetResponse:
    benefits = _benefits(card)

    children: list[Widget] = [
        _card_detail_header(card),
        {"type": "Divider"},
        {"type": "Text", "value": "주요 혜택", "weight": "semibold"},
    ]
    children.extend(_card_benefit_row(benefit) for benefit in benefits)
    children.append(_detail_page_button(absolute_url(card.CRD_PD_URL)))

    widget = {"type": "Card", "children": children}

    lines = [
        f"### {card.CRD_PD_NM}",
        f"- 연회비: **{format_won(card.CRD_PD_AFE)}**",
        "",
        "#### 주요 혜택",
    ]
    for benefit in benefits:
        lines.append(f"- {benefit}")
    copy_text = "\n".join(lines) + "\n"
    copy_text += f"\n[자세히 보기]({absolute_url(card.CRD_PD_URL)})"
    return response(widget, copy_text)


def _benefits(card: CardDetail) -> list[str]:
    pairs = [
        (card.CRD_PD_BNF_NM1, card.CRD_PD_BNF_DL1),
        (card.CRD_PD_BNF_NM2, card.CRD_PD_BNF_DL2),
        (card.CRD_PD_BNF_NM3, card.CRD_PD_BNF_DL3),
    ]
    benefits: list[str] = []
    for name, detail in pairs:
        name = (name or "").strip()
        detail = (detail or "").strip()
        if name and detail:
            benefits.append(f"{name} · {detail}")
        elif name:
            benefits.append(name)
        elif detail:
            benefits.append(detail)
    return benefits


def _card_detail_header(card: CardDetail) -> Widget:
    card_image = {
        "type": "Image",
        "src": absolute_url(card.CRD_PD_IMG_URL, image=True),
        "alt": f"{card.CRD_PD_NM} 카드 이미지",
        "width": 112,
        "height": 72,
        "fit": "contain",
        "radius": "sm",
    }
    card_summary = {
        "type": "Col",
        "gap": 2,
        "flex": 1,
        "children": [
            {
                "type": "Text",
                "value": card.CRD_PD_NM,
                "size": "lg",
                "weight": "semibold",
                "maxLines": 2,
            },
            {
                "type": "Badge",
                "label": f"연회비 {format_won(card.CRD_PD_AFE)}",
                "color": "info",
                "variant": "soft",
            },
        ],
    }
    return {
        "type": "Row",
        "gap": 3,
        "align": "start",
        "children": [card_image, card_summary],
    }


def _card_benefit_row(benefit: str) -> Widget:
    return {
        "type": "Row",
        "gap": 2,
        "children": [
            {"type": "Text", "value": "✓", "weight": "semibold"},
            {"type": "Text", "value": benefit, "flex": 1},
        ],
    }


def _detail_page_button(detail_page_url: str) -> Widget:
    return {
        "type": "Button",
        "label": "자세히 보기",
        "onClickAction": open_url_action(detail_page_url),
    }
