"""카카오 툴 계약에서 사용하는 연회비 구간."""

from __future__ import annotations

from enum import Enum


class AnnualFeeBand(Enum):
    TEN_THOUSAND_RANGE = ("0~1만원대", 0, 19_999)
    THIRTY_THOUSAND_RANGE = ("2~3만원대", 20_000, 39_999)
    NO_LIMIT = ("제한없음", 0, 5_000_000)

    def __init__(self, display_name: str, minimum: int, maximum: int) -> None:
        self._display_name = display_name
        self._minimum = minimum
        self._maximum = maximum

    @property
    def display_name(self) -> str:
        return self._display_name

    @property
    def minimum(self) -> int:
        return self._minimum

    @property
    def maximum(self) -> int:
        return self._maximum

    @property
    def representative_fee(self) -> int | None:
        if self is AnnualFeeBand.TEN_THOUSAND_RANGE:
            return 10_000
        if self is AnnualFeeBand.THIRTY_THOUSAND_RANGE:
            return 30_000
        return None

    def matches(self, annual_fee: int) -> bool:
        return self.minimum <= annual_fee <= self.maximum

    @classmethod
    def display_names(cls) -> list[str]:
        return [band.display_name for band in cls]

    @classmethod
    def from_string(cls, value: str | None) -> "AnnualFeeBand":
        if value is None or not value.strip():
            return cls.NO_LIMIT

        normalized = value.strip().replace(" ", "")
        if normalized == "3만원대":
            normalized = cls.THIRTY_THOUSAND_RANGE.display_name
        for band in cls:
            if band.display_name == normalized:
                return band
        raise ValueError(f"지원하지 않는 연회비 구간입니다: {value}")
