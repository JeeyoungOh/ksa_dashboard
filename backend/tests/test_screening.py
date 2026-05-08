"""
ScreeningEngine 단위 테스트.

검증 목표: 시뮬레이션 SQL과 동일한 D1/D2/D3 trigger와 추천값이 나오는지.
"""
from __future__ import annotations
import pytest

from ksa_recruit.domain.enums import DecisionValue
from ksa_recruit.engines.screening import ScreeningEngine


# 시뮬레이션 SQL 결과와 동일한 기댓값
EXPECTED = {
    # candidate_no: (d1, d2, d3, recommendation)
    "C001": (False, False, False, DecisionValue.PASS_),
    "C002": (True,  False, False, DecisionValue.HOLD),
    "C003": (False, True,  False, DecisionValue.HOLD),
    "C004": (False, False, True,  DecisionValue.HOLD),
    "C005": (True,  True,  True,  DecisionValue.FAIL),
    "C006": (True,  True,  False, DecisionValue.HOLD),
    "C007": (False, False, False, DecisionValue.PASS_),
    "C008": (False, False, False, DecisionValue.PASS_),
    "C009": (False, False, False, DecisionValue.PASS_),
    "C010": (False, False, False, DecisionValue.PASS_),
}


@pytest.mark.parametrize("candidate_no", sorted(EXPECTED.keys()))
def test_screening_matches_sql_simulation(
    candidate_no, candidates, rule_set_job, rule_set_global,
):
    """SQL 시뮬레이션 결과와 Python 엔진 결과 일치 검증."""
    engine = ScreeningEngine()
    result = engine.screen(
        profile=candidates[candidate_no],
        rule_sets=[rule_set_job, rule_set_global],
    )

    expected_d1, expected_d2, expected_d3, expected_rec = EXPECTED[candidate_no]
    assert result.d1_triggered == expected_d1, f"{candidate_no} D1 mismatch"
    assert result.d2_triggered == expected_d2, f"{candidate_no} D2 mismatch"
    assert result.d3_triggered == expected_d3, f"{candidate_no} D3 mismatch"
    assert result.recommended_decision == expected_rec, f"{candidate_no} recommendation mismatch"


def test_evidence_payload_has_triggered_rules(candidates, rule_set_job, rule_set_global):
    """C005 (D1∧D2∧D3 모두) - rule_evidence에 트리거된 룰 정보가 모두 포함되는지."""
    engine = ScreeningEngine()
    result = engine.screen(
        profile=candidates["C005"],
        rule_sets=[rule_set_job, rule_set_global],
    )

    assert result.rule_evidence["D1"]["triggered"] is True
    assert result.rule_evidence["D1"]["triggered_count"] >= 1
    assert result.rule_evidence["D2"]["triggered"] is True
    assert result.rule_evidence["D3"]["triggered"] is True

    # D1 트리거된 룰에 학력·경력 룰 둘 다 포함되어야 함
    d1_codes = {r["code"] for r in result.rule_evidence["D1"]["rules"]}
    assert "D1_EDU_MIN" in d1_codes
    assert "D1_CAREER_MIN" in d1_codes


def test_pass_case_has_empty_triggered_rules(candidates, rule_set_job, rule_set_global):
    """C001 - 통과 케이스. 모든 그룹의 triggered_rules가 비어 있어야 함."""
    engine = ScreeningEngine()
    result = engine.screen(
        profile=candidates["C001"],
        rule_sets=[rule_set_job, rule_set_global],
    )

    assert result.recommended_decision == DecisionValue.PASS_
    assert result.rule_evidence["D1"]["rules"] == []
    assert result.rule_evidence["D2"]["rules"] == []
    assert result.rule_evidence["D3"]["rules"] == []


def test_applied_rule_sets_recorded(candidates, rule_set_job, rule_set_global):
    """감사 추적: 적용된 룰셋 메타가 결과에 기록되어야 함."""
    engine = ScreeningEngine()
    result = engine.screen(
        profile=candidates["C001"],
        rule_sets=[rule_set_job, rule_set_global],
    )

    assert len(result.applied_rule_sets) == 2
    scopes = {rs["scope"] for rs in result.applied_rule_sets}
    assert scopes == {"JOB", "GLOBAL"}


def test_input_snapshot_records_evaluation_inputs(candidates, rule_set_job, rule_set_global):
    """input_snapshot에 평가에 쓰인 핵심 필드가 직렬화되어야 함."""
    engine = ScreeningEngine()
    result = engine.screen(
        profile=candidates["C002"],
        rule_sets=[rule_set_job, rule_set_global],
    )

    snap = result.input_snapshot
    assert snap["education_level"] == "HIGH_SCHOOL"
    assert snap["career_years"] == 4.0
    assert snap["legal_disqualification_answer"] is False
    assert "missing_required" in snap["attachment_checklist"]


def test_empty_rule_sets_raises(candidates):
    engine = ScreeningEngine()
    with pytest.raises(ValueError):
        engine.screen(profile=candidates["C001"], rule_sets=[])
