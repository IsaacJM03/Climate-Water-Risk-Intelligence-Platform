from __future__ import annotations

from datetime import datetime

from sqlalchemy import Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Region(Base):
    __tablename__ = "regions"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Boundary stored as WKT string (Well-Known Text for POLYGON geometry)
    boundary: Mapped[str | None] = mapped_column(Text, nullable=True)
    population: Mapped[int] = mapped_column(Integer, default=0)
    vulnerability_index: Mapped[float] = mapped_column(Float, default=0.5)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"), nullable=False, index=True
    )

    organization: Mapped["Organization"] = relationship(back_populates="regions")
    readings: Mapped[list["EnvironmentalReading"]] = relationship(back_populates="region")
    risk_assessments: Mapped[list["RiskAssessment"]] = relationship(back_populates="region")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="region")

    __table_args__ = (Index("ix_regions_org_name", "organization_id", "name"),)
