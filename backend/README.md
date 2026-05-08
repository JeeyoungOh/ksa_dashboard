# KSA 채용 MVP — 백엔드 API

❶ 룰 평가 엔진 + ❸ FastAPI + Alembic을 통합한 백엔드 골격.

## 폴더 구조

```
backend/
├── pyproject.toml
├── alembic.ini
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/0001_baseline.py   # 현재 DDL 09개 파일 흡수
├── ksa_recruit/
│   ├── config.py                   # DATABASE_URL 환경변수
│   ├── domain/                     # ❶ 도메인 모델 (Pydantic)
│   ├── rules/                      # ❶ 연산자 + 평가기
│   ├── engines/                    # ❶ 4개 엔진 (screening/bonus/blind/pii)
│   ├── db/
│   │   ├── session.py              # SQLAlchemy Engine + Session
│   │   ├── mappers.py              # ORM ↔ 도메인 변환
│   │   └── models/                 # 9개 ORM 모델
│   ├── repositories/               # DB 접근 캡슐화
│   ├── services/                   # 룰 엔진 + DB 트랜잭션 결합
│   └── api/
│       ├── main.py                 # FastAPI 앱
│       ├── deps.py                 # 의존성 주입
│       ├── routers/                # candidates, screening
│       └── schemas/                # 요청/응답 Pydantic
├── tests/                          # 50개 단위 테스트 (룰 엔진)
└── scripts/demo.py                 # 룰 엔진 데모
```

## 의존성 설치

```bash
pip install -e ".[api,dev]"
```

`[api]`: fastapi, sqlalchemy, alembic, psycopg, uvicorn
`[dev]`: pytest, pytest-cov

## 환경변수

```bash
# 필수
export DATABASE_URL='postgresql+psycopg://recruitment:recruitment@localhost:5432/recruitment_mvp'

# 선택
export DB_ECHO=false                  # SQL 로그 출력
export KSA_DDL_DIR=/path/to/ddl       # baseline 마이그레이션이 참조할 DDL 디렉토리
```

## EC2 적용 가이드

### 시나리오 1: 이미 DDL이 적용된 환경 (현재 EC2)

DB는 이미 37개 테이블이 들어있으므로 마이그레이션 메타만 등록:

```bash
# 백엔드 코드 + DDL 디렉토리를 EC2 호스트에 업로드 후
# 호스트에서 실행 (컨테이너 안에서 실행하려면 docker exec로 감싸세요)
cd backend
pip install -e ".[api]"

KSA_DDL_DIR=/path/to/ddl \
DATABASE_URL='postgresql+psycopg://recruitment:recruitment@localhost:5432/recruitment_mvp' \
alembic stamp 0001_baseline
```

### 시나리오 2: 새 환경에 처음 세팅

```bash
# 빈 DB 위에서 baseline부터 적용 → 37 테이블 + 시드 자동 생성
KSA_DDL_DIR=/path/to/ddl alembic upgrade head
```

### API 서버 기동

```bash
DATABASE_URL='postgresql+psycopg://recruitment:recruitment@localhost:5432/recruitment_mvp' \
uvicorn ksa_recruit.api.main:app --host 0.0.0.0 --port 8000

# 백그라운드 실행
nohup uvicorn ksa_recruit.api.main:app --host 0.0.0.0 --port 8000 \
  > /var/log/ksa-api.log 2>&1 &
```

## API 사용

### 헬스체크

```bash
curl http://localhost:8000/health
# → {"status":"ok","app":"KSA Recruit MVP","ts":"..."}

curl http://localhost:8000/health/db
# → {"status":"ok"}
```

### Swagger UI

```
http://localhost:8000/api/v1/docs
```

### 시나리오: ❷ 시뮬레이션 SQL을 API로 재현

**1. 후보자 등록**

```bash
curl -X POST http://localhost:8000/api/v1/candidates \
  -H 'Content-Type: application/json' \
  -d '{
    "cycle_id": "11111111-1111-1111-1111-111111111111",
    "posting_id": "22222222-2222-2222-2222-222222222222",
    "candidate_no": "API001",
    "job_code": "AI_RESEARCHER",
    "education_level": "MASTER",
    "career_years": 5.0,
    "certifications": ["A_GRADE"],
    "submitted_documents": ["application_form","self_intro","career_history"],
    "attachment_checklist": {"missing_required":false,"expired":false,"unreadable":false},
    "cover_letter": "AI 연구에 5년간 매진해 왔습니다."
  }'
# → 201 Created, candidate.id 반환
```

**2. 결격 자동판정 실행**

```bash
CANDIDATE_ID="..."  # 위 응답에서 받은 ID
curl -X POST http://localhost:8000/api/v1/screening/$CANDIDATE_ID/run
# → 200 OK, recommendation: PASS, candidate_status: AUTO_SCREENED
```

**3. 결과 조회**

```bash
curl http://localhost:8000/api/v1/candidates/$CANDIDATE_ID
# → 후보자 + 프로필 + 자유서술 + 자동판정 결과 (rule_evidence, input_snapshot 포함)
```

## 단위 테스트

```bash
pytest tests/ -v --ignore=tests/integration
# ====== 50 passed ====== (룰 엔진 회귀)
```

## 검증 포인트

이번 골격은 ❷ 시뮬레이션 SQL의 Step 1~2를 **API 호출로 재현**할 수 있도록 구성됐습니다.
검증 절차:

1. `alembic stamp 0001_baseline`으로 baseline 등록
2. uvicorn으로 서버 기동
3. 시뮬레이션 SQL의 C001~C010 데이터 중 하나를 위 curl 시나리오로 등록·판정
4. 결과의 `recommendation` 값이 ❷ 시뮬레이션 결과(SQL과 Python 단위 테스트 모두 일치 확인됨)와 같은지 확인

룰 엔진 자체의 정확성은 단위 테스트 50/50으로 이미 보장되어 있어,
API 통합 검증은 "DB ↔ ORM ↔ 엔진" 연결 점검 위주로만 하시면 됩니다.

## 다음 단계 (선택)

골격 위에 추가할 수 있는 항목:

- `POST /screening/{id}/decide` — 사람 검토자 결정 입력 (DOC_SCREENING)
- `POST /blind/{id}/detect` + `POST /blind/{id}/review` — 블라인드 위배 검토
- `POST /interview/sessions` + `POST /evaluations` — 면접 평가
- `POST /bonus/{id}/calculate` — 가점 자동계산
- 인증 (JWT) + 권한 가드 (REVIEWER vs APPROVER)
- `tests/integration/` — httpx 기반 통합 테스트
