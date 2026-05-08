"""
BonusEngine 단위 테스트.

검증 목표: 시뮬레이션 SQL의 가점 계산 결과와 일치.
"""
from __future__ import annotations
from decimal import Decimal

import pytest

from ksa_recruit.domain.enums import BonusStatus
from ksa_recruit.engines.bonus import BonusEngine


def _by_code(items, code):
    """결과 항목 중 특정 코드 1개 반환."""
    matches = [i for i in items if i.bonus_rule_code == code]
    assert len(matches) == 1, f"{code} 매칭 항목 없음 또는 중복: {len(matches)}"
    return matches[0]


def test_c001_kim_mugyeol_basic_bonus(candidates, bonus_rule_set):
    """C001: 석사 + A자격증 + 어학 = 8점 (상한 미만, 모두 승인)."""
    engine = BonusEngine()
    result = engine.calculate(candidates["C001"], bonus_rule_set)

    assert result.total_doc_bonus == Decimal("8")

    master = _by_code(result.items, "BONUS_MASTER")
    assert master.status == BonusStatus.APPROVED
    assert master.applied_score == Decimal("3")

    cert_a = _by_code(result.items, "BONUS_CERT_A")
    assert cert_a.status == BonusStatus.APPROVED
    assert cert_a.applied_score == Decimal("3")

    lang = _by_code(result.items, "BONUS_LANG_HIGH")
    assert lang.status == BonusStatus.APPROVED
    assert lang.applied_score == Decimal("2")


def test_c008_im_gajeom_max_cap_applied(candidates, bonus_rule_set):
    """
    C008: 박사5 + A자격3 + B자격1 + 어학2 = 11점 → 상한 10점 적용.
    exclusive_group=EDUCATION 룰은 박사만 매칭 (석사 룰은 매칭 안됨).
    상한 도달 시 점수 낮은 항목부터 REJECTED 또는 부분 감액.
    """
    engine = BonusEngine()
    result = engine.calculate(candidates["C008"], bonus_rule_set)

    # 총 적용 점수는 정확히 10
    assert result.total_doc_bonus == Decimal("10")

    # 박사 5점 - 승인
    phd = _by_code(result.items, "BONUS_PHD")
    assert phd.status == BonusStatus.APPROVED
    assert phd.applied_score == Decimal("5")

    # A자격증 3점 - 승인
    cert_a = _by_code(result.items, "BONUS_CERT_A")
    assert cert_a.status == BonusStatus.APPROVED
    assert cert_a.applied_score == Decimal("3")

    # 어학 2점 - 승인
    lang = _by_code(result.items, "BONUS_LANG_HIGH")
    assert lang.status == BonusStatus.APPROVED
    assert lang.applied_score == Decimal("2")

    # B자격증 1점 - 상한 도달로 REJECTED (점수가 가장 낮아서 마지막)
    cert_b = _by_code(result.items, "BONUS_CERT_B")
    assert cert_b.status == BonusStatus.REJECTED
    assert cert_b.applied_score == Decimal("0")


def test_c008_education_exclusive_group_only_phd_matches(candidates, bonus_rule_set):
    """C008은 박사이므로 석사 룰은 매칭조차 안돼야 함 (rejection이 아니라 미매칭)."""
    engine = BonusEngine()
    result = engine.calculate(candidates["C008"], bonus_rule_set)

    master_matches = [i for i in result.items if i.bonus_rule_code == "BONUS_MASTER"]
    assert master_matches == []  # 매칭조차 되지 않음


def test_c010_no_yugongja_patriot_caps_at_10(candidates, bonus_rule_set):
    """
    C010: 국가유공자 10점 = 상한 즉시 도달.
    매칭은 됐지만 학력·자격증은 모두 REJECTED 처리되어야 함.
    """
    engine = BonusEngine()
    result = engine.calculate(candidates["C010"], bonus_rule_set)

    assert result.total_doc_bonus == Decimal("10")

    patriot = _by_code(result.items, "BONUS_PATRIOT_10")
    assert patriot.status == BonusStatus.APPROVED
    assert patriot.applied_score == Decimal("10")

    master = _by_code(result.items, "BONUS_MASTER")
    assert master.status == BonusStatus.REJECTED
    assert master.applied_score == Decimal("0")

    cert_a = _by_code(result.items, "BONUS_CERT_A")
    assert cert_a.status == BonusStatus.REJECTED
    assert cert_a.applied_score == Decimal("0")


def test_no_matching_rules_returns_zero(candidates, bonus_rule_set):
    """C002 (학력 미달): 박사·석사 룰 매칭 안됨, 자격·어학·유공자도 없음 → 0점."""
    engine = BonusEngine()
    result = engine.calculate(candidates["C002"], bonus_rule_set)

    assert result.total_doc_bonus == Decimal("0")
    assert result.items == []


def test_partial_cap_when_exact_overflow():
    """
    경계값 테스트: 누적 9점 + 다음 항목 5점 = 14점이지만 상한 10점이면
    다음 항목은 1점만 부분 적용되어야 함.
    """
    from uuid import uuid4
    from ksa_recruit.domain.models import (
        BonusRule, BonusRuleSet, CandidateProfile,
    )
    from ksa_recruit.domain.enums import EducationLevel

    rule_set = BonusRuleSet(
        id=uuid4(), code="TEST", name="Test", version=1,
        max_bonus_score=Decimal("10"),
        rules=[
            BonusRule(
                id=uuid4(), code="A", name="A 9점",
                score_value=Decimal("9"), operator="is_true",
                field_path="normalized_profile.flag_a", expected_value=True,
            ),
            BonusRule(
                id=uuid4(), code="B", name="B 5점",
                score_value=Decimal("5"), operator="is_true",
                field_path="normalized_profile.flag_b", expected_value=True,
            ),
        ],
    )

    profile = CandidateProfile(
        candidate_id=uuid4(),
        candidate_no="TEST",
        job_code="X",
        education_level=EducationLevel.MASTER,
        career_years=Decimal(0),
        normalized_profile={"flag_a": True, "flag_b": True},
    )

    engine = BonusEngine()
    result = engine.calculate(profile, rule_set)

    assert result.total_doc_bonus == Decimal("10")

    a = _by_code(result.items, "A")
    b = _by_code(result.items, "B")

    # A가 더 높으므로 먼저 9점 적용, B는 1점만 부분 적용
    assert a.status == BonusStatus.APPROVED
    assert a.applied_score == Decimal("9")
    assert b.status == BonusStatus.APPROVED
    assert b.applied_score == Decimal("1")
    assert b.rejection_reason is not None  # 감액 사유 기록
