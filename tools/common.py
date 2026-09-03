"""툴 모듈 공통 헬퍼."""

from __future__ import annotations

from typing import Any, TypeVar

TModel = TypeVar("TModel")


def with_kakao(model: TModel, widget_response: dict[str, Any]) -> TModel:
    """카카오툴즈 위젯 응답(``{"widget", "copy_text"}``)을 결과 모델 최상위에 싣는다."""
    model.widget = widget_response.get("widget")
    model.copy_text = widget_response.get("copy_text", "")
    return model
