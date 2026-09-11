"""LOCAL STUB — 필요 시 사내 헬스체크 규격(의존 서비스 점검 등)으로 교체.

run.sh 가 안내하는 ``/health`` 엔드포인트만 제공하는 최소 구현이다.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
