"""fetch_card_finder 카카오툴즈 응답.

업종 재질문 셀렉터 + 조건별 카드 추천 목록. (연회비 셀렉터는 제거됨 —
새 시그니처의 annualFeeMin/Max 는 항상 값이 있어 재질문 트리거가 없다.)
"""

from __future__ import annotations

import random

from domain.industry import Industry
from kakao.common import (
    CARD_SEARCH_URL,
    Widget,
    WidgetResponse,
    absolute_url,
    benefit_category_badge,
    format_won,
    open_url_action,
    response,
    selector_button_rows,
    send_user_message_action,
)
from schemas.card_finder_tools_schemas import Card


def industry_selector() -> WidgetResponse:
    children: list[Widget] = [
        {"type": "Text", "value": "어떤 업종의 카드 혜택을 원하시나요?"}
    ]
    children.extend(selector_button_rows(Industry.selector_display_names()))
    widget = {"type": "Card", "children": children}
    return response(widget, "원하시는 업종을 선택해 주세요.")


def credit_card_guide_list(
    cards: list[Card],
    industry: Industry,
    annual_fee_label: str,
) -> WidgetResponse:
    card_rows = [_to_credit_card_list_row(industry, card) for card in cards]

    more_cards_button = {
        "type": "Button",
        "label": "더 많은 카드 보기",
        "variant": "outline",
        "pill": True,
        "block": True,
        "onClickAction": open_url_action(CARD_SEARCH_URL),
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
        f"- 연회비: **{annual_fee_label}**",
        "",
    ]
    for card in cards:
        lines.append(f"- {card.CRD_PD_NM} (`{format_won(card.CRD_PD_AFE)}`)")
    copy_text = "\n".join(lines) + "\n"
    copy_text += (
        f"\n[더 많은 카드 보기]({CARD_SEARCH_URL})"
        "\n\n_연회비와 혜택 조건은 카드 상세 페이지에서 최종 확인해 주세요._"
    )
    return response(widget, copy_text)


def _to_credit_card_list_row(searched_industry: Industry, card: Card) -> Widget:
    card_image = {
        "type": "Image",
        "src": absolute_url(card.CRD_PD_IMG_URL, image=True),
        "alt": f"{card.CRD_PD_NM} 카드 이미지",
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
                "label": f"연회비 {format_won(card.CRD_PD_AFE)}",
                "color": "info",
                "variant": "soft",
            }
        ],
    }

    detail_children: list[Widget] = [
        {
            "type": "Text",
            "value": card.CRD_PD_NM,
            "size": "sm",
            "weight": "semibold",
            "maxLines": 2,
        },
        annual_fee_row,
    ]
    categories = _benefit_categories(searched_industry, card.CRD_PD_BNF_CD)
    if categories:
        detail_children.append(
            {
                "type": "Row",
                "gap": 2,
                "children": [
                    benefit_category_badge(category) for category in categories
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
        "onClickAction": send_user_message_action(f"{card.CRD_PD_NM} 혜택 알려줘"),
    }
    return {
        "type": "Row",
        "key": card.CRD_PD_NM,
        "gap": 4,
        "align": "center",
        "padding": {"y": 2},
        "children": [card_image, card_details, click_indicator],
    }


def _benefit_categories(searched_industry: Industry, benefit_code_field: str) -> list[str]:
    """카드의 혜택 업종코드(콤마 구분) → 대표 업종명 최대 3개. 기존 로직 유지."""
    other_categories: list[str] = []
    for raw_code in benefit_code_field.split(","):
        code = raw_code.strip()
        if not code:
            continue
        try:
            industry = Industry.from_code(int(code))
        except ValueError:
            continue
        name = industry.widget_display_name
        if industry is not searched_industry and name not in other_categories:
            other_categories.append(name)

    random.shuffle(other_categories)
    return [searched_industry.widget_display_name, *other_categories[:2]]
