"""getCreditCardDetail 응답 위젯.

카드명 되묻기와 카드 한 장 상세. Java ``PlayMcpWidgetFactory`` 대응.
"""

from __future__ import annotations

from app.services.card_guide_service import CardDetail
from app.widgets.common import Widget, WidgetResponse, open_url_action, response


def card_name_clarification() -> WidgetResponse:
    message = "조회할 신한카드 상품명을 정확히 말씀해 주세요."
    widget = {"type": "Card", "children": [{"type": "Text", "value": message}]}
    return response(widget, message)


def credit_card_detail(detail: CardDetail) -> WidgetResponse:
    children: list[Widget] = [
        _card_detail_header(detail),
        {"type": "Divider"},
        {"type": "Text", "value": "주요 혜택", "weight": "semibold"},
    ]
    children.extend(_card_benefit_row(benefit) for benefit in detail.benefits)
    children.append(_detail_page_button(detail.detail_page_url))

    widget = {"type": "Card", "children": children}

    lines = [
        f"### {detail.name}",
        f"- 연회비: **{detail.annual_fee}**",
        "",
        "#### 주요 혜택",
    ]
    for benefit in detail.benefits:
        lines.append(f"- {benefit}")
    copy_text = "\n".join(lines) + "\n"
    copy_text += f"\n[자세히 보기]({detail.detail_page_url})"
    return response(widget, copy_text)


def _card_detail_header(detail: CardDetail) -> Widget:
    card_image = {
        "type": "Image",
        "src": detail.image_url,
        "alt": f"{detail.name} 카드 이미지",
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
                "value": detail.name,
                "size": "lg",
                "weight": "semibold",
                "maxLines": 2,
            },
            {
                "type": "Badge",
                "label": f"연회비 {detail.annual_fee}",
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
