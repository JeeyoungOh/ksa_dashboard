"""
PIIScrubber - LLM 호출 전 PII 제거 엔진 (MVP: Layer 1 사전 + 정규식).

설계 원칙:
  - LLM에 보낼 텍스트는 반드시 이 엔진을 거쳐야 함 (외부 데이터 유출 방지).
  - 잔여 PII가 없을 때만 passed=True. 운영에선 passed=False면 LLM 호출 차단.
"""
from __future__ import annotations
import re
from dataclasses import dataclass

from ..domain.models import PIIDetection, PIIScrubResult


@dataclass(frozen=True)
class PIIPattern:
    pii_type: str
    pattern: re.Pattern
    mask: str


# 한국 도메인에 맞춘 기본 PII 패턴
DEFAULT_PII_PATTERNS: tuple[PIIPattern, ...] = (
    # 휴대전화 (010-1234-5678, 01012345678)
    PIIPattern("PHONE", re.compile(r"01[0-9][\s\-\.]?\d{3,4}[\s\-\.]?\d{4}"), "[전화번호]"),
    # 일반 전화 (02-123-4567, 031-1234-5678)
    PIIPattern("PHONE_LAND", re.compile(r"\b0\d{1,2}[\s\-\.]?\d{3,4}[\s\-\.]?\d{4}\b"), "[전화번호]"),
    # 주민등록번호 (123456-1234567)
    PIIPattern("RRN", re.compile(r"\d{6}[\s\-\.]?[1-4]\d{6}"), "[주민번호]"),
    # 이메일
    PIIPattern("EMAIL", re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"), "[이메일]"),
    # 우편번호
    PIIPattern("POSTAL_CODE", re.compile(r"\b\d{5}\b(?=\s*[가-힣])"), "[우편번호]"),
    # 주소 (시/도 + 구/군 + 동/읍/면 패턴)
    PIIPattern(
        "ADDR",
        re.compile(r"(?:서울|부산|대구|인천|광주|대전|울산|세종|경기도?|강원도?|충청[남북]?도?|전라[남북]?도?|경상[남북]?도?|제주(?:특별자치)?도?)\s*[가-힣]+(?:구|군|시)\s*[가-힣]+(?:동|읍|면|로|길)"),
        "[주소]",
    ),
)


# 한국식 이름 후보 사전 (예시 - 실제 운영에선 한국 인구 통계 기반 사전 사용)
DEFAULT_NAME_DICT: frozenset[str] = frozenset({
    "김철수", "이영희", "박민수", "최지영",
    "김무결", "이부족", "박미제출", "최자기신고", "정삼중",
    "강이중", "윤위배", "임가점", "한경계", "노유공자",
})


class PIIScrubber:
    def __init__(
        self,
        patterns: tuple[PIIPattern, ...] = DEFAULT_PII_PATTERNS,
        name_dict: frozenset[str] = DEFAULT_NAME_DICT,
    ) -> None:
        self._patterns = patterns
        self._name_dict = name_dict

    def scrub(self, text: str | None) -> PIIScrubResult:
        if not text:
            return PIIScrubResult(
                input_original=text or "",
                input_scrubbed=text or "",
                detected_pii=[],
                layer_results={"layer1_dict": 0, "layer2_ner": 0, "layer3_heuristic": 0},
                passed=True,
            )

        original = text
        scrubbed = text
        detections: list[PIIDetection] = []

        # 1) 정규식 기반 패턴 (Layer 1a)
        for pat in self._patterns:
            for m in pat.pattern.finditer(scrubbed):
                detections.append(PIIDetection(
                    pii_type=pat.pii_type,
                    text=m.group(),
                    span_start=m.start(),
                    span_end=m.end(),
                ))
            scrubbed = pat.pattern.sub(pat.mask, scrubbed)

        # 2) 이름 사전 기반 (Layer 1b)
        for name in self._name_dict:
            idx = 0
            while True:
                pos = scrubbed.find(name, idx)
                if pos < 0:
                    break
                detections.append(PIIDetection(
                    pii_type="PERSON_NAME",
                    text=name,
                    span_start=pos,
                    span_end=pos + len(name),
                ))
                idx = pos + len(name)
            scrubbed = scrubbed.replace(name, "[이름]")

        layer_results = {
            "layer1_dict": len(detections),
            "layer2_ner": 0,        # 추후 NER 모델 도입 시 채움
            "layer3_heuristic": 0,  # 추후 LLM 휴리스틱 도입 시 채움
        }

        # 잔여 PII 검사: 스크럽 후 남은 패턴이 있는지 재검사
        residual = any(p.pattern.search(scrubbed) for p in self._patterns)
        passed = not residual

        return PIIScrubResult(
            input_original=original,
            input_scrubbed=scrubbed,
            detected_pii=detections,
            layer_results=layer_results,
            passed=passed,
        )
