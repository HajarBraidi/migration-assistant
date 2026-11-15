from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Project(Base):
    """Un projet de migration. `plan` contient toujours la version la plus récente."""

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

    versions: Mapped[list["Version"]] = relationship(
        order_by="Version.numero", cascade="all, delete-orphan"
    )
    messages: Mapped[list["Message"]] = relationship(
        order_by="Message.id", cascade="all, delete-orphan"
    )


class Version(Base):
    """Une version du plan. Les versions ne sont jamais modifiées ni supprimées."""

    __tablename__ = "versions"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    numero: Mapped[int] = mapped_column(Integer)
    origine: Mapped[str] = mapped_column(String(300))
    plan: Mapped[dict] = mapped_column(JSON)
    avertissements: Mapped[list] = mapped_column(JSON)
    cree_le: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Message(Base):
    """Un message de la conversation entre l'utilisateur et l'assistant."""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    role: Mapped[str] = mapped_column(String(20))  # "utilisateur" ou "assistant"
    contenu: Mapped[str] = mapped_column(Text)
    type: Mapped[str | None] = mapped_column(String(20), nullable=True)  # question, reponse…
    # Numéro de la version créée par ce message (seulement pour une modification)
    version_creee: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cree_le: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
