from __future__ import annotations

import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_redis, require_role
from app.core.config import settings
from app.core.database import get_db
from app.models.region import Region
from app.models.risk import RiskAssessment
from app.models.user import User
from app.schemas.region import RegionCreate, RegionResponse
from app.schemas.risk import ForecastResponse, RiskAssessmentResponse
from app.services.forecast_engine import get_forecast_engine
from app.services.risk_engine import get_risk_engine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/regions", tags=["regions"])


@router.get("", response_model=list[RegionResponse])
async def list_regions(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[RegionResponse]:
    result = await db.execute(
        select(Region).where(Region.organization_id == current_user.organization_id)
    )
    regions = result.scalars().all()
    return [RegionResponse.model_validate(r) for r in regions]


@router.post(
    "",
    response_model=RegionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin", "analyst"))],
)
async def create_region(
    payload: RegionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> RegionResponse:
    region = Region(
        name=payload.name,
        population=payload.population,
        vulnerability_index=payload.vulnerability_index,
        boundary=payload.boundary,
        organization_id=current_user.organization_id,
    )
    db.add(region)
    await db.flush()
    await db.refresh(region)
    return RegionResponse.model_validate(region)


@router.get("/{region_id}", response_model=RegionResponse)
async def get_region(
    region_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> RegionResponse:
    result = await db.execute(
        select(Region).where(
            and_(
                Region.id == region_id,
                Region.organization_id == current_user.organization_id,
            )
        )
    )
    region = result.scalar_one_or_none()
    if region is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Region not found")
    return RegionResponse.model_validate(region)


@router.get("/{region_id}/risk", response_model=RiskAssessmentResponse)
async def get_region_risk(
    region_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> RiskAssessmentResponse:
    # Check org scoping
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

    # Try cache
    redis = getattr(request.app.state, "redis", None)
    cache_key = f"risk:{current_user.organization_id}:{region_id}"
    if redis is not None:
        cached = await redis.get(cache_key)
        if cached:
            data = json.loads(cached)
            return RiskAssessmentResponse(**data)

    # Fetch latest assessment from DB
    assessment_result = await db.execute(
        select(RiskAssessment)
        .where(RiskAssessment.region_id == region_id)
        .order_by(RiskAssessment.created_at.desc())
        .limit(1)
    )
    assessment = assessment_result.scalar_one_or_none()
    if assessment is None:
        # Compute on demand
        engine = get_risk_engine()
        try:
            assessment = await engine.compute_region_risk(
                db, region_id, current_user.organization_id
            )
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    response = RiskAssessmentResponse.model_validate(assessment)

    # Store in cache
    if redis is not None:
        await redis.setex(cache_key, settings.RISK_CACHE_TTL, response.model_dump_json())

    return response


@router.get("/{region_id}/forecast", response_model=ForecastResponse)
async def get_region_forecast(
    region_id: int,
    horizon_days: int = 7,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ForecastResponse:
    engine = get_forecast_engine()
    try:
        return await engine.forecast_region(
            db, region_id, current_user.organization_id, horizon_days
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete(
    "/{region_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("admin"))],
)
async def delete_region(
    region_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        select(Region).where(
            and_(
                Region.id == region_id,
                Region.organization_id == current_user.organization_id,
            )
        )
    )
    region = result.scalar_one_or_none()
    if region is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Region not found")
    await db.delete(region)
