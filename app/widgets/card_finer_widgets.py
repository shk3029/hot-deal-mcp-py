"""getCreditCardRecommendationsWithSelector 응답 위젯.

업종/연회비 재질문 셀렉터와 카드 추천 목록. Java ``PlayMcpWidgetFactory`` 대응.
"""

from __future__ import annotations

from app.domain.annual_fee_band import AnnualFeeBand
from app.domain.industry import Industry
from app.services.card_guide_service import CardGuide
from app.widgets.common import (
    MORE_CARDS_URL,
    Widget,
    WidgetResponse,
    benefit_category_badge,
    open_url_action,
    response,
    selector_button_rows,
    send_user_message_action,
)


def industry_selector() -> WidgetResponse:
    children: list[Widget] = [
        {"type": "Text", "value": "어떤 업종의 카드 혜택을 원하시나요?"}
    ]
    children.extend(selector_button_rows(Industry.selector_display_names()))
    widget = {"type": "Card", "children": children}
    return response(widget, "원하시는 업종을 선택해 주세요.")


def annual_fee_selector() -> WidgetResponse:
    children: list[Widget] = [
        {"type": "Text", "value": "원하시는 연회비 구간을 선택해주세요"}
    ]
    children.extend(selector_button_rows(AnnualFeeBand.display_names()))
    widget = {"type": "Card", "children": children}
    return response(widget, "원하시는 연회비 구간을 선택해 주세요.")


def credit_card_guide_list(
    guides: list[CardGuide],
    industry: Industry,
    annual_fee_band: AnnualFeeBand,
) -> WidgetResponse:
    card_rows = [_to_credit_card_list_row(guide) for guide in guides]

    more_cards_button = {
        "type": "Button",
        "label": "더 많은 카드 보기",
        "variant": "outline",
        "pill": True,
        "block": True,
        "onClickAction": open_url_action(MORE_CARDS_URL),
    }
    card_list = {
        "type": "Col",
        "gap": 4,
        "padding": {"x": 2, "y": 3},
        "children": card_rows,
    }
    widget = {"type": "Card", "children": [card_list, more_cards_button]}

    lines = [
        "### 카드 안내",
        "",
        f"- 업종: **{industry.display_name}**",
        f"- 연회비: **{annual_fee_band.display_name}**",
        "",
    ]
    for guide in guides:
        lines.append(f"- {guide.name} (`{guide.annual_fee}`)")
    copy_text = "\n".join(lines) + "\n"
    copy_text += (
        f"\n[더 많은 카드 보기]({MORE_CARDS_URL})"
        "\n\n_연회비와 혜택 조건은 카드 상세 페이지에서 최종 확인해 주세요._"
    )
    return response(widget, copy_text)


def _to_credit_card_list_row(guide: CardGuide) -> Widget:
    card_image = {
        "type": "Image",
        "src": guide.image_url,
        "alt": f"{guide.name} 카드 이미지",
        "width": 112,
        "height": 72,
        "fit": "contain",
        "radius": "sm",
    }
    annual_fee_row = {
        "type": "Row",
        "gap": 2,
        "children": [
            {
                "type": "Badge",
                "label": f"연회비 {guide.annual_fee}",
                "color": "info",
                "variant": "soft",
            }
        ],
    }

    detail_children: list[Widget] = [
        {
            "type": "Text",
            "value": guide.name,
            "size": "sm",
            "weight": "semibold",
            "maxLines": 2,
        },
        annual_fee_row,
    ]
    if guide.benefit_categories:
        detail_children.append(
            {
                "type": "Row",
                "gap": 2,
                "children": [
                    benefit_category_badge(category)
                    for category in guide.benefit_categories
                ],
            }
        )

    card_details = {
        "type": "Col",
        "gap": 2,
        "flex": "auto",
        "children": detail_children,
    }
    click_indicator = {
        "type": "Button",
        "label": ">",
        "variant": "ghost",
        "uniform": True,
        "size": "xl",
        "onClickAction": send_user_message_action(f"{guide.name} 혜택 알려줘"),
    }
    return {
        "type": "Row",
        "key": guide.name,
        "gap": 4,
        "align": "center",
        "padding": {"y": 2},
        "children": [card_image, card_details, click_indicator],
    }
