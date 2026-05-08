"""
ORM 모델 — 룰셋 + 사이클 + 공고 + 사용자.

실제 DB 스키마에 정합된 정의 (DDL 09개 파일 기준).
"""
from __future__ import annotations
import uuid
from datetime import datetime, date
from uuid import UUID

from sqlalchemy import (
    String, Integer, DateTime, Date, Boolean, Text, ForeignKey,
    UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..session import Base
from ._enums import (
    rule_scope_enum, rule_set_status_enum, rule_operator_enum,
    decision_value_enum, cycle_type_enum, cycle_status_enum,
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RuleSet(Base):
    __tablename__ = "rule_sets"
    __table_args__ = (UniqueConstraint("code", "version", name="rule_sets_code_version_key"),)

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    scope: Mapped[str] = mapped_column(rule_scope_enum, nullable=False)
    status: Mapped[str] = mapped_column(rule_set_status_enum, nullable=False, default="DRAFT")
    effective_from: Mapped[date | None] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date)
    created_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    groups: Mapped[list[RuleGroup]] = relationship(
        back_populates="rule_set", cascade="all, delete-orphan", lazy="selectin",
    )

    @property
    def is_active(self) -> bool:
        """status == 'ACTIVE'를 boolean으로 노출 (서비스 호환용)."""
        return self.status == "ACTIVE"


class RuleGroup(Base):
    __tablename__ = "rule_groups"
    __table_args__ = (UniqueConstraint("rule_set_id", "code", name="rule_groups_rule_set_id_code_key"),)

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_set_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("rule_sets.id", ondelete="CASCADE"), nullable=False,
    )
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    operator: Mapped[str] = mapped_column(rule_operator_enum, nullable=False, default="ALL")
    default_decision: Mapped[str] = mapped_column(decision_value_enum, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    rule_set: Mapped[RuleSet] = relationship(back_populates="groups")
    items: Mapped[list[RuleItem]] = relationship(
        back_populates="group", cascade="all, delete-orphan", lazy="selectin",
    )


class RuleItem(Base):
    __tablename__ = "rule_items"
    __table_args__ = (UniqueConstraint("rule_group_id", "code", name="rule_items_rule_group_id_code_key"),)

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_group_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("rule_groups.id", ondelete="CASCADE"), nullable=False,
    )
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    field_path: Mapped[str] = mapped_column(String(200), nullable=False)
    operator: Mapped[str] = mapped_column(String(20), nullable=False)
    expected_value: Mapped[dict | list | str | int | float | bool | None] = mapped_column(JSONB, nullable=False)
    failure_decision: Mapped[str] = mapped_column(decision_value_enum, nullable=False)
    evidence_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    group: Mapped[RuleGroup] = relationship(back_populates="items")

    @property
    def is_active(self) -> bool:
        """active를 is_active로 노출 (도메인 모델 호환용)."""
        return self.active


class RecruitmentCycle(Base):
    __tablename__ = "recruitment_cycles"
    __table_args__ = (
        UniqueConstraint(
            "cycle_type", "cycle_year", "cycle_seq",
            name="recruitment_cycles_cycle_type_cycle_year_cycle_seq_key",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cycle_type: Mapped[str] = mapped_column(cycle_type_enum, nullable=False)
    cycle_year: Mapped[int] = mapped_column(Integer, nullable=False)
    cycle_seq: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(cycle_status_enum, nullable=False, default="DRAFT")
    created_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class JobPosting(Base):
    __tablename__ = "job_postings"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cycle_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("recruitment_cycles.id"), nullable=False,
    )
    rule_set_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("rule_sets.id"))
    interview_template_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    bonus_rule_set_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    job_code: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    department: Mapped[str | None] = mapped_column(String(100))
    headcount: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    open_date: Mapped[date | None] = mapped_column(Date)
    close_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="OPEN")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
