from __future__ import annotations

from datetime import datetime

from sqlalchemy import Float, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class EnvironmentalReading(Base):
    __tablename__ = "environmental_readings"

    id: Mapped[int] = mapped_column(primary_key=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    rainfall: Mapped[float] = mapped_column(Float, default=0.0)       # mm
    temperature: Mapped[float] = mapped_column(Float, default=0.0)    # Celsius
    water_level: Mapped[float] = mapped_column(Float, default=0.0)    # meters
    recorded_at: Mapped[datetime] = mapped_column(
        nullable=False, default=lambda: datetime.utcnow(), index=True
    )
    region_id: Mapped[int] = mapped_column(ForeignKey("regions.id"), nullable=False)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"), nullable=False
    )

    region: Mapped["Region"] = relationship(back_populates="readings")

    __table_args__ = (
        Index("ix_readings_region_time", "region_id", "recorded_at"),
        Index("ix_readings_org", "organization_id"),
    )
