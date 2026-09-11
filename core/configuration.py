"""LOCAL STUB — 실제 사내 설정 로더로 교체 필요.

로컬 실행만 되면 되므로 앱 이름만 담은 최소 구현.
"""

from __future__ import annotations

from types import SimpleNamespace


def get_conf() -> SimpleNamespace:
    return SimpleNamespace(name="shinhan-credit-card-guide")
