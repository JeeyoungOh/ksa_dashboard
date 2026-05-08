"""
BonusEngine - 가점 자동계산.

처리 순서:
  1) 매칭 단계: 후보자 프로필 ↔ 가점 룰 매칭. 매칭된 룰을 calculated_score와 함께 수집.
  2) exclusive_group 적용: 같은 그룹(EDUCATION 등) 내 최고점 1개만 살림. 나머지는 REJECTED.
  3) 총 상한 적용: 점수 내림차순으로 누적, max_bonus_score를 넘는 항목은 부분 감액 또는 REJECTED.

면접 후 가점(B7)은 별도 흐름이라 이 엔진에서 다루지 않음.
법정 우대 가점은 SQL 시뮬레이션과 동일하게 normalized_profile 플래그를 통해 평가.
"""
from __future__ import annotations
from decimal import Decimal
from typing import Any

from ..domain.enums import BonusStatus
from ..domain.models import (
    BonusRule, BonusRuleSet, CandidateProfile,
    BonusItemResult, BonusResult,
)
from ..rules.evaluator import RuleEvaluator


class BonusEngine:
    def __init__(self, evaluator: RuleEvaluator | None = None) -> None:
        self._evaluator = evaluator or RuleEvaluator()

    # ---- public API -----------------------------------------------------

    def calculate(
        self,
        profile: CandidateProfile,
        rule_set: BonusRuleSet,
    ) -> BonusResult:
        """후보자 프로필에 가점 룰셋을 적용해 가점 계산."""
        # 1. 룰 매칭 → 후보 가점 항목 수집
        matched = self._match_rules(profile, rule_set)

        # 2. exclusive_group 적용
        after_exclusive = self._apply_exclusive_groups(matched)

        # 3. 총 상한 적용
        final_items = self._apply_max_cap(after_exclusive, rule_set.max_bonus_score)

        total = sum(
            (item.applied_score for item in final_items if item.status == BonusStatus.APPROVED),
            Decimal("0"),
        )

        return BonusResult(
            candidate_id=profile.candidate_id,
            bonus_rule_set_id=rule_set.id,
            bonus_rule_set_version=rule_set.version,
            items=final_items,
            total_doc_bonus=total,
            max_bonus_score=rule_set.max_bonus_score,
        )

    # ---- 1. 매칭 --------------------------------------------------------

    def _match_rules(
        self, profile: CandidateProfile, rule_set: BonusRuleSet
    ) -> list[BonusItemResult]:
        """후보자 데이터에 매칭되는 가점 룰만 추려 PENDING 상태로 반환."""
        results: list[BonusItemResult] = []

        for rule in rule_set.rules:
            if not rule.is_active:
                continue

            triggered, actual = self._evaluator.evaluate(
                # RuleItem 형태로 어댑팅 (BonusRule도 동일 필드 구조)
                _bonus_to_rule_adapter(rule),
                profile,
            )
            if not triggered:
                continue

            results.append(BonusItemResult(
                bonus_rule_id=rule.id,
                bonus_rule_code=rule.code,
                bonus_rule_name=rule.name,
                exclusive_group=rule.exclusive_group,
                calculated_score=Decimal(rule.score_value),
                applied_score=Decimal("0"),       # 일단 0, 후속 단계에서 결정
                status=BonusStatus.PENDING_APPROVAL,
                matched_evidence={"actual": _serialize(actual)},
            ))

        return results

    # ---- 2. exclusive_group --------------------------------------------

    def _apply_exclusive_groups(
        self, items: list[BonusItemResult]
    ) -> list[BonusItemResult]:
        """
        같은 exclusive_group 내에서는 최고점 1개만 살리고 나머지는 REJECTED 처리.
        exclusive_group이 None인 항목은 그대로 통과.
        """
        # exclusive_group별 최고점 항목 인덱스
        best_in_group: dict[str, int] = {}
        for idx, item in enumerate(items):
            if item.exclusive_group is None:
                continue
            current_best = best_in_group.get(item.exclusive_group)
            if current_best is None:
                best_in_group[item.exclusive_group] = idx
            else:
                if item.calculated_score > items[current_best].calculated_score:
                    best_in_group[item.exclusive_group] = idx

        winners = set(best_in_group.values())

        result: list[BonusItemResult] = []
        for idx, item in enumerate(items):
            if item.exclusive_group is None or idx in winners:
                result.append(item)
            else:
                result.append(item.model_copy(update={
                    "status": BonusStatus.REJECTED,
                    "applied_score": Decimal("0"),
                    "rejection_reason": (
                        f"exclusive_group={item.exclusive_group} 내 다른 룰이 "
                        f"더 높은 점수로 채택됨"
                    ),
                }))

        return result

    # ---- 3. 총 상한 -----------------------------------------------------

    def _apply_max_cap(
        self,
        items: list[BonusItemResult],
        max_score: Decimal,
    ) -> list[BonusItemResult]:
        """
        남은 PENDING_APPROVAL 항목들을 점수 내림차순으로 누적.
        상한을 넘는 항목은 부분 감액 또는 REJECTED.
        """
        result: list[BonusItemResult] = []
        running = Decimal("0")

        # PENDING 항목만 점수 내림차순 정렬, 그 외(이미 REJECTED)는 그대로
        pending_indices = [
            i for i, x in enumerate(items)
            if x.status == BonusStatus.PENDING_APPROVAL
        ]
        pending_sorted = sorted(
            pending_indices,
            key=lambda i: items[i].calculated_score,
            reverse=True,
        )

        # 처리 결정 맵
        decisions: dict[int, BonusItemResult] = {}

        for idx in pending_sorted:
            item = items[idx]
            if running >= max_score:
                # 상한 이미 도달 → 거부
                decisions[idx] = item.model_copy(update={
                    "status": BonusStatus.REJECTED,
                    "applied_score": Decimal("0"),
                    "rejection_reason": f"총 가점 상한({max_score}) 도달로 거부",
                })
            elif running + item.calculated_score > max_score:
                # 일부만 적용
                applied = max_score - running
                decisions[idx] = item.model_copy(update={
                    "status": BonusStatus.APPROVED,
                    "applied_score": applied,
                    "rejection_reason": (
                        f"총 가점 상한({max_score}) 적용으로 "
                        f"{item.calculated_score} → {applied} 감액"
                    ),
                })
                running = max_score
            else:
                # 정상 승인
                decisions[idx] = item.model_copy(update={
                    "status": BonusStatus.APPROVED,
                    "applied_score": item.calculated_score,
                })
                running += item.calculated_score

        # 원래 순서로 결과 조립
        for idx, item in enumerate(items):
            result.append(decisions.get(idx, item))

        return result


def _bonus_to_rule_adapter(rule: BonusRule):
    """BonusRule을 RuleEvaluator가 기대하는 인터페이스로 어댑팅."""
    from ..domain.models import RuleItem
    from uuid import UUID
    return RuleItem(
        id=rule.id if isinstance(rule.id, UUID) else UUID(int=0),
        code=rule.code,
        name=rule.name,
        operator=rule.operator,
        field_path=rule.field_path,
        expected_value=rule.expected_value,
        is_active=rule.is_active,
    )


def _serialize(v: Any) -> Any:
    from decimal import Decimal as D
    from enum import Enum
    if isinstance(v, D):
        return float(v)
    if isinstance(v, Enum):
        return v.value
    if isinstance(v, list):
        return [_serialize(x) for x in v]
    if isinstance(v, dict):
        return {k: _serialize(val) for k, val in v.items()}
    return v
