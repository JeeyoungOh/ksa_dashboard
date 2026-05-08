-- =====================================================================
-- SIMULATION 통합 실행
-- 사용법: psql -d recruitment_mvp -f apply_simulation.sql
-- =====================================================================

\set ON_ERROR_STOP on

\echo ''
\echo '=== SIM 00. Cycle & Posting Setup ==='
\i 00_setup_cycle_posting.sql

\echo ''
\echo '=== SIM 01. Insert 10 Candidates ==='
\i 01_insert_candidates.sql

\echo ''
\echo '=== SIM 02. Run Screening (D1/D2/D3) ==='
\i 02_run_screening.sql

\echo ''
\echo '=== SIM 03. Human Review (1차 검토) ==='
\i 03_human_review.sql

\echo ''
\echo '=== SIM 04. Blind Detection & Review ==='
\i 04_blind_detection.sql

\echo ''
\echo '=== SIM 05. Interview Setup (Q-Set + Sessions) ==='
\i 05_interview_setup.sql

\echo ''
\echo '=== SIM 06. Interview Evaluation + Final Approvald 06. Int(Rc sal Apterview_setup.sql

\echo ''
\ec7o 'onus01.lc -f appew tion + Final Appro7_bonus
\ilc -f appterview_setup.sql

\echo ''
\ec8. EvaluaVerificf appenal Appro8_fvalu_statuert_ca