from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    """Un compte utilisateur."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    mot_de_passe_hash: Mapped[str] = mapped_column(String(255))
    cree_le: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
