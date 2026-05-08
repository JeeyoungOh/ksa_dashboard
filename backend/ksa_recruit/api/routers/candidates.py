"""
/candidates 라우터.
"""
from __future__ import annotations
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from ..deps import SessionDep
from ..schemas.candidate import (
    CandidateCreate, CandidateOut,
    CandidateProfileOut, CandidateNarrativeOut, ScreeningRecommendationOut,
)
from ...repositories.candidate import CandidateRepository
from ...repositories.rule_set import ScreeningRepository
from ...services.candidate import CandidateService, CandidateAlreadyExists


router = APIRouter(prefix="/candidates", tags=["candidates"])


@router.post(
    "",
    response_model=CandidateOut,
    status_code=status.HTTP_201_CREATED,
    summary="후보자 등록",
)
def create_candidate(payload: CandidateCreate, session: SessionDep) -> CandidateOut:
    service = CandidateService(session)
    try:
        candidate = service.register(**payload.model_dump())
    except CandidateAlreadyExists as e:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(e))

    session.commit()
    session.refresh(candidate)

    return _to_out(candidate, screening=None)


@router.get(
    "/{candidate_id}",
    response_model=CandidateOut,
    summary="후보자 조회 (프로필+자유서술+자동판정 결과)",
)
def get_candidate(candidate_id: UUID, session: SessionDep) -> CandidateOut:
    candidate = CandidateRepository(session).get(candidate_id)
    if candidate is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"candidate {candidate_id} not found")

    screening = ScreeningRepository(session).get_by_candidate(candidate_id)
    return _to_out(candidate, screening)


# ---------------------------------------------------------------------------

def _to_out(candidate, screening) -> CandidateOut:
    return CandidateOut(
        id=candidate.id,
        cycle_id=candidate.cycle_id,
        posting_id=candidate.posting_id,
        candidate_no=candidate.candidate_no,
        status=candidate.status,
        created_at=candidate.created_at,
        updated_at=candidate.updated_at,
        profile=CandidateProfileOut.model_validate(candidate.profile) if candidate.profile else None,
        narrative=CandidateNarrativeOut.model_validate(candidate.narrative) if candidate.narrative else None,
        screening=ScreeningRecommendationOut.model_validate(screening) if screening else None,
    )
