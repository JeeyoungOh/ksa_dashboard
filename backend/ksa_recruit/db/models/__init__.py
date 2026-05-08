"""
ORM 모델 한 곳에서 import.

Alembic이 메타데이터를 발견할 수 있도록 모든 모델 모듈을 import해 둠.
"""
from .setup import (
    User, RuleSet, RuleGroup, RuleItem,
    RecruitmentCycle, JobPosting,
)
from .candidate import (
    Candidate, CandidateProfile, CandidateNarrative,
)
from .screening import ScreeningRecommendation

__all__ = [
    "User",
    "RuleSet", "RuleGroup", "RuleItem",
    "RecruitmentCycle", "JobPosting",
    "Candidate", "CandidateProfile", "CandidateNarrative",
    "ScreeningRecommendation",
]
