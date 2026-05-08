"""
데모 스크립트.

시뮬레이션 SQL과 동일한 10명 후보자에 대해 ScreeningEngine + BonusEngine을 실행하고
표 형태로 결과를 출력. 시뮬레이션 SQL 결과와 비교해 보면서 검증할 수 있도록.

실행:
  cd rule_engine
  PYTHONPATH=. python scripts/demo.py
"""
from __future__ import annotations
from decimal import Decimal
from uuid import UUID, uuid4

from ksa_recruit.domain.enums import (
    EducationLevel, RuleScope, RuleGroupCode,
)
from ksa_recruit.domain.models import (
    CandidateProfile, CandidateNarrative,
    RuleItem, RuleGroup, RuleSet,
    BonusRule, BonusRuleSet,
)
from ksa_recruit.engines.screening import ScreeningEngine
from ksa_recruit.engines.bonus import BonusEngine
from ksa_recruit.engines.blind import BlindDetector
from ksa_recruit.engines.pii_scrub import PIIScrubber


# ---- 룰셋 정의 (테스트 픽스처와 동일) -------------------------------------
def build_rule_sets() -> tuple[RuleSet, RuleSet]:
    job = RuleSet(
        id=uuid4(), code="JOB_DEFAULT_2026_V1", name="JOB 기본 룰셋",
        scope=RuleScope.JOB, version=1,
        groups=[
            RuleGroup(id=uuid4(), code=RuleGroupCode.D1, name="응시자격 미충족", items=[
                RuleItem(id=uuid4(), code="D1_EDU_MIN", name="학력 최소요건",
                         operator="not_in", field_path="education_level",
                         expected_value=["BACHELOR", "MASTER", "DOCTORATE"]),
                RuleItem(id=uuid4(), code="D1_CAREER_MIN", name="경력 최소요건",
                         operator="lt", field_path="career_years", expected_value=3),
            ]),
            RuleGroup(id=uuid4(), code=RuleGroupCode.D2, name="필수서류 불비", items=[
                RuleItem(id=uuid4(), code="D2_MISSING_DOC", name="필수서류 누락",
                         operator="is_true",
                         field_path="attachment_checklist.missing_required",
                         expected_value=True),
            ]),
        ],
    )
    glob = RuleSet(
        id=uuid4(), code="GLOBAL_LEGAL_DISQUAL_2026", name="GLOBAL 법적결격",
        scope=RuleScope.GLOBAL, version=1,
        groups=[
            RuleGroup(id=uuid4(), code=RuleGroupCode.D3, name="법적 결격 자기신고", items=[
                RuleItem(id=uuid4(), code="D3_SELF_DECLARED", name="법적 결격 자기신고",
                         operator="is_true",
                         field_path="legal_disqualification_answer",
                         expected_value=True),
            ]),
        ],
    )
    return job, glob


def build_bonus_rule_set() -> BonusRuleSet:
    return BonusRuleSet(
        id=uuid4(), code="KSA_BONUS_MVP_2026", name="가점 룰셋", version=1,
        max_bonus_score=Decimal("10"),
        rules=[
            BonusRule(id=uuid4(), code="BONUS_PHD", name="박사학위",
                      score_value=Decimal("5"), operator="eq",
                      field_path="education_level", expected_value="DOCTORATE",
                      exclusive_group="EDUCATION"),
            BonusRule(id=uuid4(), code="BONUS_MASTER", name="석사학위",
                      score_value=Decimal("3"), operator="eq",
                      field_path="education_level", expected_value="MASTER",
                      exclusive_group="EDUCATION"),
            BonusRule(id=uuid4(), code="BONUS_CERT_A", name="자격증 A급",
                      score_value=Decimal("3"), operator="contains",
                      field_path="certifications", expected_value="A_GRADE"),
            BonusRule(id=uuid4(), code="BONUS_CERT_B", name="자격증 B급",
                      score_value=Decimal("1"), operator="contains",
                      field_path="certifications", expected_value="B_GRADE"),
            BonusRule(id=uuid4(), code="BONUS_LANG_HIGH", name="어학 고급",
                      score_value=Decimal("2"), operator="is_true",
                      field_path="normalized_profile.has_high_language",
                      expected_value=True, exclusive_group="LANGUAGE"),
            BonusRule(id=uuid4(), code="BONUS_PATRIOT_10", name="국가유공자 10%",
                      score_value=Decimal("10"), operator="is_true",
                      field_path="normalized_profile.is_patriot_top",
                      expected_value=True, exclusive_group="PATRIOT"),
        ],
    )


