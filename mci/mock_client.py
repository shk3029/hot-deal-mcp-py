"""MciClient 드롭인 목업 (feature/mock 전용).

``mci.mci_client.MciClient`` 와 동일한 ``call_with_itf_id(itf_id, data, include_sensitive)``
시그니처를 갖되, 실제 전문 호출 대신 ``mci/mock_data.json`` 기반 응답을 돌려준다.
MCI 백엔드/``mci_interfaces.yaml`` 없이 카카오툴즈에 붙여 테스트하기 위한 것.

이 브랜치(feature/mock)의 툴들은 ``from mci.mock_client import MockMciClient as MciClient``
로 임포트한다. 실제 연동 브랜치(feature/mci-fetch-tools)와의 차이는 이 파일과 그
임포트 한 줄뿐이다.
"""

from __future__ import annotations

from typing import Any

from mci.mock import MockBackend


class MockMciClient:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._backend = MockBackend()

    def call_with_itf_id(
        self,
        itf_id: str,
        data: Any | None = None,
        include_sensitive: bool = False,
    ) -> dict[str, Any]:
        return self._backend.call_with_itf_id(itf_id, data, include_sensitive)
