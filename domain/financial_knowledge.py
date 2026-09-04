"""금융생활지식 카테고리 계약."""

from __future__ import annotations

from enum import Enum


class FinancialKnowledgeCategory(Enum):
    TREND = ("트렌드", "TREND", "trend")
    FINANCE = ("금융", "FINANCE", "finance")
    CARD_LAB = ("카드연구소", "CARD LAB", "card_tips")

    def __init__(self, display_name: str, widget_title: str, internal_key: str) -> None:
        self._display_name = display_name
        self._widget_title = widget_title
        self._internal_key = internal_key

    @property
    def display_name(self) -> str:
        return self._display_name

    @property
    def widget_title(self) -> str:
        return self._widget_title

    @property
    def internal_key(self) -> str:
        return self._internal_key

    def next(self) -> "FinancialKnowledgeCategory":
        order = list(type(self))
        return order[(order.index(self) + 1) % len(order)]

    @classmethod
    def from_string(cls, value: str | None) -> "FinancialKnowledgeCategory":
        if value is None or not value.strip():
            return cls.TREND
        normalized = value.strip().replace(" ", "")
        for category in cls:
            if category.display_name == normalized:
                return category
        raise ValueError(f"지원하지 않는 금융생활지식 카테고리입니다: {value}")
