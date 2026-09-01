"""연회비 구간. Java ``AnnualFeeBand`` enum 의 파이썬 포팅."""

from __future__ import annotations

from enum import Enum


class AnnualFeeBand(Enum):
    TEN_THOUSAND_RANGE = ("0~1만원대", 10_000)
    THIRTY_THOUSAND_RANGE = ("2~3만원대", 30_000)
    NO_LIMIT = ("제한없음", None)

    def __init__(self, display_name: str, representative_fee: int | None) -> None:
        self._display_name = display_name
        self._representative_fee = representative_fee

    @property
    def display_name(self) -> str:
        return self._display_name

    @property
    def representative_fee(self) -> int | None:
        return self._representative_fee

    def matches(self, annual_fee: int) -> bool:
        if self is AnnualFeeBand.TEN_THOUSAND_RANGE:
            return 0 <= annual_fee < 20_000
        if self is AnnualFeeBand.THIRTY_THOUSAND_RANGE:
            return 20_000 <= annual_fee < 40_000
        return True

    @classmethod
    def display_names(cls) -> list[str]:
        return [band.display_name for band in cls]

    @classmethod
    def from_string(cls, value: str | None) -> "AnnualFeeBand":
        if value is None or not value.strip():
            return cls.NO_LIMIT

        normalized = value.strip().replace(" ", "")
        for band in cls:
            if band.display_name.replace(" ", "") == normalized:
                return band
        raise ValueError(f"지원하지 않는 연회비 구간입니다: {value}")
