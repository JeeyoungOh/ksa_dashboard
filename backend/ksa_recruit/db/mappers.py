"""
ORM 객체 ↔ 도메인 Pydantic 모델 변환.

룰 엔진은 도메인 모델만 다루고 ORM·DB를 모르도록 격리.
이 매퍼는 그 둘을 잇는 유일한 지점.
"""
from __future__ import annotations
from decimal import Decimal

from .. import db
from ..domain.enums import EducationLevel, RuleScope, RuleGroupCode
from ..domain.models import (
    CandidateProfile as DomainProfile,
    CandidateNarrative as DomainNarrative,
    RuleSet as DomainRuleSet,
    RuleGroup as DomainRuleGroup,
    RuleItem as DomainRuleItem,
)


# ---------------------------------------------------------------------------
# Candidate ORM → Domain
# ---------------------------------------------------------------------------
def to_domain_profile(
    candidate: db.models.Candidate,
) -> DomainProfile:
    """ORM Candidate(+ profile)를 도메인 CandidateProfile로 변환."""
    if candidate.profile is None:
        raise ValueError(f"candidate {candidate.id} has no profile")

    p = candidate.profile
    return DomainProfile(
        candidate_id=candidate.id,
        candidate_no=candidate.candidate_no,
        job_code=p.job_code or "",
        education_level=EducationLevel(p.education_level) if p.education_level else EducationLevel.BACHELOR,
        career_years=Decimal(str(p.career_years)) if p.career_years is not None else Decimal("0"),
        education=p.education or [],
        certifications=p.certifications or [],
        language_tests=p.language_tests or [],
        submitted_documents=p.submitted_documents or [],
        legal_disqualification_answer=bool(p.legal_disqualification_answer),
        self_declaration_submitted=p.self_declaration_submitted,
        attachment_checklist=p.attachment_checklist or {},
        normalized_profile=p.normalized_profile or {},
    )


def to_domain_narrative(
    candidate: db.models.Candidate,
) -> DomainNarrative:
    if candidate.narrative is None:
        return DomainNarrative(candidate_id=candidate.id)
    n = candidate.narrative
    return DomainNarrative(
        candidate_id=candidate.id,
        cover_letter=n.cover_letter,
        career_history=n.career_history,
    )


# ---------------------------------------------------------------------------
# RuleSet ORM → Domain
# ---------------------------------------------------------------------------
def to_domain_rule_set(
    rule_set: db.models.RuleSet,
) -> DomainRuleSet:
    """ORM RuleSet(+ groups + items)를 도메인 RuleSet으로 변환."""
    return DomainRuleSet(
        id=rule_set.id,
        code=rule_set.code,
        name=rule_set.name,
        scope=RuleScope(rule_set.scope),
        version=rule_set.version,
        groups=[_to_domain_group(g) for g in rule_set.groups],
    )


def _to_domain_group(group: db.models.RuleGroup) -> DomainRuleGroup:
    # RuleGroupCode ENUM에 없는 코드는 D1로 fallback
    try:
        code = RuleGroupCode(group.code)
    except ValueError:
        code = RuleGroupCode.D1
    return DomainRuleGroup(
        id=group.id,
        code=code,
        name=group.name,
        items=[_to_domain_item(it) for it in group.items],
    )


def _to_domain_item(item: db.models.RuleItem) -> DomainRuleItem:
    """
    DB의 rule_items에는 severity 컬럼이 없고, 대신 failure_decision (PASS/FAIL/HOLD/AUTO_FAIL)이 있음.
    도메인 RuleItem.severity는 ERROR/WARN인데, DB의 failure_decision을 다음과 같이 매핑:
      - PASS  → "INFO"   (실제로는 사용 안 됨)
      - HOLD  → "WARN"   (보완 가능)
      - FAIL / AUTO_FAIL → "ERROR"  (즉시 결격)
    """
    failure = item.failure_decision
    if failure == "HOLD":
        severity = "WARN"
    elif failure in ("FAIL", "AUTO_FAIL"):
        severity = "ERROR"
    else:
        severity = "INFO"

    return DomainRuleItem(
        id=item.id,
        code=item.code,
        name=item.name,
        operator=item.operator,
        field_path=item.field_path,
        expected_value=item.expected_value,
        severity=severity,
        is_active=item.active,
    )
