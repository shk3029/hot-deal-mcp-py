"""LOCAL STUB — 실제 사내 환경 판별 로직으로 교체 필요.

``api/app.py``가 ``env`` 변수를 만들기만 하고 쓰지는 않아, 로컬 실행만
되면 되므로 값 없이 통과시키는 최소 구현.
"""

from __future__ import annotations

from types import SimpleNamespace


def get_env() -> SimpleNamespace:
    return SimpleNamespace()
