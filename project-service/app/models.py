from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Project(Base):
    """Un projet de migration enregistré (avec la dernière version de son plan)."""

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

    revisions: Mapped[list["Revision"]] = relationship(
        back_populates="projet", order_by="Revision.id", cascade="all, delete-orphan"
    )


class Revision(Base):
    """Une modification du plan demandée par l'utilisateur (historique des versions)."""

    __tablename__ = "revisions"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    demande: Mapped[str] = mapped_column(Text)
    # Le plan AVANT la modification, pour pouvoir revenir en arrière plus tard
    plan_precedent: Mapped[dict] = mapped_column(JSON)
    cree_le: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    projet: Mapped[Project] = relationship(back_populates="revisions")
