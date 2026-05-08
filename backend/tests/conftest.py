"""
공통 테스트 픽스처.

시뮬레이션에서 사용한 10명 후보자 + 동일한 룰셋·가점 룰셋을 Python 객체로 재구성.
SQL 시뮬레이션과 같은 결과가 나오는지 검증하는 것이 목표.
"""
from __future__ import annotations
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from ksa_recruit.domain.enums import (
    EducationLevel, RuleScope, RuleGroupCode,
)
from ksa_recruit.domain.models import (
    CandidateProfile, CandidateNarrative,
    RuleItem, RuleGroup, RuleSet,
    BonusRule, BonusRuleSet,
)


# =========================================================================
# 룰셋 (JOB)
# =========================================================================
@pytest.fixture
def rule_set_job() -> RuleSet:
    """JOB 스코프 룰셋 - 시뮬레이션 SQL의 JOB_DEFAULT_2026_V1과 동일한 의미."""
    d1 = RuleGroup(
        id=uuid4(),
        code=RuleGroupCode.D1,
        name="응시자격 미충족",
        items=[
            RuleItem(
                id=uuid4(),
                code="D1_EDU_MIN",
                name="최소 학력 요건 (학사 이상)",
                operator="not_in",
                field_path="education_level",
                expected_value=["BACHELOR", "MASTER", "DOCTORATE"],
            ),
            RuleItem(
                id=uuid4(),
                code="D1_CAREER_MIN",
                name="최소 경력 요건 (3년 이상)",
                operator="lt",
                field_path="career_years",
                expected_value=3,
            ),
        ],
    )
    d2 = RuleGroup(
        id=uuid4(),
        code=RuleGroupCode.D2,
        name="필수서류 불비",
        items=[
            RuleItem(
                id=uuid4(),
                code="D2_MISSING_DOC",
                name="필수서류 누락",
                operator="is_true",
                field_path="attachment_checklist.missing_required",
                expected_value=True,
            ),
            RuleItem(
                id=uuid4(),
                code="D2_EXPIRED_DOC",
                name="서류 기한초과",
                operator="is_true",
                field_path="attachment_checklist.expired",
                expected_value=True,
            ),
            RuleItem(
                id=uuid4(),
                code="D2_UNREADABLE",
                name="서류 식별불가",
                operator="is_true",
                field_path="attachment_checklist.unreadable",
                expected_value=True,
            ),
        ],
    )
    return RuleSet(
        id=uuid4(),
        code="JOB_DEFAULT_2026_V1",
        name="JOB 기본 룰셋",
        scope=RuleScope.JOB,
        version=1,
        groups=[d1, d2],
    )


@pytest.fixture
def rule_set_global() -> RuleSet:
    """GLOBAL 스코프 룰셋 - D3 (법적 결격) 담당."""
    d3 = RuleGroup(
        id=uuid4(),
        code=RuleGroupCode.D3,
        name="법적 결격 자기신고",
        items=[
            RuleItem(
                id=uuid4(),
                code="D3_SELF_DECLARED",
                name="법적 결격 자기신고 해당",
                operator="is_true",
                field_path="legal_disqualification_answer",
                expected_value=True,
            ),
            RuleItem(
                id=uuid4(),
                code="D3_NOT_SUBMITTED",
                name="자기신고서 미제출",
                operator="is_false",
                field_path="self_declaration_submitted",
                expected_value=False,
            ),
        ],
    )
    return RuleSet(
        id=uuid4(),
        code="GLOBAL_LEGAL_DISQUAL_2026",
        name="GLOBAL 법적 결격 룰셋",
        scope=RuleScope.GLOBAL,
        version=1,
        groups=[d3],
    )


