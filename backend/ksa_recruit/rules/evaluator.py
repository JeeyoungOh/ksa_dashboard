"""
단일 RuleItem을 후보자 데이터에 대해 평가.

설계 원칙:
  - 평가 실패(조건 위반)를 "트리거됨"으로 표현. 결격 사유에 해당하면 True.
  - 룰 항목 코드 자체가 의미를 나타냄 (예: D1_EDU_MIN = 학력 최소조건 미달).
"""
from __future__ import annotations
from typing import Any

from ..domain.models import RuleItem, TriggeredRule
from .extractors import extract, MISSING
from .operators import evaluate_operator


class RuleEvaluator:
    """단일 룰 평가기. 상태 없음 → 함수처럼 사용 가능."""

    @staticmethod
    def evaluate(rule: RuleItem, candidate_data: Any) -> tuple[bool, Any]:
        """
        룰을 후보자 데이터에 대해 평가.

        Returns:
            (triggered, actual_value)
              - triggered: True이면 룰이 트리거됨 (결격 사유 발생).
              - actual_value: 추출된 실제 값 (evidence에 기록).

        평가 모델:
            룰의 expected_value 와 operator 는 "이 조건을 만족하면 결격"을 표현.
            예) D1_EDU_MIN: operator=not_in, expected=[BACHELOR, MASTER, DOCTORATE]
                → 후보자 학력이 학사·석사·박사 중 하나가 아니면 트리거.
        """
        actual = extract(candidate_data, rule.field_path)

        if actual is MISSING:
            # 필드 자체가 누락 → 룰별 정책: 기본은 트리거 안함 (안전 측 가정).
            # 실제 운영에서는 룰 메타에 missing_policy를 추가해 제어 가능.
            return False, None

        try:
            triggered = evaluate_operator(rule.operator, actual, rule.expected_value)
        except (TypeError, ValueError) as e:
            # 연산자 평가 중 타입 오류 등은 트리거 안함 (안전 측). 추후 로깅.
            return False, actual

        return triggered, actual

    @staticmethod
    def to_triggered_rule(rule: RuleItem, actual_value: Any) -> TriggeredRule:
        """트리거된 룰을 evidence 객체로 변환."""
        return TriggeredRule(
            rule_code=rule.code,
            rule_name=rule.name,
            field_path=rule.field_path,
            actual_value=actual_value,
            expected_value=rule.expected_value,
            operator=rule.operator,
        )
