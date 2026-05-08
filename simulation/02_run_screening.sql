-- =====================================================================
-- SIMULATION 02: 결격 자동판정 (D1·D2·D3 평가 + 추천값 산출)
-- =====================================================================

WITH evaluated AS (
    SELECT
        c.id AS candidate_id,
        cp.education_level, cp.career_years,
        cp.submitted_documents,
        cp.legal_disqualification_answer,
        cp.self_declaration_submitted,
        cp.attachment_checklist,
        CASE
            WHEN cp.education_level NOT IN ('BACHELOR','MASTER','DOCTORATE')
              OR cp.career_years < 3
            THEN TRUE ELSE FALSE END AS d1_triggered,
        CASE
            WHEN COALESCE((cp.attachment_checklist->>'missing_required')::boolean, FALSE) = TRUE
              OR COALESCE((cp.attachment_checklist->>'expired')::boolean, FALSE) = TRUE
              OR COALESCE((cp.attachment_checklist->>'unreadable')::boolean, FALSE) = TRUE
            THEN TRUE ELSE FALSE END AS d2_triggered,
        CASE
            WHEN cp.legal_disqualification_answer = TRUE
              OR cp.self_declaration_submitted = FALSE
            THEN TRUE ELSE FALSE END AS d3_triggered
    FROM candidates c
    JOIN candidate_profiles cp ON cp.candidate_id = c.id
    WHERE c.cycle_id = '11111111-1111-1111-1111-111111111111'::uuid
),
recommendation AS (
    SELECT *,
        CASE
            WHEN d1_triggered AND d2_triggered AND d3_triggered THEN 'FAIL'::decision_value
            WHEN d1_triggered OR d2_triggered OR d3_triggered THEN 'HOLD'::decision_value
            ELSE 'PASS'::decision_value
        END AS recommended_decision
    FROM evaluated
)
INSERT INTO screening_recommendations (
    candidate_id, applied_rule_sets,
    d1_triggered, d2_triggered, d3_triggered,
    recommended_decision, rule_evidence, input_snapshot,
    evaluator_version, evaluated_at
)
SELECT
    r.candidate_id,
    jsonb_build_array(
        jsonb_build_object(
            'rule_set_id', (SELECT id FROM rule_sets WHERE code='JOB_DEFAULT_2026_V1'),
            'version', 1, 'scope', 'JOB'),
        jsonb_build_object(
            'rule_set_id', (SELECT id FROM rule_sets WHERE code='GLOBAL_LEGAL_DISQUAL_2026'),
            'version', 1, 'scope', 'GLOBAL')
    ),
    r.d1_triggered, r.d2_triggered, r.d3_triggered,
    r.recommended_decision,
    jsonb_build_object(
        'D1', jsonb_build_object('triggered', r.d1_triggered),
        'D2', jsonb_build_object('triggered', r.d2_triggered),
        'D3', jsonb_build_object('triggered', r.d3_triggered)
    ),
    jsonb_build_object(
        'education_level', r.education_level,
        'career_years', r.career_years,
        'legal_disqualification_answer', r.legal_disqualification_answer,
        'attachment_checklist', r.attachment_checklist),
    'sql_simulation_v1', NOW()
FROM recommendation r
ON CONFLICT (candidate_id) DO NOTHING;

UPDATE candidates SET status = 'AUTO_SCREENED', updated_at = NOW()
WHERE cycle_id = '11111111-1111-1111-1111-111111111111'::uuid
  AND status = 'NORMALIZED';

SELECT
    c.candidate_no,
    sr.d1_triggered AS d1, sr.d2_triggered AS d2, sr.d3_triggered AS d3,
    sr.recommended_decision AS recommendation,
    CASE c.candidate_no
        WHEN 'C001' THEN 'PASS'
        WHEN 'C002' THEN 'HOLD (D1)'
        WHEN 'C003' THEN 'HOLD (D2)'
        WHEN 'C004' THEN 'HOLD (D3)'
        WHEN 'C005' THEN 'FAIL (D1∧D2∧D3)'
        WHEN 'C006' THEN 'HOLD (D1∧D2)'
        WHEN 'C007' THEN 'PASS'
        WHEN 'C008' THEN 'PASS'
        WHEN 'C009' THEN 'PASS'
        WHEN 'C010' THEN 'PASS'
    END AS expected
FROM candidates c
JOIN screening_recommendations sr ON sr.candidate_id = c.id
WHERE c.cycle_id = '11111111-1111-1111-1111-111111111111'::uuid
ORDER BY c.candidate_no;
