from __future__ import annotations

from datetime import datetime

from sqlalchemy import Float, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id: Mapped[int] = mapped_column(primary_key=True)
    region_id: Mapped[int] = mapped_column(
        ForeignKey("regions.id"), nullable=False, index=True
    )
    calculated_risk: Mapped[float] = mapped_column(Float, nullable=False)
    flood_probability: Mapped[float] = mapped_column(Float, nullable=False)
    drought_probability: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.utcnow(), index=True)

    region: Mapped["Region"] = relationship(back_populates="risk_assessments")
