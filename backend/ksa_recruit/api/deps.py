"""
FastAPI 의존성 주입 헬퍼.
"""
from __future__ import annotations
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from ..db.session import get_session


SessionDep = Annotated[Session, Depends(get_session)]
