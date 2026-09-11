"""카카오 툴 계약에서 사용하는 카드 정렬 기준."""

from __future__ import annotations

from enum import Enum


class CardSortOrder(Enum):
    SCORE       = "정확도순"
    RELEASE_DATE = "출시일순"
    HIGH_RATE   = "높은연회비순"
    LOW_RATE    = "낮은연회비순"

    @property
    def display_name(self) -> str:
        return self.value

    @property
    def api_code(self) -> str:
        """MCI API QEE 필드에 전달할 영문 정렬 코드."""
        mapping = {
            CardSortOrder.SCORE:        "score",
            CardSortOrder.RELEASE_DATE: "date",
            CardSortOrder.HIGH_RATE:    "high_rate",
            CardSortOrder.LOW_RATE:     "low_rate",
        }
        return mapping[self]

    @classmethod
    def from_string(cls, value: str | None) -> "CardSortOrder":
        if value is None or not value.strip():
            return cls.RELEASE_DATE  # 기본값: 출시일순

        normalized = value.strip().replace(" ", "")
        for order in cls:
            if order.display_name == normalized:
                return order
        raise ValueError(f"지원하지 않는 정렬 기준입니다: {value!r}")
