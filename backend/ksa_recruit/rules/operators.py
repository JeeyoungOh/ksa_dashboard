"""
룰 연산자 - 후보자 필드의 actual_value와 룰의 expected_value를 비교.

DB의 rule_items.operator 컬럼 값과 1:1 매핑.
신규 연산자 추가 시 OPERATORS 딕셔너리에 등록만 하면 됨.
"""
from __future__ import annotations
from decimal import Decimal
from typing import Any, Callable


def _to_number(v: Any) -> Decimal:
    """비교를 위해 숫자형으로 강제 변환. 변환 실패 시 ValueError."""
    if isinstance(v, Decimal):
        return v
    if isinstance(v, bool):
        # bool은 int의 서브클래스라 의도치 않은 비교를 막기 위해 명시적으로 변환
        return Decimal(int(v))
    if isinstance(v, (int, float, str)):
        return Decimal(str(v))
    raise ValueError(f"숫자형으로 변환 불가: {v!r}")


# ---- 연산자 함수 시그니처: (actual, expected) -> bool ----------------------

def op_eq(actual: Any, expected: Any) -> bool:
    return actual == expected


def op_neq(actual: Any, expected: Any) -> bool:
    return actual != expected


def op_in(actual: Any, expected: Any) -> bool:
    """expected는 리스트. actual이 expected 안에 있으면 True."""
    if not isinstance(expected, (list, tuple, set)):
        raise ValueError(f"in 연산자의 expected는 리스트여야 함: {expected!r}")
    return actual in expected


def op_not_in(actual: Any, expected: Any) -> bool:
    return not op_in(actual, expected)


def op_ge(actual: Any, expected: Any) -> bool:
    return _to_number(actual) >= _to_number(expected)


def op_le(actual: Any, expected: Any) -> bool:
    return _to_number(actual) <= _to_number(expected)


def op_gt(actual: Any, expected: Any) -> bool:
    return _to_number(actual) > _to_number(expected)


def op_lt(actual: Any, expected: Any) -> bool:
    return _to_number(actual) < _to_number(expected)


def op_between(actual: Any, expected: Any) -> bool:
    """expected는 [low, high] 리스트. inclusive on both ends."""
    if not isinstance(expected, (list, tuple)) or len(expected) != 2:
        raise ValueError(f"between 연산자의 expected는 [low, high]: {expected!r}")
    a = _to_number(actual)
    return _to_number(expected[0]) <= a <= _to_number(expected[1])


def op_is_true(actual: Any, expected: Any = None) -> bool:
    """boolean True 검사. expected 무시."""
    return bool(actual) is True


def op_is_false(actual: Any, expected: Any = None) -> bool:
    return bool(actual) is False


def op_contains(actual: Any, expected: Any) -> bool:
    """actual이 리스트일 때 expected 값을 포함하는지."""
    if isinstance(actual, (list, tuple, set)):
        return expected in actual
    if isinstance(actual, str):
        return expected in actual
    raise ValueError(f"contains 연산자에 부적합한 actual: {type(actual)}")


def op_contains_any(actual: Any, expected: Any) -> bool:
    """actual 리스트가 expected 리스트 중 하나라도 포함하면 True."""
    if not isinstance(actual, (list, tuple, set)):
        raise ValueError(f"contains_any: actual은 리스트여야 함: {type(actual)}")
    if not isinstance(expected, (list, tuple, set)):
        raise ValueError(f"contains_any: expected는 리스트여야 함: {type(expected)}")
    return any(e in actual for e in expected)


# ---- 연산자 레지스트리 -----------------------------------------------------

OPERATORS: dict[str, Callable[[Any, Any], bool]] = {
    "eq": op_eq,
    "neq": op_neq,
    "in": op_in,
    "not_in": op_not_in,
    "ge": op_ge,
    "le": op_le,
    "gt": op_gt,
    "lt": op_lt,
    "between": op_between,
    "is_true": op_is_true,
    "is_false": op_is_false,
    "contains": op_contains,
    "contains_any": op_contains_any,
}


def evaluate_operator(operator: str, actual: Any, expected: Any) -> bool:
    """
    연산자 이름으로 평가 실행.
    Raises:
        ValueError: 등록되지 않은 연산자 사용 시.
    """
    if operator not in OPERATORS:
        raise ValueError(
            f"등록되지 않은 연산자: {operator!r}. "
            f"사용 가능: {sorted(OPERATORS.keys())}"
        )
    return OPERATORS[operator](actual, expected)
