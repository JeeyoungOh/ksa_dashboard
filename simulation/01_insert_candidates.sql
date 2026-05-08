-- =====================================================================
-- SIMULATION 01: 가상 지원자 10명 INSERT
-- =====================================================================

-- C001 김무결: 모든 조건 충족 → 예상 PASS
INSERT INTO candidates (id, cycle_id, posting_id, candidate_no, status)
VALUES ('aaaaaaaa-0001-0000-0000-000000000000'::uuid,
    '11111111-1111-1111-1111-111111111111'::uuid,
    '22222222-2222-2222-2222-222222222222'::uuid, 'C001', 'NORMALIZED');
INSERT INTO candidate_profiles (
    candidate_id, job_code, career_years, education_level,
    education, certifications, language_tests, submitted_documents,
    legal_disqualification_answer, self_declaration_submitted, attachment_checklist
) VALUES (
    'aaaaaaaa-0001-0000-0000-000000000000'::uuid,
    'AI_RESEARCHER', 5.0, 'MASTER',
    '[{"degree":"MASTER","field":"Computer Science"}]'::jsonb,
    '["A_GRADE"]'::jsonb,
    '[{"test":"TOEIC","score":850,"level":"HIGH"}]'::jsonb,
    '["application_form","self_intro","career_history"]'::jsonb,
    FALSE, TRUE,
    '{"missing_required":false,"expired":false,"unreadable":false}'::jsonb);
INSERT INTO candidate_narratives (candidate_id, cover_letter, career_history)
VALUES ('aaaaaaaa-0001-0000-0000-000000000000'::uuid,
    'AI 연구에 5년간 매진해 왔습니다. 자연어처리와 추천시스템 분야에서 다수의 프로젝트를 수행했습니다.',
    '5년간 다양한 AI 프로젝트를 수행했으며, 특히 추천 시스템 고도화에 주력했습니다.');

-- C002 이부족: 학력 미달 → HOLD (D1)
INSERT INTO candidates (id, cycle_id, posting_id, candidate_no, status)
VALUES ('aaaaaaaa-0002-0000-0000-000000000000'::uuid,
    '11111111-1111-1111-1111-111111111111'::uuid,
    '22222222-2222-2222-2222-222222222222'::uuid, 'C002', 'NORMALIZED');
INSERT INTO candidate_profiles (
    candidate_id, job_code, career_years, education_level,
    submitted_documents, legal_disqualification_answer,
    self_declaration_submitted, attachment_checklist
) VALUES (
    'aaaaaaaa-0002-0000-0000-000000000000'::uuid,
    'AI_RESEARCHER', 4.0, 'HIGH_SCHOOL',
    '["application_form","self_intro","career_history"]'::jsonb,
    FALSE, TRUE,
    '{"missing_required":false,"expired":false,"unreadable":false}'::jsonb);
INSERT INTO candidate_narratives (candidate_id, cover_letter, career_history)
VALUES ('aaaaaaaa-0002-0000-0000-000000000000'::uuid,
    '실무 경험으로 4년간 AI 분야에서 일했습니다.',
    '4년간 AI 모델 운영 업무를 담당했습니다.');

-- C003 박미제출: 서류 누락 → HOLD (D2)
INSERT INTO candidates (id, cycle_id, posting_id, candidate_no, status)
VALUES ('aaaaaaaa-0003-0000-0000-000000000000'::uuid,
    '11111111-1111-1111-1111-111111111111'::uuid,
    '22222222-2222-2222-2222-222222222222'::uuid, 'C003', 'NORMALIZED');
INSERT INTO candidate_profiles (
    candidate_id, job_code, career_years, education_level,
    submitted_documents, legal_disqualification_answer,
    self_declaration_submitted, attachment_checklist
) VALUES (
    'aaaaaaaa-0003-0000-0000-000000000000'::uuid,
    'AI_RESEARCHER', 6.0, 'MASTER',
    '["application_form"]'::jsonb,
    FALSE, TRUE,
    '{"missing_required":true,"expired":false,"unreadable":false}'::jsonb);
INSERT INTO candidate_narratives (candidate_id, cover_letter, career_history)
VALUES ('aaaaaaaa-0003-0000-0000-000000000000'::uuid,
    NULL, '6년 경력입니다.');

-- C004 최자기신고: 법적 결격 → HOLD (D3)
INSERT INTO candidates (id, cycle_id, posting_id, candidate_no, status)
VALUES ('aaaaaaaa-0004-0000-0000-000000000000'::uuid,
    '11111111-1111-1111-1111-111111111111'::uuid,
    '22222222-2222-2222-2222-222222222222'::uuid, 'C004', 'NORMALIZED');
