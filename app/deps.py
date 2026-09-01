"""공유 의존성(서비스) 조립. Spring 의 DI 컨테이너에 해당한다.

프로세스당 한 번만 만들어지고, 모든 툴 모듈이 여기서 가져다 쓴다.
(``CreditCardDataRepository`` 는 생성 시 ``data.json`` 을 1회 로드한다.)
"""

from __future__ import annotations

from app.services.card_guide_service import CreditCardGuideService
from app.services.card_repository import CreditCardDataRepository
from app.services.financial_knowledge_service import FinancialKnowledgeService
from app.services.popular_card_service import PopularCreditCardService

repository = CreditCardDataRepository()
guide_service = CreditCardGuideService(repository)
popular_service = PopularCreditCardService(repository)
financial_service = FinancialKnowledgeService()
