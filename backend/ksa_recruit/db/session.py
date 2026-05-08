"""
SQLAlchemy 2.0 동기 세션.

async를 쓰지 않는 이유:
  - MVP 단계에서 동시성 부담이 낮음 (검토자 수십 명 규모)
  - sync가 단순하고 디버깅 쉬움
  - 향후 성능 이슈 발생 시 async로 마이그레이션 가능
"""
from __future__ import annotations
from typing import Iterator

from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import (
    DeclarativeBase, sessionmaker, Session,
)

from ..config import settings


# PostgreSQL 명명규약 (Alembic이 제약조건 자동명 생성에 사용)
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


# 엔진 + 세션 팩토리 (모듈 로드 시 1회 생성)
engine = create_engine(
    settings.database_url,
    echo=settings.db_echo,
    pool_pre_ping=True,    # 끊긴 커넥션 자동 복구
    pool_size=5,
    max_overflow=10,
)

SessionFactory = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def get_session() -> Iterator[Session]:
    """
    FastAPI 의존성으로 사용. 요청 1건당 세션 1개.
    예외 발생 시 자동 rollback, 항상 close.
    """
    session = SessionFactory()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
