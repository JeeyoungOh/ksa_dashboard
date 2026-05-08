"""
DB ENUM 타입과 1:1 매핑되는 Python ENUM.
PostgreSQL 측 ENUM 변경 시 여기도 함께 수정.
"""
from enum import Enum


class EducationLevel(str, Enum):
    HIGH_SCHOOL = "HIGH_SCHOOL"
    ASSOCIATE = "ASSOCIATE"
    BACHELOR = "BACHELOR"
    MASTER = "MASTER"
    DOCTORATE = "DOCTORATE"


class DecisionValue(str, Enum):
    PASS_ = "PASS"
    HOLD = "HOLD"
    HOLD_AGAIN = "HOLD_AGAIN"
    FAIL = "FAIL"


class RuleScope(str, Enum):
    GLOBAL = "GLOBAL"
    JOB = "JOB"
    CYCLE = "CYCLE"


class RuleGroupCode(str, Enum):
    """결격 사유 분류 - D1/D2/D3"""
    D1 = "D1"   # 응시자격 미충족 (학력·경력 등)
    D2 = "D2"   # 필수서류 불비
    D3 = "D3"   # 법적 결격 자기신고


class BonusStatus(str, Enum):
    PENDING_EVIDENCE = "PENDING_EVIDENCE"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class BlindCategory(str, Enum):
    """블라인드 위배 카테고리 (KSA 9개 항목)"""
    PERSONAL_ID = "personal_id"        # 이름·생년월일·주민번호
    SCHOOL = "school"                  # 학교명
    REGION = "region"                  # 출신 지역
    GENDER = "gender"                  # 성별
    AGE = "age"                        # 나이
    FAMILY = "family"                  # 가족 관계
    APPEARANCE = "appearance"          # 외모·키·체중
    RELIGION = "religion"              # 종교
    POLITICS = "politics"              # 정치 성향


class DetectorLayer(str, Enum):
    RULE_DICT = "RULE_DICT"
    NER_MODEL = "NER_MODEL"
    LLM_HEURISTIC = "LLM_HEURISTIC"
