from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RiskAssessmentResponse(BaseModel):
    id: int
    region_id: int
    calculated_risk: float
    flood_probability: float
    drought_probability: float
    confidence_score: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ForecastResponse(BaseModel):
    region_id: int
    flood_probability: float
    drought_probability: float
    confidence_score: float
    horizon_days: int
