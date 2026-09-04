from __future__ import annotations
from enum import Enum
from dataclasses import dataclass

# ── 콘텐츠 데이터 정의 ──────────────────────────────────────


@dataclass
class Content:
    title: str
    url: str
    intent: str
    next_action: str


class CardTips(Enum):
    ECO_PLAN = Content(
        title="[쏠깃한 카드 연구소] 지구와 나를 위한 더 나은 Plan 신한카드 ECO Plan",
        url="https://www.shinhancardblog.com/1424",
        intent="금융생활지식 (카드연구소)",
        next_action="콘텐츠 랜딩 화면 이동",
    )
    SIMPLE_PLAN_PLUS = Content(
        title="[쏠깃한 카드 연구소] 조건 없이 한층 더 강해진 혜택, 신한카드 Simple Plan +",
        url="https://www.shinhancardblog.com/1421",
        intent="금융생활지식 (카드연구소)",
        next_action="콘텐츠 랜딩 화면 이동",
    )
    SIMPLE_PLAN = Content(
        title="[쏠깃한 카드 연구소] 복잡한 건 딱 질색일 땐? 신한카드 Simple Plan",
        url="https://www.shinhancardblog.com/1415",
        intent="금융생활지식 (카드연구소)",
        next_action="콘텐츠 랜딩 화면 이동",
    )
    MILITARY_CARD = Content(
        title="[쏠깃한 카드 연구소] 장병들을 위한 '진짜' 카드! 신한카드 나라사랑카드",
        url="https://www.shinhancardblog.com/1412",
        intent="금융생활지식 (카드연구소)",
        next_action="콘텐츠 랜딩 화면 이동",
    )
    NPAY_BIZ = Content(
        title="[쏠깃한 카드 연구소] 사장님 지갑 쏠쏠해지는 Npay biz 신한카드",
        url="https://www.shinhancardblog.com/1407",
        intent="금융생활지식 (카드연구소)",
        next_action="콘텐츠 랜딩 화면 이동",
    )


class TrendContents(Enum):
    TRAVEL_2026 = Content(
        title="데이터로 살펴본 2026 여행 트렌드",
        url="https://www.shinhancardblog.com/1432",
        intent="금융생활지식 (트렌드)",
        next_action="콘텐츠 랜딩 화면 이동",
    )
    WELLNESS_2026 = Content(
        title="데이터로 살펴본 2026년 웰니스 트렌드",
        url="https://www.shinhancardblog.com/1425",
        intent="금융생활지식 (트렌드)",
        next_action="콘텐츠 랜딩 화면 이동",
    )
    DINING_TREND = Content(
        title="데이터로 살펴본 외식 트렌드 : 경험 콘텐츠가 된 파인 다이닝",
        url="https://www.shinhancardblog.com/1417",
        intent="금융생활지식 (트렌드)",
        next_action="콘텐츠 랜딩 화면 이동",
    )
    WISE_UP_2026 = Content(
        title="2026년 주목할 만한 소비 트렌드 'WISE UP'",
        url="https://www.shinhancardblog.com/1410",
        intent="금융생활지식 (트렌드)",
        next_action="콘텐츠 랜딩 화면 이동",
    )
    EXPERIENCE_CONSUMPTION = Content(
        title="경험소비가 늘어나는 이유, 사람들은 왜 물건보다 경험에 돈을 쓸까요?",
        url="https://shinhangroup.com/kr/archive/insight/extend/detail/33245",
        intent="금융생활지식 (트렌드)",
        next_action="콘텐츠 랜딩 화면 이동",
    )


class FinanceContents(Enum):
    LUNCHFLATION = Content(
        title="직장인이 점심값에 민감해진 이유 : 런치플레이션 시대의 생존법",
        url="https://shinhangroup.com/kr/archive/insight/extend/detail/33233",
        intent="금융생활지식 (금융)",
        next_action="콘텐츠 랜딩 화면 이동",
    )
    RETIREMENT_COST = Content(
        title="노후 생활비 계산, 은퇴 후 실제 필요한 생활비는 어떻게 계산할까요?",
        url="https://shinhangroup.com/kr/archive/insight/extend/detail/33235",
        intent="금융생활지식 (금융)",
        next_action="콘텐츠 랜딩 화면 이동",
    )
    SUPER_SOL = Content(
        title="새로워진 신한 슈퍼 SOL ! 가입하고 런칭 이벤트 혜택 받는 방법",
        url="https://www.shinhancardblog.com/1434",
        intent="금융생활지식 (금융)",
        next_action="콘텐츠 랜딩 화면 이동",
    )
