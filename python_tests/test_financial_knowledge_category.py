import pytest

from app.domain.financial_knowledge import FinancialKnowledgeCategory


def test_missing_category_defaults_to_trend() -> None:
    assert FinancialKnowledgeCategory.from_string(None) is FinancialKnowledgeCategory.TREND
    assert FinancialKnowledgeCategory.from_string(" ") is FinancialKnowledgeCategory.TREND


def test_parses_supported_categories_ignoring_spaces() -> None:
    assert FinancialKnowledgeCategory.from_string("트렌드") is FinancialKnowledgeCategory.TREND
    assert FinancialKnowledgeCategory.from_string("금융") is FinancialKnowledgeCategory.FINANCE
    assert (
        FinancialKnowledgeCategory.from_string("카드 연구소")
        is FinancialKnowledgeCategory.CARD_LAB
    )


def test_cycles_through_all_categories() -> None:
    assert FinancialKnowledgeCategory.TREND.next() is FinancialKnowledgeCategory.FINANCE
    assert FinancialKnowledgeCategory.FINANCE.next() is FinancialKnowledgeCategory.CARD_LAB
    assert FinancialKnowledgeCategory.CARD_LAB.next() is FinancialKnowledgeCategory.TREND


def test_rejects_unsupported_category() -> None:
    with pytest.raises(ValueError):
        FinancialKnowledgeCategory.from_string("보험")
