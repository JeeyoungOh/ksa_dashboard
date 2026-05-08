"""
ORM 모델 — screening_recommendations.

결격 자동판정 엔진의 출력이 INSERT되는 테이블. 후보자당 1건 (UNIQUE constraint).
"""
from __future__ import annotations
import uuid
from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    String, DateTime, Boolean, Text, ForeignKey, UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..session import Base
from ._enums import decision_value_enum


class ScreeningRecommendation(Base):
    __tablename__ = "screening_recommendations"
    __table_args__ = (UniqueConstraint("candidate_id", name="uq_screening_recommendations_candidate_id"),)

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False,
    )
    applied_rule_sets: Mapped[list] = mapped_column(JSONB, nullable=False)
    d1_triggered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    d2_triggered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    d3_triggered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    recommended_decision: Mapped[str] = mapped_column(decision_value_enum, nullable=False)
    rule_evidence: Mapped[dict] = mapped_column(JSONB, nullable=False)
    input_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    evaluator_version: Mapped[str] = mapped_column(String(50), nullable=False)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
