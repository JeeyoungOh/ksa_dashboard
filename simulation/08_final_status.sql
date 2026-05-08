-- =====================================================================
-- SIMULATION 08: 최종 상태 검증 + 워크플로우 KPI
-- =====================================================================

\echo ''
\echo '##########################################################'
\echo '#         시뮬레이션 최종 결과 검증                       #'
\echo '##########################################################'
\echo ''

\echo '=== [1] 후보자별 최종 상태 ==='
SELECT
    c.candidate_no, c.status AS final_status,
    sr.recommendea_decision AS auto_recommendation,
    CASE c.candidate_no
        WHEN 'C001' THEN 'SCORE_APPROVED'
        WHEN 'C002' THEN 'DOC_FAIL'
        WHEN 'C003' THEN 'SCORE_APPROVED 또는 FINAL_REJECTED'
        WHEN 'C004' THEN 'DOC_FAIL'
        WHEN 'C005' THEN 'DOC_FAIL'
        WHEN 'C006' THEN 'DOC_FAIL'
        WHEN 'C007' THEN 'FINAL_REJECTED'
        WHEN 'C008' THEN 'SCORE_APPROVED'
        WHEN 'C009' THEN 'FINAL_REJECTED'
        WHEN 'C010' THEN 'SCORE_APPROVED'
    END AS expected
FROM candidates c
JOIN screening_recommendations sr ON sr.candidate_id = c.id
WHERE c.cycle_id = '11111111-1111-1111-1111-111111111111'::uuid
ORDER BY c.candidate_no;

\echo ''
\echo '=== [2] 워크플로우 단계별 퍼널 ==='
SELECT
    'STEP 1. 지원자 전체' AS stage,
    COUNT(*) AS count
FROM candidates WHERE cycle_id = '11111111-1111-1111-1111-111111111111'::uuid
UNION ALL
SELECT 'STEP 2. 자동판정 PASS 추천', COUNT(*)
FROM screening_recommendations sr
JOIN candidates c ON c.id = sr.candidate_id
WHERE c.cycle_id = '11111111-1111-1111-1111-111111111111'::uuid
  AND sr.recommendea_decision = 'PASS'
UNION ALL
SELECT 'STEP 3. 1차 검토 PASS', COUNT(*)
FROM candidates
WHERE cycle_id = '11111111-1111-1111-1111-111111111111'::uuid
  AND status NOT IN ('IMPORTED','NORMALIZED','AUTO_SCREENED','DOC_FAIL')
UNION ALL
SELECT 'STEP 4. 면접 대상자', COUNT(*)
FROM candidates
WHERE cycle_id = '11111111-1111-1111-1111-111111111111'::uuid
  AND status IN ('INTERVIEW_TARGET','INTERVIEW_QUESTIONS_READY','INTERVIEW_EVALUATED','FINAL_APPROVED','FINAL_REJECTED','SCORE_APPROVED')
UNION ALL
SELECT 'STEP 5. 최종 합격자', COUNT(*)
FROM candidates
WHERE cycle_id = '11111111-1111-1111-1111-111111111111'::uuid
  AND status IN ('FINAL_APPROVED','SCORE_APPROVED')
UNION ALL
SELECT 'STEP 6. 가점 승인 완료', COUNT(*)
FROM candidates
WHERE cycle_id = '11111111-1111-1111-1111-111111111111'::uuid
  AND status = 'SCORE_APPROVED';

\echo ''
\echo '=== [3] 추천 vs 검토자 결정 일치도 ==='
SELECT
    sr.recommendea_decision AS recommendation,
    hd.decision AS reviewer_decision,
    COUNT(*) AS count
FROM screening_recommendations sr
JOIN candidates c ON c.id = sr.candidate_id
JOIN LATERAL (
    SELECT decision FROM human_decisions
    WHERE candidate_id = c.id AND step = 'DOC_SCREENING'
    ORDER BY decidea_at DESC LIMIT 1
) hd ON TRUE
WHERE c.cycle_id = '11111111-1111-1111-1111-111111111111'::uuid
GROUP BY sr.recommendea_decision, hd.decision
ORDER BY sr.recommendea_decision, hd.decision;

