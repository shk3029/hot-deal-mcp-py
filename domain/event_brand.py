"""이벤트 검색의 브랜드 후보 단일 원본 (첨부 구성안 40 + 59개).

브랜드뿐 아니라 카드 상품·서비스·이벤트 시리즈도 검색 대상으로 포함한다.
실제 API의 브랜드 식별자와의 매핑은 연동 규격 확정 후 별도로 적용한다.
"""

REQUIRED_BRANDS = (
    "SOL페이", "슈퍼SOL", "The Moment", "Lady Propose", "SKT 제휴카드",
    "JCB", "신한EZ", "하이패스", "지방세", "티머니",
    "신세계", "네이버", "쿠팡", "이마트", "GS리테일", "스타필드", "이케아",
    "전자랜드", "LG베스트샵", "에싸소파", "씰리침대", "템퍼", "소노시즌",
    "SKB", "한샘", "통인익스프레스", "교원", "웨딩",
    "CU", "공차", "제주", "트립닷컴", "조선호텔(그랜드 웨스틴)",
    "마이샵", "디스커버", "럭키박스", "LG트윈스", "유튜브프리미엄", "쥬비스", "노란우산",
)

PROVISIONAL_BRANDS = (
    "메가MGC커피", "스타벅스", "맘스터치", "윌리", "한샘", "현대큐밍",
    "비스터 컬렉션", "신라면세점", "싱가포르항공", "UPI(유니온페이)",
    "롯데호텔", "아고다", "파르나스", "하얏트", "한진트래블", "참좋은여행",
    "LG전자", "장수돌침대", "지누스", "한국투자증권", "온누리상품권", "4대보험",
    "SOL트래블", "Hi-Point Plan", "Biz Plan", "국민행복카드", "아름인",
    "SOL LINK 체크카드", "SOL Plan+", "ECO Plan", "Air One", "The CLASSIC Air",
    "The ACE", "Haru", "나라사랑카드", "국방복지카드", "아멕스", "SOL트립앤J",
    "SOL패밀리", "돈키호테", "LF몰", "라쿠텐", "마이셀렉트샵", "몽쥬약국",
    "Hotels.com", "에어비앤비", "시그니엘", "소노호텔", "마리나 베이 샌즈", "풀만",
    "노랑풍선", "킹캐디", "Bic Camera", "Alipay", "샤롯데", "안심대리",
    "티스테이션", "런츠", "칼이파이",
)

# 사진의 한샘은 필수/일단 포함 양쪽에 있어 enum에는 한 번만 제공한다.
BRAND_NAMES = list(dict.fromkeys((*REQUIRED_BRANDS, *PROVISIONAL_BRANDS)))
BRAND_NAME_SET = frozenset(BRAND_NAMES)

BRAND_DESCRIPTION = (
    "Optional exact brand, product, service, or series from enum. Brand takes priority "
    "over event_type across all categories. SOL LINK 체크카드 is 쇼핑문화; "
    "스타벅스 can span 쇼핑문화 and 카드결제. Omit if no supported name is identified; "
    "never substitute an unrelated brand."
)
