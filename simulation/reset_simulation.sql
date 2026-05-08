-- =====================================================================
-- SIMULATION 데이터만 정리 (시드 데이터는 보존)
-- 시뮬레이션을 다시 실행하고 싶을 때 사용
-- =====================================================================

\set ON_ERROR_STOP on

BEGIN;

\echo '시뮬레이션 데이터 삭제 시작...'

-- 시뮬레이션에서 만든 사이클 ID
\set sim_cycle '11111111-1111-1111-1111-111111111111'

-- 1. 종속 데이터부터 역순으로 삭제 (FK 제약조건 회피)

-- 가점 관련
DELETE FROM bonus_approvals WHERE bonus_calculation_id IN (
    SELECT bc.id FROM bonus_calculations bc
    JOIN candidates c ON c.id = bc.candidate_id
    WHERE c.cycle_id = :'sim_cycle'::uuid
);
DELETE FROM bonus_evidences WHERE bonus_calculation_id IN (
    SELECT bc.id FROM bonus_calculations bc
    JOIN candidates c ON c.id = bc.candidate_id
    WHERE c.cycle_id = :'sim_cycle'::uuid
);
DELETE FROM bonus_calculations WHERE candidate_id IN (
    SELECT id FROM candidates WHERE cycle_id = :'sim_cycle'::uuid
);
DELETE FROM interview_bonuses WHERE candidate_id IN (
    SELECT id FROM candidates WHERE cycle_id = :'sim_cycle'::uuid
);

-- 면접 관련
DELETE FROM interview_scores WHERE evaluation_id IN (
    SELECT ie.id FROM interview_evaluations ie
    JOIN interview_sessions s ON s.id = ie.session_id
    JOIN candidates c ON c.id = s.candidate_id
    WHERE c.cycle_id = :'sim_cycle'::uuid
);
DELETE FROM interview_evaluations WHERE session_id IN (
    SELECT s.id FROM interview_sessions s
    JOIN candidates c ON c.id = s.candidate_id
    WHERE c.cycle_id = :'sim_cycle'::uuid
);
DELETE FROM interview_sessions WHERE candidate_id IN (
    SELECT id FROM candidates WHERE cycle_id = :'sim_cycle'::uuid
);
DELETE FROM interview_questions WHERE question_set_id IN (
    SELECT qs.id FROM interview_question_sets qs
    JOIN candidates c ON c.id = qs.candidate_id
    WHERE c.cycle_id = :'sim_cycle'::uuid
);
DELETE FROM interview_question_sets WHERE candidate_id IN (
    SELECT id FROM candidates WHERE cycle_id = :'sim_cycle'::uuid
);

-- LLM·PII 로그
DELETE FROM pii_scrub_logs WHERE candidate_id IN (
    SELECT id FROM candidates WHERE cycle_id = :'sim_cycle'::uuid
);
DELETE FROM llm_call_logs WHERE candidate_id IN (
    SELECT id FROM candidates WHERE cycle_id = :'sim_cycle'::uuid
);

-- 블라인드
DELETE FROM blind_reviews WHERE candidate_id IN (
    SELECT id FROM candidates WHERE cycle_id = :'sim_cycle'::uuid
);
DELETE FROM blind_detections WHERE candidate_id IN (
    SELECT id FROM candidates WHERE cycle_id = :'sim_cycle'::uuid
);

-- 검토 결정
DELETE FROM human_decisions WHERE candidate_id IN (
    SELECT id FROM candidates WHERE cycle_id = :'sim_cycle'::uuid
);

-- 자동판정
DELETE FROM screening_recommendations WHERE candidate_id IN (
    SELECT id FROM candidates WHERE cycle_id = :'sim_cycle'::uuid
);

-- 후보자 데이터
DELETE FROM candidate_narratives WHERE candidate_id IN (
    SELECT id FROM candidates WHERE cycle_id = :'sim_cycle'::uuid
);
DELETE FROM candidate_profiles WHERE candidate_id IN (
    SELECT id FROM candidates WHERE cycle_id = :'sim_cycle'::uuid
);
DELETE FROM candidate_pii WHERE candidate_id IN (
    SELECT id FROM candidates WHERE cycle_id = :'sim_cycle'::uuid
);
DELETE FROM candidates WHERE cycle_id = :'sim_cycle'::uuid;

-- 공고·사이클
DELETE FROM job_postings WHERE cycle_id = :'sim_cycle'::uuid;
DELETE FROM recruitment_cycles WHERE id = :'sim_cycle'::uuid;

\echo '시뮬레이션 데이터 정리 완료. 시드 데이터는 보존됨.'

COMMIT;

-- 확인
SELECT
    (SELECT count(*) FROM candidates WHERE cycle_id = :'sim_cycle'::uuid) AS remaining_candidates,
    (SELECT count(*) FROM rule_sets) AS rule_sets_kept,
    (SELECT count(*) FROM bonus_rules) AS bonus_rules_kept;
