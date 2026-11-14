from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Project(Base):
    """Un projet de migration enregistré."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Propriétaire du projet (identifiant fourni par auth-service via le gateway)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    nom: Mapped[str] = mapped_column(String(100))
    description: Mapped[dict] = mapped_column(JSON)
    plan: Mapped[dict] = mapped_column(JSON)
    avertissements: Mapped[list] = mapped_column(JSON)
    cree_le: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
