-- =====================================================================
-- SIMULATION 00: 채용 사이클 + 공고 셋업
-- =====================================================================

INSERT INTO recruitment_cycles (id, cycle_type, cycle_year, cycle_seq, name, start_date, end_date, status)
VALUES (
    '11111111-1111-1111-1111-111111111111'::uuid,
    'PUBLIC', 2026, 1,
    '2026년 KSA 정기공채',
    '2026-03-01', '2026-04-30', 'ACTIVE'
) ON CONFLICT DO NOTHING;

INSERT INTO job_postings (
    id, cycle_id, rule_set_id, interview_template_id, bonus_rule_set_id,
    job_code, title, department, headcount, open_date, close_date, status
)
SELECT
    '22222222-2222-2222-2222-222222222222'::uuid,
    '11111111-1111-1111-1111-111111111111'::uuid,
    rs.id, ift.id, brs.id,
    'AI_RESEARCHER', 'AI 연구원 (정규직)', 'AI혁신본부', 2,
    '2026-03-01', '2026-03-31', 'OPEN'
FROM rule_sets rs, interview_form_templates ift, bonus_rule_sets brs
WHERE rs.code = 'JOB_DEFAULT_2026_V1'
  AND ift.code = 'KSA_DEFAULT_2026'
  AND brs.code = 'KSA_BONUS_MVP_2026'
ON CONFLICT DO NOTHING;

SELECT
    rc.cycle_year || '-' || rc.cycle_seq AS cycle,
    rc.name AS cycle_name,
    jp.job_code, jp.title, jp.headcount
FROM recruitment_cycles rc
JOIN job_postings jp ON jp.cycle_id = rc.id
WHERE rc.id = '11111111-1111-1111-1111-111111111111'::uuid;