INSERT INTO candidate_profiles (
    candidate_id, job_code, career_years, education_level,
    submitted_documents, legal_disqualification_answer,
    self_declaration_submitted, attachment_checklist
) VALUES (
    'aaaaaaaa-0004-0000-0000-000000000000'::uuid,
    'AI_RESEARCHER', 8.0, 'DOCTORATE',
    '["application_form","self_intro","career_history"]'::jsonb,
    TRUE, TRUE,
    '{"missing_required":false,"expired":false,"unreadable":false}'::jsonb);
INSERT INTO candidate_narratives (candidate_id, cover_letter, career_history)
VALUES ('aaaaaaaa-0004-0000-0000-000000000000'::uuid,
    '박사학위를 보유하고 8년간 연구 활동을 수행했습니다.',
    '연구원으로서 8년간 다양한 프로젝트를 수행했습니다.');

-- C005 정삼중: D1+D2+D3 모두 결격 → AUTO_FAIL
INSERT INTO candidates (id, cycle_id, posting_id, candidate_no, status)
VALUES ('aaaaaaaa-0005-0000-0000-000000000000'::uuid,
    '11111111-1111-1111-1111-111111111111'::uuid,
    '22222222-2222-2222-2222-222222222222'::uuid, 'C005', 'NORMALIZED');
INSERT INTO candidate_profiles (
    candidate_id, job_code, career_years, education_level,
    submitted_documents, legal_disqualification_answer,
    self_declaration_submitted, attachment_checklist
) VALUES (
    'aaaaaaaa-0005-0000-0000-000000000000'::uuid,
    'AI_RESEARCHER', 1.0, 'HIGH_SCHOOL',
    '["application_form"]'::jsonb,
    TRUE, TRUE,
    '{"missing_required":true,"expired":false,"unreadable":false}'::jsonb);
INSERT INTO candidate_narratives (candidate_id, cover_letter, career_history)
VALUES ('aaaaaaaa-0005-0000-0000-000000000000'::uuid,
    '경력 1년의 신입입니다.', '1년간 인턴 경험이 있습니다.');

-- C006 강이중: D1+D2 결격 (D3 OK) → HOLD
INSERT INTO candidates (id, cycle_id, posting_id, candidate_no, status)
VALUES ('aaaaaaaa-0006-0000-0000-000000000000'::uuid,
    '11111111-1111-1111-1111-111111111111'::uuid,
    '22222222-2222-2222-2222-222222222222'::uuid, 'C006', 'NORMALIZED');
INSERT INTO candidate_profiles (
    candidate_id, job_code, career_years, education_level,
    submitted_documents, legal_disqualification_answer,
    self_declaration_submitted, attachment_checklist
) VALUES (
    'aaaaaaaa-0006-0000-0000-000000000000'::uuid,
    'AI_RESEARCHER', 2.0, 'HIGH_SCHOOL',
    '["application_form"]'::jsonb,
    FALSE, TRUE,
    '{"missing_required":true,"expired":false,"unreadable":false}'::jsonb);
INSERT INTO candidate_narratives (candidate_id, cover_letter, career_history)
VALUES ('aaaaaaaa-0006-0000-0000-000000000000'::uuid,
    '경력 2년의 실무자입니다.', '2년간 데이터 분석 업무를 했습니다.');

-- C007 윤위배: 모든 조건 충족 + 자기소개에 학교명·지역·가족 노출
INSERT INTO candidates (id, cycle_id, posting_id, candidate_no, status)
VALUES ('aaaaaaaa-0007-0000-0000-000000000000'::uuid,
    '11111111-1111-1111-1111-111111111111'::uuid,
    '22222222-2222-2222-2222-222222222222'::uuid, 'C007', 'NORMALIZED');
INSERT INTO candidate_profiles (
    candidate_id, job_code, career_years, education_level,
    submitted_documents, legal_disqualification_answer,
    self_declaration_submitted, attachment_checklist
) VALUES (
    'aaaaaaaa-0007-0000-0000-000000000000'::uuid,
    'AI_RESEARCHER', 4.0, 'MASTER',
    '["application_form","self_intro","career_history"]'::jsonb,
    FALSE, TRUE,
    '{"missing_required":false,"expired":false,"unreadable":false}'::jsonb);
INSERT INTO candidate_narratives (candidate_id, cover_letter, career_history)
VALUES ('aaaaaaaa-0007-0000-0000-000000000000'::uuid,
    '저는 서울대학교 컴퓨터공학과를 졸업하고 4년간 AI 분야에서 일했습니다. 부산 출신으로 어머니께서 교사로 재직하시며 학업을 지원해 주셨습니다.',
    '서울대학교 졸업 후 부산에서 4년간 근무했습니다.');

