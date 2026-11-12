"""홈페이지 이벤트 분류. 숫자는 홈페이지 코드이며 MCI 규격은 아니다."""
EVENT_TYPE_CODES = {"쇼핑문화": 51, "앱테크": 52, "여행숙박": 53, "카드결제": 54, "청소년": 55}
EVENT_TYPE_NAMES = list(EVENT_TYPE_CODES)
EVENT_TYPE_DESCRIPTION = (
    "Optional homepage category: 쇼핑문화, 앱테크, 여행숙박, 카드결제, 청소년. "
    "청소년 covers school payments and private kindergarten automatic payments. "
    "Omit for all events. If brand is supplied, this filter is ignored. "
    "Do not infer 카드결제 just because the user mentions a card."
)
