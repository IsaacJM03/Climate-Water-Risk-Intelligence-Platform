from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ReadingCreate(BaseModel):
    latitude: float
    longitude: float
    rainfall: float = 0.0
    temperature: float = 0.0
    water_level: float = 0.0
    recorded_at: Optional[datetime] = None


class ReadingResponse(BaseModel):
    id: int
    latitude: float
    longitude: float
    rainfall: float
    temperature: float
    water_level: float
    recorded_at: datetime
    region_id: int
    organization_id: int

    model_config = ConfigDict(from_attributes=True)
