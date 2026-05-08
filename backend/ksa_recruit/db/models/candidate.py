"""
ORM 모델 — 후보자.

PII(candidate_pii)는 면접 합격 후 단계에 사용되므로 이번 MVP API에선 제외.
candidates / candidate_profiles / candidate_narratives 3개만.
"""
from __future__ import annotations
import uuid
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    String, Integer, Numeric, DateTime, Boolean, Text, ForeignKey, func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..session import Base
from ._enums import candidate_status_enum, education_level_enum


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cycle_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("recruitment_cycles.id"), nullable=False)
    posting_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("job_postings.id"), nullable=False)
    candidate_no: Mapped[str] = mapped_column(String(50), nullable=False)
    pseudonym: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(candidate_status_enum, default="IMPORTED", nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    profile: Mapped[CandidateProfile | None] = relationship(
        back_populates="candidate", uselist=False,
        cascade="all, delete-orphan", lazy="joined",
    )
    narrative: Mapped[CandidateNarrative | None] = relationship(
        back_populates="candidate", uselist=False,
        cascade="all, delete-orphan", lazy="joined",
    )


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    candidate_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), primary_key=True,
    )
    job_code: Mapped[str] = mapped_column(String(50), nullable=False)
    education_level: Mapped[str] = mapped_column(education_level_enum, nullable=False)
    career_years: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"))
    education: Mapped[list | None] = mapped_column(JSONB, default=list)
    certifications: Mapped[list | None] = mapped_column(JSONB, default=list)
    language_tests: Mapped[list | None] = mapped_column(JSONB, default=list)
    submitted_documents: Mapped[list | None] = mapped_column(JSONB, default=list)
    legal_disqualification_answer: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    self_declaration_submitted: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    attachment_checklist: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    normalized_profile: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    candidate: Mapped[Candidate] = relationship(back_populates="profile")


class CandidateNarrative(Base):
    __tablename__ = "candidate_narratives"

    candidate_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), primary_key=True,
    )
    cover_letter: Mapped[str | None] = mapped_column(Text)
    career_history: Mapped[str | None] = mapped_column(Text)
    cover_letter_masked: Mapped[str | None] = mapped_column(Text)
    career_history_masked: Mapped[str | None] = mapped_column(Text)
    masking_version: Mapped[int] = mapped_column(Integer, default=0)

    candidate: Mapped[Candidate] = relationship(back_populates="narrative")
