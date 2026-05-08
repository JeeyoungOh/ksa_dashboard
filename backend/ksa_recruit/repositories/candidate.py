"""
CandidateRepository.

세션 받아 CRUD만. 비즈니스 로직은 Service에서.
"""
from __future__ import annotations
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..db import models


class CandidateRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, candidate_id: UUID) -> Optional[models.Candidate]:
        """후보자 + profile + narrative 한 번에 로딩."""
        stmt = (
            select(models.Candidate)
            .where(models.Candidate.id == candidate_id)
            .options(
                selectinload(models.Candidate.profile),
                selectinload(models.Candidate.narrative),
            )
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_candidate_no(
        self, cycle_id: UUID, candidate_no: str
    ) -> Optional[models.Candidate]:
        stmt = (
            select(models.Candidate)
            .where(
                models.Candidate.cycle_id == cycle_id,
                models.Candidate.candidate_no == candidate_no,
            )
            .options(
                selectinload(models.Candidate.profile),
                selectinload(models.Candidate.narrative),
            )
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def add(self, candidate: models.Candidate) -> None:
        self.session.add(candidate)

    def list_by_cycle(self, cycle_id: UUID) -> list[models.Candidate]:
        stmt = (
            select(models.Candidate)
            .where(models.Candidate.cycle_id == cycle_id)
            .order_by(models.Candidate.candidate_no)
        )
        return list(self.session.execute(stmt).scalars().all())
