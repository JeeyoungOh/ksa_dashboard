"""
PostgreSQL ENUM 타입을 SQLAlchemy로 노출.

DDL이 ENUM을 이미 만들어 두었으므로 ORM에서는 create_type=False로 매핑만.
"""
from __future__ import annotations
from sqlalchemy.dialects.postgresql import ENUM


# ---- 후보자 상태 흐름 ENUM -------------------------------------------------
candidate_status_enum = ENUM(
    "IMPORTED", "NORMALIZED", "AUTO_SCREENED",
    "DOC_PASS", "DOC_FAIL",
    "INTERVIEW_TARGET", "INTERVIEW_QUESTIONS_READY", "INTERVIEW_EVALUATED",
    "FINAL_APPROVED", "FINAL_REJECTED", "SCORE_APPROVED",
    name="candidate_status",
    create_type=False,
)

# ---- 결정 단계/값 ---------------------------------------------------------
decision_step_enum = ENUM(
    "DOC_SCREENING", "BLIND_REVIEW",
    "INTERVIEW_FINAL", "BONUS_APPROVAL",
    name="decision_step",
    create_type=False,
)

decision_value_enum = ENUM(
    "PASS", "HOLD", "HOLD_AGAIN", "FAIL",
    "MASKING_PASS", "RESUBMIT_REQUIRED", "REJECT",
    name="decision_value",
    create_type=False,
)

# ---- 학력 -----------------------------------------------------------------
education_level_enum = ENUM(
    "HIGH_SCHOOL", "ASSOCIATE", "BACHELOR", "MASTER", "DOCTORATE",
    name="education_level",
    create_type=False,
)

# ---- 룰셋 / 룰 그룹 -------------------------------------------------------
rule_scope_enum = ENUM(
    "GLOBAL", "JOB", "CYCLE",
    name="rule_scope",
    create_type=False,
)

# ---- 가점 상태 ------------------------------------------------------------
bonus_status_enum = ENUM(
    "PENDING_EVIDENCE", "PENDING_APPROVAL", "APPROVED", "REJECTED",
    name="bonus_status",
    create_type=False,
)

# ---- 사용자 권한 ----------------------------------------------------------
user_role_enum = ENUM(
    "ADMIN", "REVIEWER", "INTERVIEWER", "APPROVER", "VIEWER",
    name="user_role",
    create_type=False,
)
