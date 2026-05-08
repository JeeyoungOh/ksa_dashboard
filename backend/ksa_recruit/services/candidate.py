"""
CandidateService — 후보자 등록 비즈니스 로직.
"""
from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from ..db import models
from ..repositories.candidate import CandidateRepository


class CandidateAlreadyExists(ValueError):
    pass


class CandidateService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repo = CandidateRepository(session)

    def register(
        self,
        *,
        cycle_id: UUID,
        posting_id: UUID,
        candidate_no: str,
        job_code: str,
        education_level: str,
        career_years: Decimal,
        education: list | None = None,
        certifications: list | None = None,
        language_tests: list | None = None,
        submitted_documents: list | None = None,
        legal_disqualification_answer: bool = False,
        self_declaration_submitted: bool = True,
        attachment_checklist: dict | None = None,
        normalized_profile: dict | None = None,
        cover_letter: Optional[str] = None,
        career_history: Optional[str] = None,
    ) -> models.Candidate:
        """
        후보자 + 프로필 + 자유서술 등록. 트랜잭션은 호출자(API 라우터)가 commit 책임.
        같은 cycle 안에서 candidate_no 중복이면 예외.
        """
        existing = self.repo.get_by_candidate_no(cycle_id, candidate_no)
        if existing is not None:
            raise CandidateAlreadyExists(
                f"cycle={cycle_id} 안에 candidate_no={candidate_no} 이미 존재"
            )

        candidate = models.Candidate(
            cycle_id=cycle_id,
            posting_id=posting_id,
            candidate_no=candidate_no,
            status="NORMALIZED",
            submitted_at=datetime.utcnow(),
        )
        candidate.profile = models.CandidateProfile(
            job_code=job_code,
            education_level=education_level,
            career_years=career_years,
            education=education or [],
            certifications=certifications or [],
            language_tests=language_tests or [],
            submitted_documents=submitted_documents or [],
            legal_disqualification_answer=legal_disqualification_answer,
            self_declaration_submitted=self_declaration_submitted,
            attachment_checklist=attachment_checklist or {
                "missing_required": False, "expired": False, "unreadable": False,
            },
            normalized_profile=normalized_profile or {},
        )
        candidate.narrative = models.CandidateNarrative(
            cover_letter=cover_letter,
            career_history=career_history,
        )

        self.repo.add(candidate)
        self.session.flush()    # candidate.id 채워지도록
        return candidate
