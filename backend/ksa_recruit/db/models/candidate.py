"""
ORM 모델 — 후보자.

실제 DB 스키마에 정합:
- candidates: id, cycle_id, posting_id, source_row_id, candidate_no, status, created_at, updated_at
- candidate_profiles: id (PK), candidate_id (UNIQUE), ...
- candidate_narratives: id (PK), candidate_id (UNIQUE), ...
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
    cycle_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("recruitment_cycles.id"), nullable=False,
    )
    posting_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("job_postings.id"), nullable=False,
    )
    source_row_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    candidate_no: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(candidate_status_enum, default="IMPORTED", nullable=False)
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

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"),
        unique=True, nullable=False,
    )
    job_code: Mapped[str | None] = mapped_column(String(50))
    career_years: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    education_level: Mapped[str | None] = mapped_column(String(50))
    education: Mapped[list | None] = mapped_column(JSONB)
    certifications: Mapped[list | None] = mapped_column(JSONB)
    language_tests: Mapped[list | None] = mapped_column(JSONB)
    submitted_documents: Mapped[list | None] = mapped_column(JSONB)
    eligibility_answers: Mapped[dict | None] = mapped_column(JSONB)
    legal_disqualification_answer: Mapped[bool | None] = mapped_column(Boolean)
    self_declaration_submitted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    attachment_checklist: Mapped[dict | None] = mapped_column(JSONB)
    normalized_profile: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    candidate: Mapped[Candidate] = relationship(back_populates="profile")


class CandidateNarrative(Base):
    __tablename__ = "candidate_narratives"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"),
        unique=True, nullable=False,
    )
    cover_letter: Mapped[str | None] = mapped_column(Text)
    career_history: Mapped[str | None] = mapped_column(Text)
    additional_essays: Mapped[dict | None] = mapped_column(JSONB)
    cover_letter_masked: Mapped[str | None] = mapped_column(Text)
    career_history_masked: Mapped[str | None] = mapped_column(Text)
    masking_version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    candidate: Mapped[Candidate] = relationship(back_populates="narrative")
