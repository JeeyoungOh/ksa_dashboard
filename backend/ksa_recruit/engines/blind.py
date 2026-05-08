"""
BlindDetector - 블라인드 위배 탐지 엔진 (MVP: Layer 1 사전 매칭만).

NER 기반 Layer 2, LLM 기반 Layer 3은 별도 구현체로 추후 추가.
이 엔진은 단순 사전 매칭(대소문자 구분 X, 단어 경계 미고려) 방식으로,
시뮬레이션 SQL과 동일한 동작을 재현.

확장 포인트:
  - DictLoader: 정책 사전 로딩 (DB blind_policy_items + 키워드 사전)
  - Detector 인터페이스: 다른 레이어 추가 시 동일 인터페이스로 결합
"""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable
from uuid import UUID

from ..domain.enums import BlindCategory, DetectorLayer
from ..domain.models import (
    CandidateNarrative, BlindDetection, BlindDetectionResult,
)


@dataclass(frozen=True)
class BlindDictEntry:
    """블라인드 사전의 한 엔트리. category × keyword."""
    category: BlindCategory
    keyword: str
    mask_label: str   # 마스킹 시 치환 라벨 (예: "[학교]")


# 기본 사전 (KSA 임시 표준, 추후 DB의 blind_policy_items + dict 테이블에서 로드)
DEFAULT_BLIND_DICT: tuple[BlindDictEntry, ...] = (
    # 학교
    BlindDictEntry(BlindCategory.SCHOOL, "서울대학교", "[학교]"),
    BlindDictEntry(BlindCategory.SCHOOL, "고려대학교", "[학교]"),
    BlindDictEntry(BlindCategory.SCHOOL, "연세대학교", "[학교]"),
    BlindDictEntry(BlindCategory.SCHOOL, "KAIST", "[학교]"),
    BlindDictEntry(BlindCategory.SCHOOL, "POSTECH", "[학교]"),
    # 지역
    BlindDictEntry(BlindCategory.REGION, "서울", "[지역]"),
    BlindDictEntry(BlindCategory.REGION, "부산", "[지역]"),
    BlindDictEntry(BlindCategory.REGION, "대구", "[지역]"),
    BlindDictEntry(BlindCategory.REGION, "인천", "[지역]"),
    BlindDictEntry(BlindCategory.REGION, "광주", "[지역]"),
    # 가족
    BlindDictEntry(BlindCategory.FAMILY, "어머니", "[가족]"),
    BlindDictEntry(BlindCategory.FAMILY, "아버지", "[가족]"),
    BlindDictEntry(BlindCategory.FAMILY, "부모님", "[가족]"),
    BlindDictEntry(BlindCategory.FAMILY, "형", "[가족]"),
    BlindDictEntry(BlindCategory.FAMILY, "누나", "[가족]"),
    # 종교
    BlindDictEntry(BlindCategory.RELIGION, "기독교", "[종교]"),
    BlindDictEntry(BlindCategory.RELIGION, "불교", "[종교]"),
    BlindDictEntry(BlindCategory.RELIGION, "천주교", "[종교]"),
)


class BlindDetector:
    """블라인드 위배 탐지기 (Layer 1: 사전 매칭)."""

    def __init__(
        self,
        dictionary: Iterable[BlindDictEntry] = DEFAULT_BLIND_DICT,
    ) -> None:
        # 긴 키워드부터 매칭하도록 정렬 (예: "서울대학교"가 "서울"보다 먼저)
        self._dict = tuple(sorted(dictionary, key=lambda e: -len(e.keyword)))

    # ---- public API -----------------------------------------------------

    def detect(
        self, narrative: CandidateNarrative
    ) -> BlindDetectionResult:
        """자유서술 텍스트에서 블라인드 위배 탐지 + 마스킹된 텍스트 생성."""
        all_detections: list[BlindDetection] = []
        masked = {}

        for field_name, text in (
            ("cover_letter", narrative.cover_letter),
            ("career_history", narrative.career_history),
        ):
            if not text:
                masked[field_name] = None
                continue

            detections, masked_text = self._scan_text(
                narrative.candidate_id, field_name, text
            )
            all_detections.extend(detections)
            masked[field_name] = masked_text

        summary = _build_summary(all_detections)

        return BlindDetectionResult(
            candidate_id=narrative.candidate_id,
            detections=all_detections,
            detection_count=len(all_detections),
            detection_summary=summary,
            cover_letter_masked=masked["cover_letter"],
            career_history_masked=masked["career_history"],
        )

    # ---- 내부 로직 -------------------------------------------------------

    def _scan_text(
        self, candidate_id: UUID, field_name: str, text: str
    ) -> tuple[list[BlindDetection], str]:
        """텍스트에서 사전 키워드 탐지 후 마스킹된 텍스트도 함께 반환."""
        detections: list[BlindDetection] = []

        # 마스킹 위치를 별도로 추적해 한 번에 치환 (탐지 결과에는 원본 좌표 보존)
        # 각 매치는 (start, end, mask_label)
        masks: list[tuple[int, int, str]] = []

        for entry in self._dict:
            start = 0
            while True:
                idx = text.find(entry.keyword, start)
                if idx < 0:
                    break
                end = idx + len(entry.keyword)

                # 이미 마스킹된 영역과 겹치면 건너뛰기 (예: "서울대학교" 매치 후 "서울" 재매치 방지)
                if any(idx < me and ie < end for ie, me, _ in masks):
                    start = end
                    continue
                if any(ie <= idx < me or ie < end <= me for ie, me, _ in masks):
                    start = end
                    continue

                detections.append(BlindDetection(
                    candidate_id=candidate_id,
                    field_name=field_name,
                    category=entry.category,
                    matched_text=entry.keyword,
                    span_start=idx,
                    span_end=end,
                    detector_layer=DetectorLayer.RULE_DICT,
                    confidence=Decimal("1.0"),
                ))
                masks.append((idx, end, entry.mask_label))
                start = end

        # 텍스트 마스킹 (뒤에서부터 치환해야 좌표 안 깨짐)
        masked_text = text
        for s, e, label in sorted(masks, key=lambda m: -m[0]):
            masked_text = masked_text[:s] + label + masked_text[e:]

        # 탐지 결과는 원본 좌표 기준으로 정렬
        detections.sort(key=lambda d: (d.field_name, d.span_start))
        return detections, masked_text


def _build_summary(detections: list[BlindDetection]) -> dict:
    by_cat: dict[str, int] = {}
    for d in detections:
        by_cat[d.category.value] = by_cat.get(d.category.value, 0) + 1
    return {"total": len(detections), "by_category": by_cat}
