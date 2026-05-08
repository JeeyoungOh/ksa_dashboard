-- =====================================================================
-- SIMULATION 03: 1차 검토자 결정
-- =====================================================================

DO $$
DECLARE
    v_reviewer UUID;
    v_approver UUID;
BEGIN
    SELECT id INTO v_reviewer FROM users WHERE role = 'REVIEWER' LIMIT 1;
    SELECT id INTO v_approver FROM users WHERE role = 'APPROVER' LIMIT 1;

    -- C001: PASS 추천 → PASS 확정
    INSERT INTO human_decisions (candidate_id, reviewer_id, step, decision, decided_at)
    VALUES ('aaaaaaaa-0001-0000-0000-000000000000'::uuid,
            v_reviewer, 'DOC_SCREENING', 'PASS', NOW());

    -- C002: HOLD → FAIL
    INSERT INTO human_decisions (candidate_id, reviewer_id, step, decision, reason, reason_required, decided_at)
    VALUES ('aaaaaaaa-0002-0000-0000-000000000000'::uuid,
            v_reviewer, 'DOC_SCREENING', 'FAIL',
            '학력 미달은 회복 불가 사유로 탈락 처리', TRUE, NOW());

    -- C003: HOLD → HOLD_AGAIN (서류 보완 요청)
    INSERT INTO human_decisions (candidate_id, reviewer_id, step, decision, reason, hold_again_count, decided_at)
    VALUES ('aaaaaaaa-0003-0000-0000-000000000000'::uuid,
            v_reviewer, 'DOC_SCREENING', 'HOLD_AGAIN',
            '자기소개서·경력기술서 미제출. 보완 요청', 1, NOW());

    -- C003 보완 후 재검토 → PASS
    INSERT INTO human_decisions (candidate_id, reviewer_id, step, decision, reason,
                                  previous_decision_id, hold_again_count, decided_at)
    SELECT 'aaaaaaaa-0003-0000-0000-000000000000'::uuid,
           v_reviewer, 'DOC_SCREENING', 'PASS', '서류 보완 완료 확인',
           hd.id, 1, NOW() + INTERVAL '2 days'
    FROM human_decisions hd
    WHERE hd.candidate_id = 'aaaaaaaa-0003-0000-0000-000000000000'::uuid
      AND hd.decision = 'HOLD_AGAIN' LIMIT 1;

    UPDATE candidate_profiles SET
        submitted_documents = '["application_form","self_intro","career_history"]'::jsonb,
        attachment_checklist = '{"missing_required":false,"expired":false,"unreadable":false}'::jsonb
    WHERE candidate_id = 'aaaaaaaa-0003-0000-0000-000000000000'::uuid;

    UPDATE candidate_narratives SET
        cover_letter = '6년간 데이터 사이언스 분야에서 다양한 프로젝트를 수행했습니다.'
    WHERE candidate_id = 'aaaaaaaa-0003-0000-0000-000000000000'::uuid;

    -- C004: HOLD → FAIL
    INSERT INTO human_decisions (candidate_id, reviewer_id, step, decision, reason, reason_required, decided_at)
    VALUES ('aaaaaaaa-0004-0000-0000-000000000000'::uuid,
            v_reviewer, 'DOC_SCREENING', 'FAIL',
            '자기신고서상 법적 결격 사유 확인', TRUE, NOW());

    -- C005: FAIL (AUTO_FAIL 추천) → 승인자가 FAIL 확정
    INSERT INTO human_decisions (candidate_id, reviewer_id, step, decision, reason, decided_at)
    VALUES ('aaaaaaaa-0005-0000-0000-000000000000'::uuid,
            v_approver, 'DOC_SCREENING', 'FAIL',
            '결격사유 3종 모두 해당 (AUTO_FAIL 추천 확인)', NOW());

    -- C006: HOLD → FAIL
    INSERT INTO human_decisions (candidate_id, reviewer_id, step, decision, reason, reason_required, decided_at)
    VALUES ('aaaaaaaa-0006-0000-0000-000000000000'::uuid,
            v_reviewer, 'DOC_SCREENING', 'FAIL',
            '학력 미달 + 서류 누락', TRUE, NOW());

    -- C007~C010: PASS
    INSERT INTO human_decisions (candidate_id, reviewer_id, step, decision, decided_at)
    VALUES
        ('aaaaaaaa-0007-0000-0000-000000000000'::uuid, v_reviewer, 'DOC_SCREENING', 'PASS', NOW()),
        ('aaaaaaaa-0008-0000-0000-000000000000'::uuid, v_reviewer, 'DOC_SCREENING', 'PASS', NOW()),
        ('aaaaaaaa-0009-0000-0000-000000000000'::uuid, v_reviewer, 'DOC_SCREENING', 'PASS', NOW()),
        ('aaaaaaaa-0010-0000-0000-000000000000'::uuid, v_reviewer, 'DOC_SCREENING', 'PASS', NOW());
END$$;

-- 상태 업데이트
UPDATE candidates SET status = 'DOC_PASS', updated_at = NOW()
WHERE id IN (
    SELECT candidate_id FROM (
        SELECT DISTINCT ON (candidate_id) candidate_id, decision
        FROM human_decisions
        WHERE step = 'DOC_SCREENING'
        ORDER BY candidate_id, decided_at DESC
    ) latest WHERE decision = 'PASS'
);

UPDATE candidates SET status = 'DOC_FAIL', updated_at = NOW()
WHERE id IN (
    SELECT candidate_id FROM (
        SELECT DISTINCT ON (candidate_id) candidate_id, decision
        FROM human_decisions
        WHERE step = 'DOC_SCREENING'
        ORDER BY candidate_id, decided_at DESC
    ) latest WHERE decision = 'FAIL'
);

SELECT
    c.candidate_no,
    sr.recommended_decision AS recommendation,
    (SELECT hd.decision FROM human_decisions hd
     WHERE hd.candidate_id = c.id AND hd.step = 'DOC_SCREENING'
     ORDER BY hd.decided_at DESC LIMIT 1) AS final_decision,
    c.status,
    (SELECT count(*) FROM human_decisions hd
     WHERE hd.candidate_id = c.id AND hd.step = 'DOC_SCREENING') AS decision_count
FROM candidates c
JOIN screening_recommendations sr ON sr.candidate_id = c.id
WHERE c.cycle_id = '11111111-1111-1111-1111-111111111111'::uuid
ORDER BY c.candidate_no;