-- C008 임가점: 박사+자격증+어학 → 가점 상한 검증
INSERT INTO candidates (id, cycle_id, posting_id, candidate_no, status)
VALUES ('aaaaaaaa-0008-0000-0000-000000000000'::uuid,
    '11111111-1111-1111-1111-111111111111'::uuid,
    '22222222-2222-2222-2222-222222222222'::uuid, 'C008', 'NORMALIZED');
INSERT INTO candidate_profiles (
    candidate_id, job_code, career_years, education_level,
    education, certifications, language_tests, submitted_documents,
    legal_disqualification_answer, self_declaration_submitted, attachment_checklist
) VALUES (
    'aaaaaaaa-0008-0000-0000-000000000000'::uuid,
    'AI_RESEARCHER', 7.0, 'DOCTORATE',
    '[{"degree":"DOCTORATE","field":"Machine Learning"}]'::jsonb,
    '["A_GRADE","B_GRADE"]'::jsonb,
    '[{"test":"TOEIC","score":920,"level":"HIGH"}]'::jsonb,
    '["application_form","self_intro","career_history"]'::jsonb,
    FALSE, TRUE,
    '{"missing_required":false,"expired":false,"unreadable":false}'::jsonb);
INSERT INTO candidate_narratives (candidate_id, cover_letter, career_history)
VALUES ('aaaaaaaa-0008-0000-0000-000000000000'::uuid,
    '박사학위를 취득하고 7년간 머신러닝 연구를 수행했습니다.',
    '박사 과정 중 5편의 논문을 발표하고, 졸업 후 산업계에서 추천 시스템 연구를 주도했습니다.');

-- C009 한경계: 경력 정확히 3년 (경계값) → PASS
INSERT INTO candidates (id, cycle_id, posting_id, candidate_no, status)
VALUES ('aaaaaaaa-0009-0000-0000-000000000000'::uuid,
    '11111111-1111-1111-1111-111111111111'::uuid,
    '22222222-2222-2222-2222-222222222222'::uuid, 'C009', 'NORMALIZED');
INSERT INTO candidate_profiles (
    candidate_id, job_code, career_years, education_level,
    submitted_documents, legal_disqualification_answer,
    self_declaration_submitted, attachment_checklist
) VALUES (
    'aaaaaaaa-0009-0000-0000-000000000000'::uuid,
    'AI_RESEARCHER', 3.0, 'BACHELOR',
    '["application_form","self_intro","career_history"]'::jsonb,
    FALSE, TRUE,
    '{"missing_required":false,"expired":false,"unreadable":false}'::jsonb);
INSERT INTO candidate_narratives (candidate_id, cover_letter, career_history)
VALUES ('aaaaaaaa-0009-0000-0000-000000000000'::uuid,
    '학사 졸업 후 정확히 3년간 AI 엔지니어로 일했습니다.',
    '3년간 모델 개발 및 운영 업무를 담당했습니다.');

-- C010 노유공자: 모든 조건 충족 + 국가유공자
INSERT INTO candidates (id, cycle_id, posting_id, candidate_no, status)
VALUES ('aaaaaaaa-0010-0000-0000-000000000000'::uuid,
    '11111111-1111-1111-1111-111111111111'::uuid,
    '22222222-2222-2222-2222-222222222222'::uuid, 'C010', 'NORMALIZED');
INSERT INTO candidate_profiles (
    candidate_id, job_code, career_years, education_level,
    education, certifications, submitted_documents,
    legal_disqualification_answer, self_declaration_submitted,
    attachment_checklist, normalized_profile
) VALUES (
    'aaaaaaaa-0010-0000-0000-000000000000'::uuid,
    'AI_RESEARCHER', 4.0, 'MASTER',
    '[{"degree":"MASTER","field":"AI"}]'::jsonb,
    '["A_GRADE"]'::jsonb,
    '["application_form","self_intro","career_history","patriot_cert"]'::jsonb,
    FALSE, TRUE,
    '{"missing_required":false,"expired":false,"unreadable":false}'::jsonb,
    '{"is_patriot_top":true}'::jsonb);
INSERT INTO candidate_narratives (candidate_id, cover_letter, career_history)
VALUES ('aaaaaaaa-0010-0000-0000-000000000000'::uuid,
    '4년간 AI 분야에서 연구개발 업무를 수행했습니다.',
    '4년간 자연어처리 모델 개발에 주력했습니다.');

SELECT
    c.candidate_no, c.status,
    cp.education_level, cp.career_years,
    cp.legal_disqualification_answer AS d3_flag,
    cp.attachment_checklist->>'missing_required' AS doc_missing
FROM candidates c
JOIN candidate_profiles cp ON cp.candidate_id = c.id
WHERE c.cycle_id = '11111111-1111-1111-1111-111111111111'::uuid
ORDER BY c.candidate_no;
