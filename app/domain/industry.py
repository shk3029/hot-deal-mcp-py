"""소비 업종(1~24). Java ``Industry`` enum 의 파이썬 포팅."""

from __future__ import annotations

from enum import Enum

# 선택 위젯에 노출하는 업종 코드. Java SELECTOR_VISIBLE_CODES 와 동일하다.
_SELECTOR_VISIBLE_CODES = frozenset({1, 2, 3, 4, 5, 6, 7, 9, 10, 12, 13, 15, 16, 20})


class Industry(Enum):
    ANYWHERE = (1, "어디서나")
    FUEL = (2, "주유")
    LARGE_MART = (3, "대형마트")
    CONVENIENCE_STORE = (4, "편의점")
    SHOPPING = (5, "쇼핑")
    MOVIE_PERFORMANCE = (6, "영화/공연")
    DINING_DELIVERY = (7, "외식/배달")
    CAFE = (8, "카페")
    PUBLIC_TRANSPORT = (9, "대중교통")
    HOSPITAL_PHARMACY = (10, "병원/약국")
    UTILITIES = (11, "공과금")
    TELECOM = (12, "통신")
    EDUCATION_CHILDCARE = (13, "교육/육아")
    LEISURE = (14, "레저")
    AIRLINE = (15, "항공")
    AIRPORT = (16, "공항")
    BEAUTY = (17, "뷰티")
    SIMPLE_PAYMENT = (18, "간편결제")
    SUBSCRIPTION = (19, "구독")
    TRAVEL_STAY = (20, "여행/숙박")
    FINANCE = (21, "금융")
    DISCOUNT = (22, "할인")
    POINTS = (23, "적립")
    YOUTH = (24, "청소년")

    def __init__(self, code: int, display_name: str) -> None:
        self._code = code
        self._display_name = display_name

    @property
    def code(self) -> int:
        return self._code

    @property
    def display_name(self) -> str:
        return self._display_name

    @property
    def widget_display_name(self) -> str:
        if self is Industry.AIRLINE:
            return "마일리지"
        if self is Industry.AIRPORT:
            return "공항라운지"
        return self._display_name

    @property
    def selector_visible(self) -> bool:
        return self._code in _SELECTOR_VISIBLE_CODES

    @classmethod
    def display_names(cls) -> list[str]:
        return [industry.display_name for industry in cls]

    @classmethod
    def selector_display_names(cls) -> list[str]:
        return [
            industry.widget_display_name
            for industry in cls
            if industry.selector_visible
        ]

    @classmethod
    def from_code(cls, code: int) -> "Industry":
        for industry in cls:
            if industry.code == code:
                return industry
        raise ValueError(f"지원하지 않는 업종 코드입니다: {code}")
