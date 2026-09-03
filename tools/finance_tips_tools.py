from __future__ import annotations

import traceback

from mcp.types import ToolAnnotations

from kakao.finance_tips import financial_knowledge_list
from schemas.finance_tips_schemas import ContentItem, ContentResult
from tools.common import with_kakao
from tools.finance_tips.constants import CATEGORY_MAP

_TITLE = "금융생활지식 콘텐츠"
_DESCRIPTION = (
    "Returns Shinhan Card(신한카드) financial-life articles grouped by intent. "
    "Use category trend for "
    "consumer trends, spending reports, consumption data, or general financial content; "
    "finance for practical money knowledge, financial issues, or Shinhan guidance; "
    "card_tips for smart card usage, card tips, saving tips, or useful card information."
)


def register_finance_tips_tools(mcp):

    @mcp.tool(
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
    def fetch_finance_tips(
        category: str,
    ) -> ContentResult:
        """
        의도별로 묶인 신한 금융생활지식 콘텐츠 목록을 조회합니다.
        """
        if not category or category not in CATEGORY_MAP:
            return ContentResult(
                error=f"category는 필수이며 {list(CATEGORY_MAP.keys())} 중 하나여야 합니다."
            )

        try:
            enum_cls = CATEGORY_MAP[category]
            items = list(enum_cls)

            contents = [
                ContentItem(
                    title=item.value.title,
                    url=item.value.url,
                    intent=item.value.intent,
                    next_action=item.value.next_action,
                )
                for item in items
            ]

            result = ContentResult(contents=contents, totalCount=len(contents))
            return with_kakao(result, financial_knowledge_list(category, contents))

        except Exception as e:
            print(f"[ERROR] {traceback.format_exc()}")
            return ContentResult(error=f"콘텐츠 조회 중 오류가 발생했습니다: {e}")
