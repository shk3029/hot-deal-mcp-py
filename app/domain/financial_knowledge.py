"""금융생활지식 카테고리와 목(mock) 콘텐츠.

Java ``FinancialKnowledgeCategory`` enum + ``FinancialKnowledgeService`` 의 목 데이터.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FinancialKnowledgeCategory(Enum):
    TREND = ("트렌드", "TREND")
    FINANCE = ("금융", "FINANCE")
    CARD_LAB = ("카드연구소", "CARD LAB")

    def __init__(self, display_name: str, widget_title: str) -> None:
        self._display_name = display_name
        self._widget_title = widget_title

    @property
    def display_name(self) -> str:
        return self._display_name

    @property
    def widget_title(self) -> str:
        return self._widget_title

    def next(self) -> "FinancialKnowledgeCategory":
        order = [
            FinancialKnowledgeCategory.TREND,
            FinancialKnowledgeCategory.FINANCE,
            FinancialKnowledgeCategory.CARD_LAB,
        ]
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


@dataclass(frozen=True)
class Article:
    title: str
    url: str


_MOCK_ARTICLES: dict[FinancialKnowledgeCategory, list[Article]] = {
    FinancialKnowledgeCategory.TREND: [
        Article("데이터로 살펴본 2026 여행 트렌드", "https://www.shinhancardblog.com/1432"),
        Article("데이터로 살펴본 2026년 웰니스 트렌드", "https://www.shinhancardblog.com/1425"),
        Article(
            "데이터로 살펴본 외식 트렌드 : 경험 콘텐츠가 된 파인 다이닝",
            "https://www.shinhancardblog.com/1417",
        ),
        Article("2026년 주목할 만한 소비 트렌드 ‘WISE UP’", "https://www.shinhancardblog.com/1410"),
        Article(
            "경험소비가 늘어나는 이유, 사람들은 왜 물건보다 경험에 돈을 쓸까요?",
            "https://shinhangroup.com/kr/archive/insight/extend/detail/33245",
        ),
    ],
    FinancialKnowledgeCategory.FINANCE: [
        Article(
            "직장인이 점심값에 민감해진 이유 : 런치플레이션 시대의 생존법",
            "https://shinhangroup.com/kr/archive/insight/extend/detail/33233",
        ),
        Article(
            "노후 생활비 계산, 은퇴 후 실제 필요한 생활비는 어떻게 계산할까요?",
            "https://shinhangroup.com/kr/archive/insight/extend/detail/33235",
        ),
        Article(
            "새로워진 신한 슈퍼 SOL! 가입하고 런칭 이벤트 혜택 받는 방법",
            "https://www.shinhancardblog.com/1434",
        ),
    ],
    FinancialKnowledgeCategory.CARD_LAB: [
        Article(
            "[쏠깃한 카드 연구소] 지구와 나를 위한 더 나은 Plan 신한카드 ECO Plan",
            "https://www.shinhancardblog.com/1432",
        ),
        Article(
            "[쏠깃한 카드 연구소] 조건 없이 한층 더 강해진 혜택, 신한카드 Simple Plan+",
            "https://www.shinhancardblog.com/1424",
        ),
        Article(
            "[쏠깃한 카드 연구소] 복잡한 건 딱 질색일 땐? 신한카드 Simple Plan",
            "https://www.shinhancardblog.com/1415",
        ),
        Article(
            "[쏠깃한 카드 연구소] 장병들을 위한 ‘진짜’ 카드! 신한카드 나라사랑카드",
            "https://www.shinhancardblog.com/1412",
        ),
        Article(
            "[쏠깃한 카드 연구소] 사장님 지갑 쏠쏠해지는 Npay biz 신한카드",
            "https://www.shinhancardblog.com/1407",
        ),
    ],
}


def mock_articles(category: FinancialKnowledgeCategory) -> list[Article]:
    return list(_MOCK_ARTICLES[category])
