"""Isolated ES implementation of the existing getCreditCardDetail tool."""
from __future__ import annotations

from typing import Any
from mcp.types import ToolAnnotations
from kakao.card_search import card_name_clarification, credit_card_detail
from mci.es_card_client import EsCardClient, display_text
from tools.common import card_detail_from_mci, json_widget


def search_card_detail(client: EsCardClient, card_name: str) -> str:
    name = display_text(card_name)
    if not name:
        return json_widget(card_name_clarification(), tool_name='getCreditCardDetail')
    result = client.call_with_itf_id('EGN00002', data={
        'MSG': name, 'SIZ': 100, 'QEE': 'score',
        'AFE_MIN_VL': 0, 'AFE_MAX_VL': 5_000_000,
    })
    cards = result['GRID1']
    exact = [c for c in cards if c['CRD_PD_NM'].casefold() == name.casefold()]
    selected = exact[0] if len(exact) == 1 else (cards[0] if result['TO_CT'] == 1 else None)
    if selected is None:
        return json_widget(card_name_clarification(), tool_name='getCreditCardDetail')
    return json_widget(credit_card_detail(card_detail_from_mci(selected)), tool_name='getCreditCardDetail')


def register_es_card_search_tools(mcp: Any, client: EsCardClient | None = None) -> None:
    client = client or EsCardClient()

    @mcp.tool(name='getCreditCardDetail',
              description='신한카드 상품명으로 상세 혜택과 연회비를 조회합니다. cardName에는 정확한 카드명을 입력하세요.',
              tags={'scope:admin', 'scope:common', 'scope:agca'},
              meta={'tool_code': 'TL-COMM-005'},
              annotations=ToolAnnotations(title='신한카드 상품 상세 조회', readOnlyHint=True,
                                          destructiveHint=False, idempotentHint=True, openWorldHint=False))
    def get_credit_card_detail(cardName: str) -> str:
        return search_card_detail(client, cardName)
