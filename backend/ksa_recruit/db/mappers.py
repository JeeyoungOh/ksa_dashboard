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
        job_code=p.job_code,
        education_level=EducationLevel(p.education_level),
        career_years=Decimal(str(p.career_years)),
        education=p.education or [],
        certifications=p.certifications or [],
        language_tests=p.language_tests or [],
        submitted_documents=p.submitted_documents or [],
        legal_disqualification_answer=p.legal_disqualification_answer,
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
    # RuleGroupCode ENUM에 없는 코드는 알 수 없는 그룹 → 무시 안전
    try:
        code = RuleGroupCode(group.code)
    except ValueError:
        # 미지의 그룹 코드: D1로 fallback (실 운영에선 로깅 + 경고)
        code = RuleGroupCode.D1
    return DomainRuleGroup(
        id=group.id,
        code=code,
        name=group.name,
        items=[_to_domain_item(it) for it in group.items],
    )


def _to_domain_item(item: db.models.RuleItem) -> DomainRuleItem:
    return DomainRuleItem(
        id=item.id,
        code=item.code,
        name=item.name,
        operator=item.operator,
        field_path=item.field_path,
        expected_value=item.expected_value,
        severity=item.severity,
        is_active=item.is_active,
    )
