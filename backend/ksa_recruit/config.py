"""
런타임 설정. 환경변수에서 로드.
"""
from __future__ import annotations
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str
    db_echo: bool = False
    api_prefix: str = "/api/v1"
    app_name: str = "KSA Recruit MVP"


def load_settings() -> Settings:
    return Settings(
        database_url=os.getenv(
            "DATABASE_URL",
            # 기본값: 개발용 (docker compose의 recruitment-postgres와 동일)
            "postgresql+psycopg://recruitment:recruitment@localhost:5432/recruitment_mvp",
        ),
        db_echo=os.getenv("DB_ECHO", "false").lower() == "true",
    )


# 싱글톤 (간단한 형태)
settings = load_settings()