def build_candidates() -> dict[str, CandidateProfile]:
    def p(no, edu, career, **kw):
        return CandidateProfile(
            candidate_id=UUID(int=int(no[1:])), candidate_no=no,
            job_code="AI_RESEARCHER",
            education_level=edu, career_years=Decimal(str(career)),
            certifications=kw.get("certs", []),
            submitted_documents=["application_form"]
                if kw.get("missing_doc") else
                ["application_form", "self_intro", "career_history"],
            attachment_checklist={"missing_required": kw.get("missing_doc", False),
                                   "expired": False, "unreadable": False},
            legal_disqualification_answer=kw.get("legal_disq", False),
            self_declaration_submitted=kw.get("self_decl", True),
            normalized_profile={
                "has_high_language": kw.get("lang_high", False),
                "is_patriot_top": kw.get("patriot", False),
            },
        )

    return {
        "C001": p("C001", EducationLevel.MASTER, 5.0, certs=["A_GRADE"], lang_high=True),
        "C002": p("C002", EducationLevel.HIGH_SCHOOL, 4.0),
        "C003": p("C003", EducationLevel.MASTER, 6.0, missing_doc=True),
        "C004": p("C004", EducationLevel.DOCTORATE, 8.0, legal_disq=True),
        "C005": p("C005", EducationLevel.HIGH_SCHOOL, 1.0, legal_disq=True, missing_doc=True),
        "C006": p("C006", EducationLevel.HIGH_SCHOOL, 2.0, missing_doc=True),
        "C007": p("C007", EducationLevel.MASTER, 4.0),
        "C008": p("C008", EducationLevel.DOCTORATE, 7.0,
                  certs=["A_GRADE", "B_GRADE"], lang_high=True),
        "C009": p("C009", EducationLevel.BACHELOR, 3.0),
        "C010": p("C010", EducationLevel.MASTER, 4.0, certs=["A_GRADE"], patriot=True),
    }


# ---- 데모 ------------------------------------------------------------------
def main():
    print("=" * 90)
    print("KSA 룰 평가 엔진 — 시뮬레이션 10명 데모")
    print("=" * 90)

    job, glob = build_rule_sets()
    bonus_set = build_bonus_rule_set()
    candidates = build_candidates()

    screening = ScreeningEngine()
    bonus = BonusEngine()

    # ---- 결격 자동판정 -----------------------------------------------------
    print("\n[1] 결격 자동판정 결과")
    print(f"{'No':<6}{'D1':<5}{'D2':<5}{'D3':<5}{'추천':<8}{'트리거 룰'}")
    print("-" * 90)
    for no in sorted(candidates):
        r = screening.screen(candidates[no], [job, glob])
        triggered = []
        for code in ("D1", "D2", "D3"):
            triggered.extend([rl["code"] for rl in r.rule_evidence[code]["rules"]])
        d1 = "✓" if r.d1_triggered else "·"
        d2 = "✓" if r.d2_triggered else "·"
        d3 = "✓" if r.d3_triggered else "·"
        print(f"{no:<6}{d1:<5}{d2:<5}{d3:<5}{r.recommended_decision.value:<8}"
              f"{', '.join(triggered) if triggered else '-'}")

    # ---- 가점 계산 (PASS 추천 + 모든 후보자) -------------------------------
    print("\n[2] 가점 계산 결과 (서류 단계)")
    print(f"{'No':<6}{'학력':<14}{'적용 가점':<12}{'세부 (적용/계산)'}")
    print("-" * 90)
    for no in sorted(candidates):
        result = bonus.calculate(candidates[no], bonus_set)
        if not result.items:
            continue
        edu = candidates[no].education_level.value
        details = []
        for item in result.items:
            mark = "✓" if item.status.value == "APPROVED" else "✗"
            details.append(
                f"{mark}{item.bonus_rule_code}({item.applied_score}/{item.calculated_score})"
            )
        print(f"{no:<6}{edu:<14}{str(result.total_doc_bonus):<12}{' '.join(details)}")

    # ---- 블라인드 탐지 (C007 + C001 비교) ---------------------------------
    print("\n[3] 블라인드 위배 탐지 (C007 vs C001)")
    detector = BlindDetector()

    c007_narrative = CandidateNarrative(
        candidate_id=UUID(int=7),
        cover_letter="저는 서울대학교 컴퓨터공학과를 졸업하고 4년간 AI 분야에서 일했습니다. "
                     "부산 출신으로 어머니께서 교사로 재직하시며 학업을 지원해 주셨습니다.",
        career_history="서울대학교 졸업 후 부산에서 4년간 근무했습니다.",
    )
    r = detector.detect(c007_narrative)
    print(f"\nC007 탐지 건수: {r.detection_count}")
    print(f"  카테고리별: {r.detection_summary['by_category']}")
    print(f"  마스킹 결과 (cover_letter):")
    print(f"    {r.cover_letter_masked}")

    c001_narrative = CandidateNarrative(
        candidate_id=UUID(int=1),
        cover_letter="AI 연구에 5년간 매진해 왔습니다.",
        career_history="5년간 다양한 AI 프로젝트를 수행했습니다.",
    )
    r = detector.detect(c001_narrative)
    print(f"\nC001 탐지 건수: {r.detection_count} (위배 없음)")

    # ---- PII 스크럽 데모 --------------------------------------------------
    print("\n[4] PII 스크럽 데모")
    scrubber = PIIScrubber()
    sample = ("안녕하세요. 저는 김무결이고, 연락처는 010-1234-5678입니다. "
              "이메일은 jeeyoung@ksa.or.kr로 보내주세요.")
    res = scrubber.scrub(sample)
    print(f"  원본:    {sample}")
    print(f"  스크럽:  {res.input_scrubbed}")
    print(f"  탐지:    {len(res.detected_pii)}건  passed={res.passed}")

    print("\n" + "=" * 90)
    print("데모 종료. (단위 테스트는 pytest tests/ 로 실행)")
    print("=" * 90)


if __name__ == "__main__":
    main()
