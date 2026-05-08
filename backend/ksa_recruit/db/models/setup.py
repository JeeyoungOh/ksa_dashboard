"""
ORM 모델 — 룰셋 + 사이클 + 공고 + 사용자.

설계 원칙:
  - 모든 PK는 UUID
  - JSONB는 dict로 노출
  - 양방향 relationship은 필요 시점에만 추가 (성능·복잡도 균형)
"""
from __future__ import annotations
import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import (
    String, Integer, Numeric, DateTime, Date, Boolean, Text, ForeignKey,
    UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..session import Base
from ._enums import (
    rule_scope_enum, user_role_enum,
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(user_role_enum, nullable=False)
    department: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RuleSet(Base):
    __tablename__ = "rule_sets"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    scope: Mapped[str] = mapped_column(rule_scope_enum, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    effective_from: Mapped[date | None] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date)
    created_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    groups: Mapped[list[RuleGroup]] = relationship(
        back_populates="rule_set", cascade="all, delete-orphan", lazy="selectin",
    )

    __table_args__ = (UniqueConstraint("code", "version", name="uq_rule_sets_code_version"),)


class RuleGroup(Base):
    __tablename__ = "rule_groups"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_set_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("rule_sets.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    rule_set: Mapped[RuleSet] = relationship(back_populates="groups")
    items: Mapped[list[RuleItem]] = relationship(
        back_populates="group", cascade="all, delete-orphan", lazy="selectin",
    )


class RuleItem(Base):
    __tablename__ = "rule_items"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_group_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("rule_groups.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    operator: Mapped[str] = mapped_column(String(20), nullable=False)
    field_path: Mapped[str] = mapped_column(String(255), nullable=False)
    expected_value: Mapped[dict | list | str | int | float | bool | None] = mapped_column(JSONB)
    severity: Mapped[str] = mapped_column(String(20), default="ERROR")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    group: Mapped[RuleGroup] = relationship(back_populates="items")


class RecruitmentCycle(Base):
    __tablename__ = "recruitment_cycles"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cycle_type: Mapped[str] = mapped_column(String(20), nullable=False)
    cycle_year: Mapped[int] = mapped_column(Integer, nullable=False)
    cycle_seq: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="PLANNED", nullable=False)


class JobPosting(Base):
    __tablename__ = "job_postings"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cycle_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("recruitment_cycles.id"), nullable=False)
    rule_set_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("rule_sets.id"))
    interview_template_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    bonus_rule_set_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    job_code: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    department: Mapped[str | None] = mapped_column(String(100))
    headcount: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    open_date: Mapped[date] = mapped_column(Date, nullable=False)
    close_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="DRAFT", nullable=False)
