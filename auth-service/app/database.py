from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    """Classe de base de toutes les tables."""


def get_db() -> Generator[Session, None, None]:
    """Ouvre une session de base de données pour une requête, puis la ferme."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
