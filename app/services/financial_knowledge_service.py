"""금융생활지식 콘텐츠 서비스. Java ``FinancialKnowledgeService`` 의 포팅."""

from __future__ import annotations

from app.domain.financial_knowledge import (
    Article,
    FinancialKnowledgeCategory,
    mock_articles,
)


class FinancialKnowledgeService:
    def find_articles(self, category: FinancialKnowledgeCategory) -> list[Article]:
        return mock_articles(category)
