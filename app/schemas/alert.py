from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AlertResponse(BaseModel):
    id: int
    region_id: int
    level: str
    message: str
    acknowledged: bool
    organization_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AlertAcknowledge(BaseModel):
    acknowledged: bool = True
