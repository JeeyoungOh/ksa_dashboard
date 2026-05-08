"""
ScreeningService — 결격 자동판정 실행.

흐름:
  1) 후보자 + 프로필 로딩
  2) 적용 룰셋 결정 (JOB 룰셋 + 활성 GLOBAL 룰셋들)
  3) ScreeningEngine 실행
  4) screening_recommendations INSERT/UPDATE (upsert)
  5) candidates.status = 'AUTO_SCREENED' 갱신

호출자(API 라우터)가 commit 책임.
"""
from __future__ import annotations
from uuid import UUID

from sqlalchemy.orm import Session

from ..db import models, mappers
from ..engines.screening import ScreeningEngine
from ..repositories.candidate import CandidateRepository
from ..repositories.rule_set import (
    RuleSetRepository, JobPostingRepository, ScreeningRepository,
)


class CandidateNotFound(LookupError):
    pass


class JobPostingNotFound(LookupError):
    pass


class NoApplicableRuleSet(ValueError):
    pass


class ScreeningService:
    def __init__(
        self,
        session: Session,
        engine: ScreeningEngine | None = None,
    ) -> None:
        self.session = session
        self.engine = engine or ScreeningEngine()
        self.candidate_repo = CandidateRepository(session)
        self.rule_set_repo = RuleSetRepository(session)
        self.posting_repo = JobPostingRepository(session)
        self.screening_repo = ScreeningRepository(session)

    # ------------------------------------------------------------------

    def run(self, candidate_id: UUID) -> models.ScreeningRecommendation:
        """단일 후보자에 대해 결격 자동판정 실행."""
        candidate = self.candidate_repo.get(candidate_id)
        if candidate is None:
            raise CandidateNotFound(f"candidate {candidate_id}")

        # 1. 적용 룰셋 결정
        applied_rule_sets_orm = self._resolve_rule_sets(candidate)
        if not applied_rule_sets_orm:
            raise NoApplicableRuleSet(
                f"candidate {candidate_id}: 적용할 활성 룰셋이 없음"
            )

        # 2. ORM → 도메인 변환
        domain_profile = mappers.to_domain_profile(candidate)
        domain_rule_sets = [mappers.to_domain_rule_set(rs) for rs in applied_rule_sets_orm]

        # 3. 룰 엔진 실행
        result = self.engine.screen(domain_profile, domain_rule_sets)

        # 4. ORM 객체로 직렬화
        rec_orm = models.ScreeningRecommendation(
            candidate_id=candidate.id,
            applied_rule_sets=result.applied_rule_sets,
            d1_triggered=result.d1_triggered,
            d2_triggered=result.d2_triggered,
            d3_triggered=result.d3_triggered,
            recommended_decision=result.recommended_decision.value,
            rule_evidence=result.rule_evidence,
            input_snapshot=result.input_snapshot,
            evaluator_version=result.evaluator_version,
        )

        # 5. upsert + 후보자 상태 갱신
        saved = self.screening_repo.upsert(rec_orm)
        candidate.status = "AUTO_SCREENED"
        self.session.flush()
        return saved

    # ------------------------------------------------------------------

    def _resolve_rule_sets(
        self, candidate: models.Candidate
    ) -> list[models.RuleSet]:
        """
        적용 룰셋 결정 정책:
          - JobPosting.rule_set_id가 가리키는 JOB 룰셋 1개
          - 모든 활성 GLOBAL 룰셋 (D3 같은 공통 결격)
        나중에 CYCLE 스코프 활성화 시 여기에 추가.
        """
        result: list[models.RuleSet] = []

        # JOB 룰셋
        posting = self.posting_repo.get(candidate.posting_id)
        if posting is None:
            raise JobPostingNotFound(f"posting {candidate.posting_id}")
        if posting.rule_set_id is not None:
            job_rule_set = self.rule_set_repo.get(posting.rule_set_id)
            if job_rule_set is not None and job_rule_set.is_active:
                result.append(job_rule_set)

        # GLOBAL 룰셋 (모두 적용)
        global_sets = self.rule_set_repo.get_active_by_scope("GLOBAL")
        result.extend(global_sets)

        return result
