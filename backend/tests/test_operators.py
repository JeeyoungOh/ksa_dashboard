"""
룰 연산자 + extractor 단위 테스트.
"""
from __future__ import annotations
from decimal import Decimal

import pytest

from ksa_recruit.rules.operators import evaluate_operator, OPERATORS
from ksa_recruit.rules.extractors import extract, MISSING


# =========================================================================
# Operators
# =========================================================================
class TestOperators:
    def test_eq(self):
        assert evaluate_operator("eq", "MASTER", "MASTER") is True
        assert evaluate_operator("eq", "MASTER", "BACHELOR") is False

    def test_neq(self):
        assert evaluate_operator("neq", "A", "B") is True
        assert evaluate_operator("neq", "A", "A") is False

    def test_in(self):
        assert evaluate_operator("in", "MASTER", ["BACHELOR", "MASTER"]) is True
        assert evaluate_operator("in", "PHD", ["BACHELOR", "MASTER"]) is False

    def test_not_in_for_d1_edu_min(self):
        """D1_EDU_MIN: education NOT IN [BACHELOR, MASTER, DOCTORATE] → 결격."""
        valid = ["BACHELOR", "MASTER", "DOCTORATE"]
        assert evaluate_operator("not_in", "HIGH_SCHOOL", valid) is True
        assert evaluate_operator("not_in", "MASTER", valid) is False

    def test_ge(self):
        assert evaluate_operator("ge", 5, 3) is True
        assert evaluate_operator("ge", 3, 3) is True
        assert evaluate_operator("ge", 2, 3) is False

    def test_lt_for_career_min(self):
        """D1_CAREER_MIN: career_years < 3 → 결격."""
        assert evaluate_operator("lt", Decimal("2.5"), 3) is True
        assert evaluate_operator("lt", Decimal("3"), 3) is False

    def test_between(self):
        assert evaluate_operator("between", 5, [3, 7]) is True
        assert evaluate_operator("between", 3, [3, 7]) is True
        assert evaluate_operator("between", 7, [3, 7]) is True
        assert evaluate_operator("between", 8, [3, 7]) is False

    def test_is_true_is_false(self):
        assert evaluate_operator("is_true", True, None) is True
        assert evaluate_operator("is_true", False, None) is False
        assert evaluate_operator("is_false", False, None) is True
        assert evaluate_operator("is_false", True, None) is False

    def test_contains_for_certifications(self):
        assert evaluate_operator("contains", ["A_GRADE", "B_GRADE"], "A_GRADE") is True
        assert evaluate_operator("contains", ["B_GRADE"], "A_GRADE") is False

    def test_contains_any(self):
        assert evaluate_operator("contains_any", ["X", "A"], ["A", "B"]) is True
        assert evaluate_operator("contains_any", ["X", "Y"], ["A", "B"]) is False

    def test_unknown_operator_raises(self):
        with pytest.raises(ValueError):
            evaluate_operator("unknown_op", 1, 1)

    def test_all_registered_operators_callable(self):
        """레지스트리에 등록된 모든 연산자가 호출 가능한지."""
        for name, fn in OPERATORS.items():
            assert callable(fn), f"{name} is not callable"


# =========================================================================
# Extractors
# =========================================================================
class TestExtract:
    def test_simple_attribute(self):
        obj = {"a": 1, "b": 2}
        assert extract(obj, "a") == 1

    def test_nested_dict_dot_path(self):
        obj = {"checklist": {"missing": True}}
        assert extract(obj, "checklist.missing") is True

    def test_missing_returns_sentinel(self):
        obj = {"a": 1}
        assert extract(obj, "b") is MISSING
        assert extract(obj, "a.x") is MISSING  # 1에서 x 추출 → MISSING

    def test_pydantic_model_attribute(self, candidates):
        profile = candidates["C001"]
        assert extract(profile, "candidate_no") == "C001"

    def test_pydantic_with_dict_path(self, candidates):
        profile = candidates["C001"]
        # normalized_profile은 dict
        result = extract(profile, "normalized_profile.has_high_language")
        assert result is True
