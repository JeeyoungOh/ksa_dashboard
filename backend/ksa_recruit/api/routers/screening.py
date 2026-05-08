"""
/screening 라우터.
"""
from __future__ import annotations
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from ..deps import SessionDep
from ..schemas.candidate import ScreeningRunResponse, ScreeningRecommendationOut
from ...repositories.candidate import CandidateRepository
from ...services.screening import (
    ScreeningService, CandidateNotFound, JobPostingNotFound, NoApplicableRuleSet,
)


router = APIRouter(prefix="/screening", tags=["screening"])


@router.post(
    "/{candidate_id}/run",
    response_model=ScreeningRunResponse,
    summary="결격 자동판정 실행 (룰 엔진 호출 + 결과 저장)",
)
def run_screening(candidate_id: UUID, session: SessionDep) -> ScreeningRunResponse:
    service = ScreeningService(session)
    try:
        rec = service.run(candidate_id)
    except CandidateNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"candidate {candidate_id} not found")
    except JobPostingNotFound as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e))
    except NoApplicableRuleSet as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    session.commit()
    session.refresh(rec)

    candidate = CandidateRepository(session).get(candidate_id)
    return ScreeningRunResponse(
        candidate_id=candidate_id,
        candidate_status=candidate.status,
        recommendation=ScreeningRecommendationOut.model_validate(rec),
    )
