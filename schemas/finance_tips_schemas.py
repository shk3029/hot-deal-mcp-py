from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ContentItem(BaseModel):
    title:       str = ""
    url:         str = ""
    intent:      str = ""
    next_action: str = ""


class ContentResult(BaseModel):
    contents:   list[ContentItem] = []
    totalCount: int = 0
    error:      str | None = None
    # 카카오툴즈 응답. 툴 결과 최상위에 그대로 실려 카카오 쪽에서 바로 렌더된다.
    widget:     dict[str, Any] | None = None
    copy_text:  str = ""
