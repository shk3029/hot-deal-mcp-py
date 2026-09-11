"""카카오 툴 계약에서 사용하는 연회비 구간."""

from __future__ import annotations

from enum import Enum


class AnnualFeeBand(Enum):
    ZERO_TO_ONE       = ("0~1만원",   0,       9_999)
    ONE_TO_TWO        = ("1~2만원",   10_000,  19_999)
    TWO_TO_THREE      = ("2~3만원",   20_000,  29_999)
    THREE_TO_FOUR     = ("3~4만원",   30_000,  39_999)
    FOUR_TO_FIVE      = ("4~5만원",   40_000,  49_999)
    FIVE_TO_TEN       = ("5~10만원",  50_000,  99_999)
    OVER_TEN          = ("10만원이상", 100_000, 5_000_000)
    NO_LIMIT          = ("제한없음",   0,       5_000_000)
    
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
        """구간 대표값 (API 호출 등 단일값이 필요한 경우 활용)"""
        _rep = {
            AnnualFeeBand.ZERO_TO_ONE:   5_000,
            AnnualFeeBand.ONE_TO_TWO:    15_000,
            AnnualFeeBand.TWO_TO_THREE:  25_000,
            AnnualFeeBand.THREE_TO_FOUR: 35_000,
            AnnualFeeBand.FOUR_TO_FIVE:  45_000,
            AnnualFeeBand.FIVE_TO_TEN:   75_000,
            AnnualFeeBand.OVER_TEN:      150_000,
        }
        return _rep.get(self)

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
        for band in cls:
            if band.display_name == normalized:
            
                print(f"from string displayname: {band.display_name}, normalized : {normalized}")
                return band
        raise ValueError(f"지원하지 않는 연회비 구간입니다: {value}")