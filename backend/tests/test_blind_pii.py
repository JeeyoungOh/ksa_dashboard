"""
BlindDetector + PIIScrubber 테스트.
"""
from __future__ import annotations
import pytest

from ksa_recruit.domain.enums import BlindCategory
from ksa_recruit.engines.blind import BlindDetector
from ksa_recruit.engines.pii_scrub import PIIScrubber


# =========================================================================
# 블라인드 탐지
# =========================================================================
def test_c007_detects_three_categories(narrative_with_violations):
    """C007 자기소개서: 학교·지역·가족 3종 모두 탐지되어야 함."""
    detector = BlindDetector()
    result = detector.detect(narrative_with_violations)

    assert result.detection_count >= 3
    categories = {d.category for d in result.detections}
    assert BlindCategory.SCHOOL in categories
    assert BlindCategory.REGION in categories
    assert BlindCategory.FAMILY in categories


def test_c007_masking_replaces_violations(narrative_with_violations):
    """마스킹된 cover_letter에는 원본 키워드가 남아 있으면 안됨."""
    detector = BlindDetector()
    result = detector.detect(narrative_with_violations)

    masked = result.cover_letter_masked
    assert masked is not None
    assert "서울대학교" not in masked
    assert "어머니" not in masked
    # 마스킹 라벨이 포함되어야 함
    assert "[학교]" in masked
    assert "[가족]" in masked


def test_c007_longer_keyword_takes_precedence(narrative_with_violations):
    """
    "서울대학교"가 "서울"보다 먼저 매칭되어야 함.
    이게 안되면 "서울"이 별도로 [지역]으로 잘못 매칭됨.
    """
    detector = BlindDetector()
    result = detector.detect(narrative_with_violations)

    # "서울"만으로 매칭된 detection이 cover_letter에 없어야 함
    region_detections_in_letter = [
        d for d in result.detections
        if d.field_name == "cover_letter" and d.category == BlindCategory.REGION
    ]
    # 부산만 1건 매칭되어야 함 ("서울"은 "서울대학교"의 일부라 제외)
    assert len(region_detections_in_letter) == 1
    assert region_detections_in_letter[0].matched_text == "부산"


def test_clean_narrative_has_no_detections(narrative_clean):
    """C001 깨끗한 텍스트: 위배 0건."""
    detector = BlindDetector()
    result = detector.detect(narrative_clean)

    assert result.detection_count == 0
    assert result.detections == []
    # 위배 없으면 마스킹 텍스트 = 원본
    assert result.cover_letter_masked == narrative_clean.cover_letter


def test_summary_counts_by_category(narrative_with_violations):
    detector = BlindDetector()
    result = detector.detect(narrative_with_violations)

    assert result.detection_summary["total"] == result.detection_count
    by_cat = result.detection_summary["by_category"]
    assert by_cat[BlindCategory.SCHOOL.value] >= 1


# =========================================================================
# PII 스크럽
# =========================================================================
def test_pii_scrubs_phone():
    text = "연락처는 010-1234-5678 입니다."
    scrubber = PIIScrubber()
    result = scrubber.scrub(text)

    assert "010-1234-5678" not in result.input_scrubbed
    assert "[전화번호]" in result.input_scrubbed
    assert any(p.pii_type == "PHONE" for p in result.detected_pii)


def test_pii_scrubs_email():
    text = "이메일은 jeeyoung@ksa.or.kr 입니다."
    scrubber = PIIScrubber()
    result = scrubber.scrub(text)

    assert "jeeyoung@ksa.or.kr" not in result.input_scrubbed
    assert "[이메일]" in result.input_scrubbed


def test_pii_scrubs_rrn():
    text = "주민번호: 880101-1234567"
    scrubber = PIIScrubber()
    result = scrubber.scrub(text)

    assert "880101-1234567" not in result.input_scrubbed
    assert "[주민번호]" in result.input_scrubbed


def test_pii_scrubs_known_name():
    text = "지원자 김무결은 우수한 후보입니다."
    scrubber = PIIScrubber()
    result = scrubber.scrub(text)

    assert "김무결" not in result.input_scrubbed
    assert "[이름]" in result.input_scrubbed


def test_pii_passed_when_clean():
    text = "AI 연구에 5년간 매진해 왔습니다."
    scrubber = PIIScrubber()
    result = scrubber.scrub(text)

    assert result.passed is True
    assert result.detected_pii == []


def test_pii_layer_results_recorded():
    text = "이메일 a@b.com 전화 010-1111-2222"
    scrubber = PIIScrubber()
    result = scrubber.scrub(text)

    assert result.layer_results["layer1_dict"] >= 2
    assert result.layer_results["layer2_ner"] == 0
    assert result.layer_results["layer3_heuristic"] == 0


def test_pii_handles_empty_input():
    scrubber = PIIScrubber()
    result = scrubber.scrub("")
    assert result.passed is True
    assert result.detected_pii == []

    result = scrubber.scrub(None)
    assert result.passed is True
