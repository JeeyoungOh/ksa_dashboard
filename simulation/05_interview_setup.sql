-- =====================================================================
-- SIMULATION 05: 면접 세션 + 질문지 생성
-- =====================================================================

DO $$
DECLARE
    v_admin UUID;
    v_llm_id UUID;
    v_scrub_id UUID;
    v_qset_id UUID;
    v_candidate RECORD;
    v_input_text TEXT;
    v_masked_text TEXT;
BEGIN
    SELECT id INTO v_admin FROM users WHERE role = 'ADMIN' LIMIT 1;

    FOR v_candidate IN
        SELECT c.id, c.candidate_no, cn.cover_letter, cn.cover_letter_masked
        FROM candidates c
        LEFT JOIN candidate_narratives cn ON cn.candidate_id = c.id
        WHERE c.status = 'INTERVIEW_TARGET'
        ORDER BY c.candidate_no
    LOOP
        v_input_text := v_candidate.cover_letter;
        v_masked_text := COALESCE(v_candidate.cover_letter_masked, v_candidate.cover_letter);

        INSERT INTO llm_call_logs (
            candidate_id, initiator_id, purpose, provider, model,
            prompt_version, input_masked, output_raw,
            input_tokens, output_tokens, latency_ms, status
        ) VALUES (
            v_candidate.id, v_admin, 'INTERVIEW_QUESTION_GEN',
            'ANTHROPIC', 'claude-opus-4-7',
            'qgen-v1.0', v_masked_text,
            '{"common":[],"job":[],"personalized":[]}',
            450, 320, 1850, 'SUCCESS'
        ) RETURNING id INTO v_llm_id;

        INSERT INTO pii_scrub_logs (
            llm_call_id, candidate_id, input_original, input_scrubbed,
            detected_pii, scrub_layer_results, passed
        ) VALUES (
            v_llm_id, v_candidate.id, v_input_text, v_masked_text,
            CASE WHEN v_candidate.candidate_no = 'C007'
                 THEN '[{"type":"SCHOOL"},{"type":"REGION"},{"type":"FAMILY"}]'::jsonb
                 ELSE '[]'::jsonb END,
            jsonb_build_object(
                'layer1_dict', CASE WHEN v_candidate.candidate_no = 'C007' THEN 3 ELSE 0 END,
                'layer2_ner', 0, 'layer3_heuristic', 0),
            TRUE
        ) RETURNING id INTO v_scrub_id;

        INSERT INTO interview_question_sets (
            candidate_id, version, llm_prompt_version,
            pii_filter_status, pii_scrub_log_id, status, generated_at, confirmed_at
        ) VALUES (
            v_candidate.id, 1, 'qgen-v1.0',
            'PASSED', v_scrub_id, 'CONFIRMED', NOW(), NOW()
        ) RETURNING id INTO v_qset_id;

        INSERT INTO interview_questions (question_set_id, track, question_text, sort_order)
        VALUES
            (v_qset_id, 'COMMON', '본인이 생각하는 공공기관 종사자의 가장 중요한 자질은?', 1),
            (v_qset_id, 'COMMON', '팀 내 의견 충돌 상황에서 본인의 역할은?', 2),
            (v_qset_id, 'JOB', 'LLM 서빙 시 비용·지연 문제 해결 접근법은?', 3),
            (v_qset_id, 'JOB', 'AI 모델 공정성 평가 지표 설명', 4),
            (v_qset_id, 'JOB', 'RAG 시스템 검색 품질 메트릭', 5);

        INSERT INTO interview_questions (question_set_id, track, question_text, source_evidence, sort_order)
        VALUES
            (v_qset_id, 'PERSONALIZED',
             '경력 중 가장 도전적이었던 AI 프로젝트의 기술적 난점과 해결을 STAR로 설명해 주십시오.',
             jsonb_build_object('source', 'cover_letter_masked'), 6),
            (v_qset_id, 'PERSONALIZED',
             '추천시스템 콜드 스타트 문제 처리 경험을 구체적으로 말씀해 주십시오.',
             jsonb_build_object('source', 'cover_letter_masked'), 7);
    END LOOP;
END$$;

DO $$
DECLARE
    v_interviewer UUID;
    v_approver UUID;
    v_candidate_id UUID;
    v_evaluators JSONB;
BEGIN
    SELECT id INTO v_interviewer FROM users WHERE role = 'INTERVIEWER' LIMIT 1;
    SELECT id INTO v_approver FROM users WHERE role = 'APPROVER' LIMIT 1;
    v_evaluators := jsonb_build_array(v_interviewer, v_approver);

    FOR v_candidate_id IN
        SELECT id FROM candidates WHERE status = 'INTERVIEW_TARGET'
    LOOP
        INSERT INTO interview_sessions (
            candidate_id, round_number, round_name,
            scheduled_at, location, status, evaluator_ids
        ) VALUES (
            v_candidate_id, 1, '실무진 면접',
            NOW() + INTERVAL '7 days', 'KSA 본관 회의실 A',
            'SCHEDULED', v_evaluators);

        INSERT INTO interview_sessions (
            candidate_id, round_number, round_name,
            scheduled_at, location, status, evaluator_ids
        ) VALUES (
            v_candidate_id, 2, '임원 면접',
            NOW() + INTERVAL '14 days', 'KSA 본관 임원회의실',
            'SCHEDULED', jsonb_build_array(v_approver));
    END LOOP;
END$$;

UPDATE candidates SET status = 'INTERVIEW_QUESTIONS_READY', updated_at = NOW()
WHERE status = 'INTERVIEW_TARGET'
  AND id IN (SELECT candidate_id FROM interview_question_sets WHERE status = 'CONFIRMED');

SELECT
    c.candidate_no, c.status, qs.pii_filter_status,
    (SELECT count(*) FROM interview_questions iq WHERE iq.question_set_id = qs.id) AS total_questions,
    (SELECT count(*) FROM interview_sessions s WHERE s.candidate_id = c.id) AS sessions
FROM candidates c
LEFT JOIN interview_question_sets qs ON qs.candidate_id = c.id AND qs.status = 'CONFIRMED'
WHERE c.cycle_id = '11111111-1111-1111-1111-111111111111'::uuid
  AND c.status = 'INTERVIEW_QUESTIONS_READY'
ORDER BY c.candidate_no;
