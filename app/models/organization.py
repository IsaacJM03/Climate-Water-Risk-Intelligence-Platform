from __future__ import annotations

from datetime import datetime

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(
        Enum("church", "NGO", "government"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.utcnow())

    users: Mapped[list["User"]] = relationship(back_populates="organization")
    regions: Mapped[list["Region"]] = relationship(back_populates="organization")
