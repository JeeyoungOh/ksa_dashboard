"""
FastAPI 요청/응답 스키마.

도메인 모델과 분리해 둠. 도메인 모델은 엔진 내부, 이 스키마는 외부 인터페이스.
"""
from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# =========================================================================
# 후보자 등록 (POST /candidates)
# =========================================================================
class CandidateCreate(BaseModel):
    cycle_id: UUID
    posting_id: UUID
    candidate_no: str = Field(..., max_length=50)
    job_code: str = Field(..., max_length=50)

    education_level: str = Field(..., description="HIGH_SCHOOL/ASSOCIATE/BACHELOR/MASTER/DOCTORATE")
    career_years: Decimal = Field(default=Decimal("0"), ge=0)
    education: list = Field(default_factory=list)
    certifications: list = Field(default_factory=list)
    language_tests: list = Field(default_factory=list)
    submitted_documents: list = Field(default_factory=list)

    legal_disqualification_answer: bool = False
    self_declaration_submitted: bool = True
    attachment_checklist: dict = Field(default_factory=dict)
    normalized_profile: dict = Field(default_factory=dict)

    cover_letter: Optional[str] = None
    career_history: Optional[str] = None


class CandidateProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_code: str
    education_level: str
    career_years: Decimal
    certifications: list = Field(default_factory=list)
    submitted_documents: list = Field(default_factory=list)
    legal_disqualification_answer: bool
    self_declaration_submitted: bool
    attachment_checklist: dict


class CandidateNarrativeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cover_letter: Optional[str] = None
    career_history: Optional[str] = None
    cover_letter_masked: Optional[str] = None
    career_history_masked: Optional[str] = None


class ScreeningRecommendationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    candidate_id: UUID
    d1_triggered: bool
    d2_triggered: bool
    d3_triggered: bool
    recommended_decision: str
    rule_evidence: dict
    input_snapshot: dict
    applied_rule_sets: list
    evaluator_version: str
    evaluated_at: datetime


class CandidateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    cycle_id: UUID
    posting_id: UUID
    candidate_no: str
    status: str
    created_at: datetime
    updated_at: datetime
    profile: Optional[CandidateProfileOut] = None
    narrative: Optional[CandidateNarrativeOut] = None
    screening: Optional[ScreeningRecommendationOut] = None


# =========================================================================
# 결격 자동판정 (POST /screening/{candidate_id}/run)
# =========================================================================
class ScreeningRunResponse(BaseModel):
    candidate_id: UUID
    candidate_status: str
    recommendation: ScreeningRecommendationOut


# =========================================================================
# 에러 응답
# =========================================================================
class ErrorResponse(BaseModel):
    detail: str
