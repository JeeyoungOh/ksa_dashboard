"""
ScreeningEngine - 결격 자동판정.

분기 로직 (확정):
  - D1 ∧ D2 ∧ D3 = 모두 True → recommendation = FAIL  (AUTO_FAIL)
  - 1~2개 True              → recommendation = HOLD
  - 0개 True                → recommendation = PASS

룰셋 우선순위: JOB > GLOBAL > CYCLE
  - 동일 그룹 코드(D1/D2/D3)가 여러 룰셋에 존재할 경우 JOB 룰셋이 우선.
  - 동일 룰셋 안에서는 그룹 내 모든 룰이 OR 결합.
"""
from __future__ import annotations
from typing import Any

from ..domain.enums import DecisionValue, RuleGroupCode, RuleScope
from ..domain.models import (
    CandidateProfile, RuleSet, RuleGroup, ScreeningResult,
    GroupResult, TriggeredRule,
)
from ..rules.evaluator import RuleEvaluator


class ScreeningEngine:
    """결격 자동판정 엔진."""

    def __init__(self, evaluator: RuleEvaluator | None = None) -> None:
        self._evaluator = evaluator or RuleEvaluator()

    # ---- public API -----------------------------------------------------

    def screen(
        self,
        profile: CandidateProfile,
        rule_sets: list[RuleSet],
    ) -> ScreeningResult:
        """후보자 프로필에 룰셋 목록을 적용해 자동판정 결과 산출."""
        if not rule_sets:
            raise ValueError("최소 1개 이상의 RuleSet이 필요합니다.")

        # 1. 우선순위에 따라 그룹 머지: JOB > GLOBAL > CYCLE
        merged_groups = self._merge_groups_by_priority(rule_sets)

        # 2. 각 그룹 평가
        d1 = self._evaluate_group(merged_groups.get(RuleGroupCode.D1), profile)
        d2 = self._evaluate_group(merged_groups.get(RuleGroupCode.D2), profile)
        d3 = self._evaluate_group(merged_groups.get(RuleGroupCode.D3), profile)

        # 3. 추천값 산출
        recommendation = self._derive_recommendation(d1.triggered, d2.triggered, d3.triggered)

        # 4. evidence 페이로드 (DB INSERT용)
        rule_evidence = {
            "D1": self._group_to_evidence(d1),
            "D2": self._group_to_evidence(d2),
            "D3": self._group_to_evidence(d3),
        }

        # 5. 적용된 룰셋 메타 (감사 추적)
        applied_rule_sets = [
            {
                "rule_set_id": str(rs.id),
                "code": rs.code,
                "version": rs.version,
                "scope": rs.scope.value,
            }
            for rs in rule_sets
        ]

        # 6. 입력 스냅샷 (감사 추적, DB INSERT용)
        input_snapshot = self._snapshot(profile)

        return ScreeningResult(
            candidate_id=profile.candidate_id,
            d1_triggered=d1.triggered,
            d2_triggered=d2.triggered,
            d3_triggered=d3.triggered,
            recommended_decision=recommendation,
            rule_evidence=rule_evidence,
            input_snapshot=input_snapshot,
            applied_rule_sets=applied_rule_sets,
        )

    # ---- 내부 로직 -------------------------------------------------------

    def _merge_groups_by_priority(
        self, rule_sets: list[RuleSet]
    ) -> dict[RuleGroupCode, RuleGroup]:
        """
        JOB > GLOBAL > CYCLE 우선순위에 따라 같은 코드의 그룹을 머지.
        같은 그룹 코드가 여러 룰셋에 있으면 우선순위 높은 룰셋의 그룹만 채택.
        """
        priority = {RuleScope.JOB: 0, RuleScope.GLOBAL: 1, RuleScope.CYCLE: 2}
        sorted_sets = sorted(rule_sets, key=lambda rs: priority.get(rs.scope, 99))

        merged: dict[RuleGroupCode, RuleGroup] = {}
        for rs in sorted_sets:
            for group in rs.groups:
                # 우선순위 높은 룰셋이 먼저 들어왔으면 덮어쓰지 않음
                if group.code not in merged:
                    merged[group.code] = group
        return merged

    def _evaluate_group(
        self, group: RuleGroup | None, profile: CandidateProfile
    ) -> GroupResult:
        """단일 그룹 (D1/D2/D3) 내 모든 룰 평가. OR 결합."""
        if group is None:
            return GroupResult(
                code=RuleGroupCode.D1,  # placeholder
                triggered=False,
                triggered_rules=[],
            )

        triggered_rules: list[TriggeredRule] = []
        for rule in group.items:
            if not rule.is_active:
                continue
            triggered, actual = self._evaluator.evaluate(rule, profile)
            if triggered:
                triggered_rules.append(self._evaluator.to_triggered_rule(rule, actual))

        return GroupResult(
            code=group.code,
            triggered=len(triggered_rules) > 0,
            triggered_rules=triggered_rules,
        )

    def _derive_recommendation(
        self, d1: bool, d2: bool, d3: bool
    ) -> DecisionValue:
        """확정 분기 룰 적용."""
        triggered_count = sum([d1, d2, d3])
        if triggered_count == 3:
            return DecisionValue.FAIL
        if triggered_count >= 1:
            return DecisionValue.HOLD
        return DecisionValue.PASS_

    def _group_to_evidence(self, result: GroupResult) -> dict:
        """GroupResult를 DB INSERT용 evidence 형태로 직렬화."""
        return {
            "triggered": result.triggered,
            "triggered_count": len(result.triggered_rules),
            "rules": [
                {
                    "code": tr.rule_code,
                    "name": tr.rule_name,
                    "field": tr.field_path,
                    "actual": _serialize(tr.actual_value),
                    "expected": _serialize(tr.expected_value),
                    "op": tr.operator,
                }
                for tr in result.triggered_rules
            ],
        }

    def _snapshot(self, profile: CandidateProfile) -> dict:
        """후보자 프로필에서 평가에 사용된 핵심 필드만 스냅샷."""
        return {
            "education_level": profile.education_level.value,
            "career_years": _serialize(profile.career_years),
            "submitted_documents": list(profile.submitted_documents),
            "attachment_checklist": dict(profile.attachment_checklist),
            "legal_disqualification_answer": profile.legal_disqualification_answer,
            "self_declaration_submitted": profile.self_declaration_submitted,
        }


# Decimal · enum 등을 JSON-friendly 값으로 변환
def _serialize(v: Any) -> Any:
    from decimal import Decimal
    from enum import Enum
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, Enum):
        return v.value
    if isinstance(v, list):
        return [_serialize(x) for x in v]
    if isinstance(v, dict):
        return {k: _serialize(val) for k, val in v.items()}
    return v
