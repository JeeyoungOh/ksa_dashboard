"""
PostgreSQL ENUM 타입 정의.

실제 DB의 ENUM 타입과 1:1 매핑. SQLAlchemy 측 검증용.
"""
from __future__ import annotations
from sqlalchemy.dialects.postgresql import ENUM


# 룰 관련
rule_scope_enum = ENUM(
    "GLOBAL", "JOB", "CYCLE",
    name="rule_scope", create_type=False,
)
rule_set_status_enum = ENUM(
    "DRAFT", "ACTIVE", "INACTIVE", "ARCHIVED",
    name="rule_set_status", create_type=False,
)
rule_operator_enum = ENUM(
    "ALL", "ANY",
    name="rule_operator", create_type=False,
)
decision_value_enum = ENUM(
    "PASS", "FAIL", "HOLD", "AUTO_FAIL",
    name="decision_value", create_type=False,
)

# 사이클·후보자
cycle_type_enum = ENUM(
    "ANNUAL", "QUARTERLY", "ADHOC",
    name="cycle_type", create_type=False,
)
cycle_status_enum = ENUM(
    "DRAFT", "OPEN", "CLOSED", "ARCHIVED",
    name="cycle_status", create_type=False,
)
candidate_status_enum = ENUM(
    "IMPORTED", "NORMALIZED", "AUTO_SCREENED", "DOC_REVIEWED",
    "BLIND_REVIEWED", "INTERVIEW_PASSED", "FINAL_PASSED", "REJECTED",
    name="candidate_status", create_type=False,
)
education_level_enum = ENUM(
    "HIGH_SCHOOL", "ASSOCIATE", "BACHELOR", "MASTER", "DOCTORATE",
    name="education_level", create_type=False,
)
