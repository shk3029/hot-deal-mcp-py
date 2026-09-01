"""getFinancialLifeKnowledgeArticles — 의도별 금융생활지식 콘텐츠 목록.

Java ``FinancialKnowledgeToolConfig`` 대응.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated

from mcp.types import ToolAnnotations
from pydantic import Field

from app import deps
from app.domain.financial_knowledge import FinancialKnowledgeCategory
from app.tools.common import json_widget
from app.widgets import finance_tips_widgets

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

_ERROR_MESSAGE = "### 금융생활지식을 불러오지 못했습니다.\n\n잠시 후 다시 시도해 주세요."
_TITLE = "금융생활지식 콘텐츠"
_DESCRIPTION = (
    "Returns Shinhan financial-life articles grouped by intent. Use category 트렌드 for "
    "consumer trends, spending reports, consumption data, or general financial content; 금융 "
    "for practical money knowledge, financial issues, or Shinhan guidance; 카드연구소 for "
    "smart card usage, card tips, saving tips, or useful card information."
)


def register_finance_tips_tools(mcp: "FastMCP") -> None:
    @mcp.tool(
        name="getFinancialLifeKnowledgeArticles",
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
            Field(
                description=(
                    "질문의 의도에 해당하는 콘텐츠 카테고리. 허용값: 트렌드, 금융, 카드연구소. "
                    "'요즘 소비 트렌드', '금융 상식', '사람들 돈 어디에 써', '볼만한 금융 콘텐츠', "
                    "'소비 리포트·데이터 분석'은 트렌드, '돈 관련 알아둘 정보', '금융생활에 도움되는 정보', "
                    "'이슈되는 금융 이야기', '신한카드 안내'는 금융, '카드 똑똑하게 쓰는 법', '카드 꿀팁', "
                    "'절약 팁'은 카드연구소를 사용합니다. 명확하지 않으면 트렌드를 사용합니다."
                )
            ),
        ] = None,
    ) -> str:
        """의도별로 묶인 신한 금융생활지식 콘텐츠 목록을 위젯으로 보여준다."""
        try:
            parsed_category = FinancialKnowledgeCategory.from_string(category)
            payload = finance_tips_widgets.financial_knowledge_list(
                parsed_category,
                deps.financial_service.find_articles(parsed_category),
            )
            logger.info(
                "MCP 툴 호출 완료 - tool=getFinancialLifeKnowledgeArticles, category=%s",
                parsed_category.display_name,
            )
            return json_widget(payload)
        except Exception as exception:  # noqa: BLE001
            logger.exception("MCP 툴 처리 실패 - tool=getFinancialLifeKnowledgeArticles")
            raise RuntimeError(_ERROR_MESSAGE) from exception
