from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models.alert import Alert
from app.models.user import User
from app.schemas.alert import AlertAcknowledge, AlertResponse
from app.services.alert_engine import get_alert_engine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertResponse])
async def list_alerts(
    level: Optional[str] = None,
    unacknowledged_only: bool = False,
    page: int = 1,
    page_size: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[AlertResponse]:
    query = select(Alert).where(Alert.organization_id == current_user.organization_id)
    if level is not None:
        query = query.where(Alert.level == level)
    if unacknowledged_only:
        query = query.where(Alert.acknowledged.is_(False))
    query = (
        query.order_by(Alert.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    alerts = result.scalars().all()
    return [AlertResponse.model_validate(a) for a in alerts]


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> AlertResponse:
    result = await db.execute(
        select(Alert).where(
            and_(
                Alert.id == alert_id,
                Alert.organization_id == current_user.organization_id,
            )
        )
    )
    alert = result.scalar_one_or_none()
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    return AlertResponse.model_validate(alert)


@router.post("/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: int,
    payload: AlertAcknowledge = AlertAcknowledge(),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> AlertResponse:
    engine = get_alert_engine()
    try:
        alert = await engine.acknowledge_alert(db, alert_id, current_user.organization_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return AlertResponse.model_validate(alert)
