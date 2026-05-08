"""baseline - import existing DDL

Revision ID: 0001_baseline
Revises:
Create Date: 2026-05-08

이 리비전은 ❷ 단계까지 만들어 둔 DDL을 Alembic 관리 하에 두기 위한 baseline.
새 환경에 alembic upgrade head 실행 시 동일한 37개 테이블 + 시드가 만들어짐.

이미 DDL이 적용된 환경(EC2 등)에서는:
  $ alembic stamp 0001_baseline
실행해 마이그레이션 메타만 기록하면 됨 (실제 DDL은 다시 실행 X).
"""
from __future__ import annotations
import os
from pathlib import Path
from typing import Sequence, Union

from alembic import op


# revision identifiers
revision: str = "0001_baseline"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# DDL 파일이 위치한 경로 (운영 환경에 맞춰 환경변수로 오버라이드 가능)
_DDL_DIR = Path(os.getenv(
    "KSA_DDL_DIR",
    str(Path(__file__).resolve().parents[2] / "ddl"),
))

# 적용 순서대로
_DDL_FILES: tuple[str, ...] = (
    "00_extensions_and_enums.sql",
    "01_users_and_rules.sql",
    "02_cycles_and_postings.sql",
    "03_candidates.sql",
    "04_screening_and_decisions.sql",
    "05_blind_review.sql",
    "06_interview.sql",
    "07_bonus.sql",
    "08_llm_pii_retention.sql",
    "09_audit_and_seed.sql",
)


def upgrade() -> None:
    for fname in _DDL_FILES:
        path = _DDL_DIR / fname
        if not path.exists():
            raise RuntimeError(
                f"baseline 적용 실패: DDL 파일을 찾을 수 없음: {path}\n"
                f"KSA_DDL_DIR 환경변수로 DDL 디렉토리를 지정하세요."
            )
        sql = path.read_text(encoding="utf-8")
        # psql 메타커맨드(\echo 등)는 raw 실행 시 에러 → 사전 제거
        cleaned = "\n".join(
            line for line in sql.splitlines()
            if not line.strip().startswith("\\")
        )
        op.execute(cleaned)


def downgrade() -> None:
    """
    baseline 다운그레이드는 위험하므로 명시적 차단.
    필요 시 별도 리비전에서 DROP 작성.
    """
    raise RuntimeError(
        "baseline 다운그레이드는 지원하지 않음. "
        "DB 자체를 재생성하거나, 명시적으로 DROP 리비전을 작성하세요."
    )
