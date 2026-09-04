"""카카오 툴 계약에서 사용하는 카드 정렬 기준."""

from __future__ import annotations

from enum import Enum


class CardSortOrder(Enum):
    RELEASE_DATE = "출시일순"
    ANNUAL_FEE = "연회비순"

    @property
    def display_name(self) -> str:
        return self.value

    @classmethod
    def from_string(cls, value: str | None) -> "CardSortOrder":
        if value is None or not value.strip():
            return cls.RELEASE_DATE

        normalized = value.strip().replace(" ", "")
        for order in cls:
            if order.display_name == normalized:
                return order
        raise ValueError(f"지원하지 않는 정렬 기준입니다: {value}")
