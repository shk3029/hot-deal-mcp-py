"""feature/test 호환 금융생활지식 툴."""

from __future__ import annotations

import logging
from typing import Annotated, Any

from mcp.types import ToolAnnotations
from pydantic import Field

from domain.financial_knowledge import FinancialKnowledgeCategory
from kakao.finance_tips import financial_knowledge_list
from schemas.finance_tips_schemas import ContentItem
from tools.common import json_widget, log_tool_request
from tools.finance_tips.constants import CATEGORY_MAP

logger = logging.getLogger(__name__)

_TITLE = "금융생활지식 콘텐츠"
_ERROR_MESSAGE = "### 금융생활지식을 불러오지 못했습니다.\n\n잠시 후 다시 시도해 주세요."
_DESCRIPTION = (
    "Returns Shinhan Card(신한카드) financial-life articles grouped by intent. "
    "Use category 트렌드 for "
    "consumer trends, spending reports, consumption data, or general financial content; 금융 "
    "for practical money knowledge, financial issues, or Shinhan guidance; 카드연구소 for "
    "smart card usage, card tips, saving tips, or useful card information."
)
_TOOL_NAME = "getFinancialLifeKnowledgeArticles"


def register_finance_tips_tools(mcp: Any) -> None:
    @mcp.tool(
        name=_TOOL_NAME,
        tags={"scope:admin", "scope:common", "scope:agca"},
        meta={"tool_code": "TL-COMM-007"},
        title=_TITLE,
        description=_DESCRIPTION,
        annotations=ToolAnnotations(
            title=_TITLE,
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )
    def get_financial_life_knowledge_articles(
        category: Annotated[
            str | None,
            Field(description=(
                "질문의 의도에 해당하는 콘텐츠 카테고리. 허용값: 트렌드, 금융, 카드연구소. "
                "'요즘 소비 트렌드', '금융 상식', '사람들 돈 어디에 써', '볼만한 금융 콘텐츠', "
                "'소비 리포트·데이터 분석'은 트렌드, '돈 관련 알아둘 정보', '금융생활에 도움되는 정보', "
                "'이슈되는 금융 이야기', '신한카드 안내'는 금융, '카드 똑똑하게 쓰는 법', '카드 꿀팁', "
                "'절약 팁'은 카드연구소를 사용합니다. 명확하지 않으면 트렌드를 사용합니다."
            )),
        ] = None,
    ) -> str:
        log_tool_request(_TOOL_NAME, {"category": category})
        try:
            parsed = FinancialKnowledgeCategory.from_string(category)
            items = [
                ContentItem(
                    title=item.value.title,
                    url=item.value.url,
                    intent=item.value.intent,
                    next_action=item.value.next_action,
                )
                for item in CATEGORY_MAP[parsed.internal_key]
            ]
            return json_widget(
                financial_knowledge_list(parsed.internal_key, items),
                tool_name=_TOOL_NAME,
            )
        except Exception as exception:
            logger.exception("MCP 툴 처리 실패 - tool=getFinancialLifeKnowledgeArticles")
            raise RuntimeError(_ERROR_MESSAGE) from exception