# =========================================================================
# 가점 룰셋 (시뮬레이션 SQL의 KSA_BONUS_MVP_2026과 동일한 의미)
# =========================================================================
@pytest.fixture
def bonus_rule_set() -> BonusRuleSet:
    rules = [
        BonusRule(
            id=uuid4(), code="BONUS_PHD", name="박사학위",
            score_value=Decimal("5"), operator="eq",
            field_path="education_level", expected_value="DOCTORATE",
            exclusive_group="EDUCATION",
        ),
        BonusRule(
            id=uuid4(), code="BONUS_MASTER", name="석사학위",
            score_value=Decimal("3"), operator="eq",
            field_path="education_level", expected_value="MASTER",
            exclusive_group="EDUCATION",
        ),
        BonusRule(
            id=uuid4(), code="BONUS_CERT_A", name="직무관련 자격증 A급",
            score_value=Decimal("3"), operator="contains",
            field_path="certifications", expected_value="A_GRADE",
        ),
        BonusRule(
            id=uuid4(), code="BONUS_CERT_B", name="직무관련 자격증 B급",
            score_value=Decimal("1"), operator="contains",
            field_path="certifications", expected_value="B_GRADE",
        ),
        BonusRule(
            id=uuid4(), code="BONUS_LANG_HIGH", name="어학 고급",
            score_value=Decimal("2"), operator="is_true",
            # 시뮬레이션의 language_tests JSON 매칭 대신 normalized_profile 플래그 사용
            field_path="normalized_profile.has_high_language",
            expected_value=True,
            exclusive_group="LANGUAGE",
        ),
        BonusRule(
            id=uuid4(), code="BONUS_PATRIOT_10", name="국가유공자 10%",
            score_value=Decimal("10"), operator="is_true",
            field_path="normalized_profile.is_patriot_top",
            expected_value=True,
            exclusive_group="PATRIOT",
        ),
    ]
    return BonusRuleSet(
        id=uuid4(),
        code="KSA_BONUS_MVP_2026",
        name="KSA MVP 가점 룰셋",
        version=1,
        max_bonus_score=Decimal("10"),
        rules=rules,
    )


# =========================================================================
# 후보자 10명 (시뮬레이션 SQL의 candidates와 동일)
# =========================================================================
def _profile(
    candidate_no: str,
    edu: EducationLevel,
    career: float,
    legal_disq: bool = False,
    self_decl: bool = True,
    missing_doc: bool = False,
    certifications: list[str] | None = None,
    language_high: bool = False,
    is_patriot: bool = False,
) -> CandidateProfile:
    return CandidateProfile(
        candidate_id=UUID(int=int(candidate_no[1:])),
        candidate_no=candidate_no,
        job_code="AI_RESEARCHER",
        education_level=edu,
        career_years=Decimal(str(career)),
        certifications=certifications or [],
        language_tests=[],
        submitted_documents=["application_form"]
            if missing_doc
            else ["application_form", "self_intro", "career_history"],
        attachment_checklist={
            "missing_required": missing_doc,
            "expired": False,
            "unreadable": False,
        },
        legal_disqualification_answer=legal_disq,
        self_declaration_submitted=self_decl,
        normalized_profile={
            "has_high_language": language_high,
            "is_patriot_top": is_patriot,
        },
    )


@pytest.fixture
def candidates() -> dict[str, CandidateProfile]:
    """시뮬레이션 SQL과 동일한 10명."""
    return {
        "C001": _profile("C001", EducationLevel.MASTER, 5.0,
                         certifications=["A_GRADE"], language_high=True),
        "C002": _profile("C002", EducationLevel.HIGH_SCHOOL, 4.0),
        "C003": _profile("C003", EducationLevel.MASTER, 6.0, missing_doc=True),
        "C004": _profile("C004", EducationLevel.DOCTORATE, 8.0, legal_disq=True),
        "C005": _profile("C005", EducationLevel.HIGH_SCHOOL, 1.0,
                         legal_disq=True, missing_doc=True),
        "C006": _profile("C006", EducationLevel.HIGH_SCHOOL, 2.0, missing_doc=True),
        "C007": _profile("C007", EducationLevel.MASTER, 4.0),
        "C008": _profile("C008", EducationLevel.DOCTORATE, 7.0,
                         certifications=["A_GRADE", "B_GRADE"], language_high=True),
        "C009": _profile("C009", EducationLevel.BACHELOR, 3.0),
        "C010": _profile("C010", EducationLevel.MASTER, 4.0,
                         certifications=["A_GRADE"], is_patriot=True),
    }


# =========================================================================
# 자유서술 (블라인드 탐지용)
# =========================================================================
@pytest.fixture
def narrative_with_violations() -> CandidateNarrative:
    """C007 시나리오 - 학교·지역·가족 노출."""
    return CandidateNarrative(
        candidate_id=UUID(int=7),
        cover_letter=(
            "저는 서울대학교 컴퓨터공학과를 졸업하고 4년간 AI 분야에서 일했습니다. "
            "부산 출신으로 어머니께서 교사로 재직하시며 학업을 지원해 주셨습니다."
        ),
        career_history="서울대학교 졸업 후 부산에서 4년간 근무했습니다.",
    )


@pytest.fixture
def narrative_clean() -> CandidateNarrative:
    """C001 시나리오 - 위배 없음."""
    return CandidateNarrative(
        candidate_id=UUID(int=1),
        cover_letter=(
            "AI 연구에 5년간 매진해 왔습니다. "
            "자연어처리와 추천시스템 분야에서 다수의 프로젝트를 수행했습니다."
        ),
        career_history="5년간 다양한 AI 프로젝트를 수행했습니다.",
    )
