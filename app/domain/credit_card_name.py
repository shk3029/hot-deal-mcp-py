"""지원하는 신한카드 상품명(정확 매칭). Java ``CreditCardName`` enum 의 파이썬 포팅.

Java 는 enum 이지만 파이썬에서는 순서가 있는 표시명 리스트로 관리한다. MCP 스키마의
``enum`` 값과 파라미터 설명이 이 리스트 하나만 바라보도록 한다(single source of truth).
"""

from __future__ import annotations

_PARAMETER_DESCRIPTION_PREFIX = (
    "Exact Shinhan Card(신한카드) product name. Choose the closest matching value from: "
)

# Java CreditCardName enum 선언 순서 그대로.
CREDIT_CARD_NAMES: list[str] = [
    "신한카드 SOL트래블 체크",
    "신한 슈퍼SOL 체크",
    "신한카드 Hey Young 체크",
    "신한카드 Point Plan 체크",
    "신한카드 SOL글로벌 체크",
    "신한카드 On 체크",
    "신한카드 Way 체크",
    "신한카드 Pick E 체크",
    "신한카드 하이패스(전용) 체크",
    "신한카드 경차사랑 Life",
    "신한카드 Pick I 체크",
    "신한카드 플리(체크)",
    "전통시장사랑 체크 신한카드",
    "신한카드 SOL트래블J 체크",
    "신한카드 처음 체크",
    "신한카드 SOL트립앤샵 체크",
    "신한카드 처음",
    "SOL 메이트 신한카드 SOL Plan 체크",
    "신한카드 나라사랑카드 체크",
    "신한카드 나라사랑카드 체크(배틀그라운드 에디션)",
    "신한카드 EVerywhere",
    "신한카드 처음 (ANNIVERSE)",
    "신한카드 Edu Plan+",
    "신한카드 국민행복",
    "신한카드 주거래 체크",
    "국민내일배움 신한카드 Simple",
    "11번가 신한카드",
    "K-패스 신한카드",
    "신한 후불 기후동행 신용카드",
    "신한카드 Deep Oil",
    "신한카드 B.Big(삑)",
    "신세계 신한카드",
    "배민 신한카드 밥친구",
    "신한카드 Deep Store",
    "신한카드 Eats More(이츠모아)",
    "티머니 Pay & GO 신한카드",
    "GS ALL 신한카드",
    "넥센타이어 신한카드",
    "E9pay 신한카드 처음",
    "신한카드 플리",
    "신한카드 Discount Plan",
    "신한카드 Mr.Life",
    "KT 가족만족 DC 신한카드",
    "신한카드 Simple Plan",
    "CU Npay 카드",
    "알리익스프레스 신한카드",
    "신한카드 알뜰More(알뜰모아)",
    "수소차 충전할인 신한카드",
    "신한카드 Edu",
    "신한카드 Shopping",
    "신한카드 Point Plan(산리오캐릭터즈)",
    "신한카드 ECO Plan",
    "신한카드 Point Plan",
    "신한카드 Hi-Point Plan",
    "카카오뱅크 착붙 신한카드",
    "LG U+ Bora 신한카드 Big Plus",
    "LG U+ 스마트플랜 Plus 신한카드",
    "LG전자 The 구독케어 신한카드",
    "SKT T라이트 신한카드",
    "LGE.COM 신한카드",
    "Toss One 신한카드",
    "SKT T&Life 신한카드",
    "코웨이 신한카드",
    "SK브로드밴드 신한카드",
    "웅진프리드 신한카드",
    "캐리어 신한카드",
    "신한카드 Haru(Hoshino Resorts)",
    "신한카드 Deep On Platinum+",
    "신한카드 Biz Plan",
    "신한카드 SOL Plan",
    "신한카드 Point Plan+",
    "신한카드 Air Platinum#",
    "신한카드 Air One",
    "신한카드 SOL Plan+",
    "SOL메이트 신한카드 SOL Plan+",
    "신한카드 Discount Plan+",
    "신한카드 Hi-Point Plan+",
    "신한카드 Simple Plan+",
    "신한카드 The CLASSIC-Y",
    "싱가포르항공 크리스플라이어 더 베스트 신한카드",
    "메리어트 본보이™ 더 베스트 신한카드",
]

_CARD_NAME_SET = set(CREDIT_CARD_NAMES)


def parameter_description() -> str:
    return _PARAMETER_DESCRIPTION_PREFIX + ", ".join(CREDIT_CARD_NAMES)


def resolve_card_name(value: str | None) -> str:
    """표시명을 정확 매칭한다. 퍼지 매칭은 하지 않는다.

    Java ``CreditCardName.fromDisplayName`` 과 동일하게, 값이 없거나 지원 목록에
    없으면 ``ValueError`` 를 던진다.
    """
    if value is None or not value.strip():
        raise ValueError("카드 이름을 입력해주세요.")

    trimmed = value.strip()
    if trimmed not in _CARD_NAME_SET:
        raise ValueError(f"지원하지 않는 카드 이름입니다: {value}")
    return trimmed
