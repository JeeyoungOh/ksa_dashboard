"""
field_path로 후보자 데이터에서 값 추출.

지원 표기법:
  - "education_level"                 → profile.education_level
  - "attachment_checklist.missing_required" → profile.attachment_checklist["missing_required"]
  - "normalized_profile.is_patriot_top"     → profile.normalized_profile["is_patriot_top"]

dict 키 접근, 객체 속성 접근을 모두 지원. 누락 시 None 반환 (KeyError 발생 X).
"""
from __future__ import annotations
from typing import Any

from pydantic import BaseModel


# 누락된 필드를 명확히 구분하기 위한 sentinel (None과 구분)
class _Missing:
    def __repr__(self) -> str:
        return "<MISSING>"

MISSING = _Missing()


def extract(obj: Any, field_path: str) -> Any:
    """
    obj에서 field_path로 값 추출. 누락 시 MISSING 반환.

    Args:
        obj: dict 또는 Pydantic 모델 또는 일반 객체
        field_path: 점으로 구분된 경로
    """
    parts = field_path.split(".")
    current: Any = obj

    for part in parts:
        if current is MISSING:
            return MISSING

        if isinstance(current, BaseModel):
            current = getattr(current, part, MISSING)
        elif isinstance(current, dict):
            current = current.get(part, MISSING)
        elif hasattr(current, part):
            current = getattr(current, part, MISSING)
        else:
            return MISSING

    return current
