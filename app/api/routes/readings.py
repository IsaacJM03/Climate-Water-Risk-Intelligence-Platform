from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models.reading import EnvironmentalReading
from app.models.region import Region
from app.models.user import User
from app.schemas.reading import ReadingCreate, ReadingResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/readings", tags=["readings"])


@router.post("", response_model=ReadingResponse, status_code=status.HTTP_201_CREATED)
async def ingest_reading(
    payload: ReadingCreate,
    region_id: int,
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ReadingResponse:
    # Validate region belongs to org
    region_result = await db.execute(
        select(Region).where(
            and_(
                Region.id == region_id,
                Region.organization_id == current_user.organization_id,
            )
        )
    )
    if region_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Region not found")

    recorded_at = payload.recorded_at or datetime.utcnow()
    reading = EnvironmentalReading(
        latitude=payload.latitude,
        longitude=payload.longitude,
        rainfall=payload.rainfall,
        temperature=payload.temperature,
        water_level=payload.water_level,
        recorded_at=recorded_at,
        region_id=region_id,
        organization_id=current_user.organization_id,
    )
    db.add(reading)
    await db.flush()
    await db.refresh(reading)

    # Invalidate Redis cache for region risk
    redis = getattr(request.app.state, "redis", None)
    if redis is not None:
        cache_key = f"risk:{current_user.organization_id}:{region_id}"
        await redis.delete(cache_key)

    # Trigger background risk recalculation
    from app.tasks.risk_tasks import recalculate_region_risk

    background_tasks.add_task(
        recalculate_region_risk,
        region_id=region_id,
        org_id=current_user.organization_id,
    )

    return ReadingResponse.model_validate(reading)


@router.get("", response_model=list[ReadingResponse])
async def list_readings(
    region_id: int | None = None,
    page: int = 1,
    page_size: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[ReadingResponse]:
    query = select(EnvironmentalReading).where(
        EnvironmentalReading.organization_id == current_user.organization_id
    )
    if region_id is not None:
        query = query.where(EnvironmentalReading.region_id == region_id)
    query = (
        query.order_by(EnvironmentalReading.recorded_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    readings = result.scalars().all()
    return [ReadingResponse.model_validate(r) for r in readings]
