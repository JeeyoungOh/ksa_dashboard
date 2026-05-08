"""
Pydantic 도메인 모델.

DB 테이블의 컬럼 구조를 그대로 반영하되, 서비스 로직에서 사용할 수 있도록 정제.
나중에 SQLAlchemy ORM 모델 → 이 도메인 모델로 변환하는 매퍼를 ❸ 단계에서 추가.
"""
from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from .enums import (
    EducationLevel, DecisionValue, RuleScope, RuleGroupCode,
    BonusStatus, BlindCategory, DetectorLayer,
)


# =========================================================================
# 후보자 (Candidate)
# =========================================================================
class CandidateProfile(BaseModel):
    """결격 평가 + 가점 계산에 필요한 정형 프로필 (PII 제외)."""
    model_config = ConfigDict(extra="forbid")

    candidate_id: UUID
    candidate_no: str
    job_code: str

    # D1 평가용
    education_level: EducationLevel
    career_years: Decimal = Decimal(0)
    education: list[dict] = Field(default_factory=list)

    # D2 평가용
    submitted_documents: list[str] = Field(default_factory=list)
    attachment_checklist: dict = Field(default_factory=dict)

    # D3 평가용
    legal_disqualification_answer: bool = False
    self_declaration_submitted: bool = True

    # 가점 계산용
    certifications: list[str] = Field(default_factory=list)
    language_tests: list[dict] = Field(default_factory=list)
    normalized_profile: dict = Field(default_factory=dict)


class CandidateNarrative(BaseModel):
    """블라인드 탐지·LLM 입력에 사용될 자유서술."""
    model_config = ConfigDict(extra="forbid")

    candidate_id: UUID
    cover_letter: Optional[str] = None
    career_history: Optional[str] = None


# =========================================================================
# 룰 메타 (RuleSet → RuleGroup → RuleItem)
# =========================================================================
class RuleItem(BaseModel):
    """단일 룰. 룰 그룹(D1/D2/D3) 내 하나의 평가 단위."""
    model_config = ConfigDict(extra="forbid")

    id: UUID
    code: str                    # 예: D1_EDU_MIN, D2_MISSING_DOC
    name: str
    operator: str                # 예: in, eq, neq, ge, le, between, is_true
    field_path: str              # 예: education_level, attachment_checklist.missing_required
    expected_value: Any          # JSONB로 직렬화 가능한 값
    severity: str = "ERROR"      # ERROR | WARN
    is_active: bool = True


class RuleGroup(BaseModel):
    """결격 사유 그룹 (D1/D2/D3). OR 결합 - 그룹 내 룰 1개 이상 트리거되면 그룹 트리거."""
    model_config = ConfigDict(extra="forbid")

    id: UUID
    code: RuleGroupCode
    name: str
    items: list[RuleItem] = Field(default_factory=list)


class RuleSet(BaseModel):
    """룰셋 (JOB or GLOBAL). 우선순위: JOB > GLOBAL."""
    model_config = ConfigDict(extra="forbid")

    id: UUID
    code: str
    name: str
    scope: RuleScope
    version: int
    groups: list[RuleGroup] = Field(default_factory=list)


# =========================================================================
# 가점 룰 (BonusRuleSet → BonusRule)
# =========================================================================
class BonusRule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    code: str                       # BONUS_PHD, BONUS_CERT_A 등
    name: str
    score_value: Decimal
    score_unit: str = "POINT"       # POINT | PERCENT
    operator: str                   # 매칭 연산자
    field_path: str                 # 평가할 후보자 필드
    expected_value: Any
    exclusive_group: Optional[str] = None   # 같은 그룹 내 최고점만 적용 (EDUCATION 등)
    evidence_type: str = "DOCUMENT"
    is_active: bool = True


class BonusRuleSet(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    code: str
    name: str
    version: int
    max_bonus_score: Decimal = Decimal("10")
    rules: list[BonusRule] = Field(default_factory=list)


# =========================================================================
# 평가 결과 (DB INSERT 페이로드와 매칭)
# =========================================================================
class TriggeredRule(BaseModel):
    """그룹 내 트리거된 룰의 evidence 항목."""
    rule_code: str
    rule_name: str
    field_path: str
    actual_value: Any
    expected_value: Any
    operator: str


class GroupResult(BaseModel):
    """D1/D2/D3 각 그룹의 평가 결과."""
    code: RuleGroupCode
    triggered: bool
    triggered_rules: list[TriggeredRule] = Field(default_factory=list)


class ScreeningResult(BaseModel):
    """결격 자동판정 최종 결과."""
    candidate_id: UUID
    d1_triggered: bool
    d2_triggered: bool
    d3_triggered: bool
    recommended_decision: DecisionValue
    rule_evidence: dict          # screening_recommendations.rule_evidence와 매칭
    input_snapshot: dict
    applied_rule_sets: list[dict]   # JSON 배열 - rule_set_id, version, scope 기록
    evaluator_version: str = "py_engine_v1"


class BonusItemResult(BaseModel):
    bonus_rule_id: UUID
    bonus_rule_code: str
    bonus_rule_name: str
    exclusive_group: Optional[str]
    calculated_score: Decimal
    applied_score: Decimal
    status: BonusStatus
    rejection_reason: Optional[str] = None
    matched_evidence: dict = Field(default_factory=dict)


class BonusResult(BaseModel):
    candidate_id: UUID
    bonus_rule_set_id: UUID
    bonus_rule_set_version: int
    items: list[BonusItemResult]
    total_doc_bonus: Decimal     # 서류 단계 가점 합계 (면접 가점 별개)
    max_bonus_score: Decimal


# =========================================================================
# 블라인드 / PII 결과
# =========================================================================
class BlindDetection(BaseModel):
    candidate_id: UUID
    field_name: str              # cover_letter | career_history
    category: BlindCategory
    matched_text: str
    span_start: int
    span_end: int
    detector_layer: DetectorLayer = DetectorLayer.RULE_DICT
    confidence: Decimal = Decimal("1.0")


class BlindDetectionResult(BaseModel):
    candidate_id: UUID
    detections: list[BlindDetection]
    detection_count: int
    detection_summary: dict      # {"total": N, "by_category": {...}}
    cover_letter_masked: Optional[str] = None
    career_history_masked: Optional[str] = None


class PIIDetection(BaseModel):
    pii_type: str                # PERSON_NAME, PHONE, EMAIL, ADDR ...
    text: str
    span_start: int
    span_end: int


class PIIScrubResult(BaseModel):
    input_original: str
    input_scrubbed: str
    detected_pii: list[PIIDetection]
    layer_results: dict          # {"layer1_dict": N, "layer2_ner": 0, "layer3_heuristic": 0}
    passed: bool                 # 스크럽 후 잔여 PII 없으면 True
