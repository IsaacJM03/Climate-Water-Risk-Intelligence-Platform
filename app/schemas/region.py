from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


class RegionCreate(BaseModel):
    name: str
    population: int = 0
    vulnerability_index: float = 0.5
    boundary: Optional[str] = None


class RegionResponse(BaseModel):
    id: int
    name: str
    population: int
    vulnerability_index: float
    organization_id: int
    boundary: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
