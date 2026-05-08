"""
RuleSet · JobPosting · ScreeningRecommendation Repository.
"""
from __future__ import annotations
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..db import models


class RuleSetRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, rule_set_id: UUID) -> Optional[models.RuleSet]:
        stmt = (
            select(models.RuleSet)
            .where(models.RuleSet.id == rule_set_id)
            .options(
                selectinload(models.RuleSet.groups)
                .selectinload(models.RuleGroup.items)
            )
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def get_active_by_scope(self, scope: str) -> list[models.RuleSet]:
        """특정 스코프의 활성 룰셋만."""
        stmt = (
            select(models.RuleSet)
            .where(models.RuleSet.scope == scope, models.RuleSet.is_active.is_(True))
            .options(
                selectinload(models.RuleSet.groups)
                .selectinload(models.RuleGroup.items)
            )
        )
        return list(self.session.execute(stmt).scalars().all())


class JobPostingRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, posting_id: UUID) -> Optional[models.JobPosting]:
        return self.session.get(models.JobPosting, posting_id)


class ScreeningRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_candidate(
        self, candidate_id: UUID
    ) -> Optional[models.ScreeningRecommendation]:
        stmt = select(models.ScreeningRecommendation).where(
            models.ScreeningRecommendation.candidate_id == candidate_id
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def add(self, rec: models.ScreeningRecommendation) -> None:
        self.session.add(rec)

    def upsert(self, rec: models.ScreeningRecommendation) -> models.ScreeningRecommendation:
        """동일 candidate_id에 이미 있으면 갱신, 없으면 INSERT.

        DB UNIQUE 제약 (candidate_id) 가정.
        """
        existing = self.get_by_candidate(rec.candidate_id)
        if existing is None:
            self.session.add(rec)
            return rec
        # 기존 갱신
        existing.applied_rule_sets = rec.applied_rule_sets
        existing.d1_triggered = rec.d1_triggered
        existing.d2_triggered = rec.d2_triggered
        existing.d3_triggered = rec.d3_triggered
        existing.recommended_decision = rec.recommended_decision
        existing.rule_evidence = rec.rule_evidence
        existing.input_snapshot = rec.input_snapshot
        existing.evaluator_version = rec.evaluator_version
        return existing