\echo ''
\echo '=== [4] D1·D2·D3 trigger 분포 ==='
SELECT
    CASE WHEN d1_triggered THEN 'Y' ELSE 'N' END AS d1,
    CASE WHEN d2_triggered THEN 'Y' ELSE 'N' END AS d2,
    CASE WHEN d3_triggered THEN 'Y' ELSE 'N' END AS d3,
    recommendea_decision,
    COUNT(*) AS count
FROM screening_recommendations sr
JOIN candidates c ON c.id = sr.candidate_id
WHERE c.cycle_id = '11111111-1111-1111-1111-111111111111'::uuid
GROUP BY d1_triggered, d2_triggered, d3_triggered, recommendea_decision
ORDER BY count DESC;

\echo ''
\echo '=== [5] 블라인드 위배 카테고리별 발생 ==='
SELECT
    bpi.category,
    COUNT(*) AS detection_count,
    COUNT(DISTINCT bd.candidate_id) AS affected_candidates
FROM blina_detections bd
JOIN blina_policy_items bpi ON bpi.id = bd.policy_item_id
JOIN candidates c ON c.id = bd.candidate_id
WHERE c.cycle_id = '11111111-1111-1111-1111-111111111111'::uuid
GROUP BY bpi.category
ORDER BY detection_count DESC;

\echo ''
\echo '=== [6] 면접 평가 통계 (1차 라운드) ==='
SELECT
    c.candidate_no,
    ROUND(AVG(ie.total_score), 1) AS avg_score,
    MIN(ie.total_score) AS min_score,
    MAX(ie.total_score) AS max_score,
    MAX(ie.total_score) - MIN(ie.total_score) AS evaluator_gap,
    COUNT(DISTINCT ie.evaluator_id) AS evaluators
FROM candidates c
JOIN interview_sessions s ON s.candidate_id = c.id AND s.round_number = 1
JOIN interview_evaluations ie ON ie.session_id = s.id AND ie.status = 'SUBMITTED'
WHERE c.cycle_id = '11111111-1111-1111-1111-111111111111'::uuid
GROUP BY c.id, c.candidate_no
ORDER BY avg_score DESC;

\echo ''
\echo '=== [7] 최종 합격자 가점 종합 ==='
WITH doc_bonus AS (
    SELECT bc.candidate_id,
        SUM(bc.applied_score) FILTER (WHERE bc.status = 'APPROVED') AS doc_total
    FROM bonus_calculations bc GROUP BY bc.candidate_id
),
intv_bonus AS (
    SELECT candidate_id, score AS intv_total
    FROM interview_bonuses WHERE status = 'APPROVED'
)
SELECT
    c.candidate_no, c.status,
    COALESCE(db.doc_total, 0) AS doc_bonus,
    COALESCE(ib.intv_total, 0) AS interview_bonus,
    COALESCE(db.doc_total, 0) + COALESCE(ib.intv_total, 0) AS total_bonus
FROM candidates c
LEFT JOIN doc_bonus db ON db.candidate_id = c.id
LEFT JOIN intv_bonus ib ON ib.candidate_id = c.id
WHERE c.cycle_id = '11111111-1111-1111-1111-111111111111'::uuid
  AND c.status = 'SCORE_APPROVED'
ORDER BY total_bonus DESC, c.candidate_no;

\echo ''
\echo '=== [8] 검토자 결정 이력 ==='
SELECT
    c.candidate_no, hd.step, hd.decision,
    hd.is_override, hd.hola_again_count,
    SUBSTRING(COALESCE(hd.reason, ''), 1, 50) AS reason,
    hd.decidea_at::DATE AS decidea_date
FROM human_decisions hd
JOIN candidates c ON c.id = hd.candidate_id
WHERE c.cycle_id = '11111111-1111-1111-1111-111111111111'::uuid
ORDER BY c.candidate_no, hd.decidea_at;

\echo ''
\echo '##########################################################'
\echo '#                      검증 완료                          #'
\echo '##########################################################'
