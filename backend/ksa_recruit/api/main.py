"""
FastAPI 애플리케이션 팩토리.

실행:
  uvicorn ksa_recruit.api.main:app --host 0.0.0.0 --port 8000 --reload
"""
from __future__ import annotations
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from ..config import settings
from ..db.session import engine
from .routers import candidates, screening


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="KSA 채용 MVP — 룰 엔진 + 결격 자동판정 API",
        openapi_url=f"{settings.api_prefix}/openapi.json",
        docs_url=f"{settings.api_prefix}/docs",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],   # 운영 시 화이트리스트로
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 헬스체크
    @app.get("/health", tags=["meta"])
    def health() -> dict:
        return {
            "status": "ok",
            "app": settings.app_name,
            "ts": datetime.utcnow().isoformat() + "Z",
        }

    @app.get("/health/db", tags=["meta"])
    def health_db() -> dict:
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1")).scalar()
            return {"status": "ok" if result == 1 else "degraded"}
        except SQLAlchemyError as e:
            return {"status": "error", "detail": str(e)}

    # 라우터 등록
    app.include_router(candidates.router, prefix=settings.api_prefix)
    app.include_router(screening.router, prefix=settings.api_prefix)

    return app


app = create_app()
