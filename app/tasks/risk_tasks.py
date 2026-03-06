from __future__ import annotations

import logging

from app.core.database import AsyncSessionLocal
from app.realtime.manager import manager
from app.services.risk_engine import get_risk_engine

logger = logging.getLogger(__name__)


async def recalculate_region_risk(region_id: int, org_id: int) -> None:
    """Background task: recalculate risk for a region after a new reading."""
    async with AsyncSessionLocal() as db:
        try:
            engine = get_risk_engine()
            assessment = await engine.compute_region_risk(db, region_id, org_id)
            await db.commit()

            # Invalidate Redis cache
            try:
                from app.main import app  # lazy import to avoid circular deps

                redis = getattr(app.state, "redis", None)
                if redis is not None:
                    cache_key = f"risk:{org_id}:{region_id}"
                    await redis.delete(cache_key)
            except Exception as exc:
                logger.warning("Cache invalidation failed: %s", exc)

            # Broadcast via WebSocket
            await manager.broadcast_to_org(
                org_id,
                {
                    "event": "risk_update",
                    "region_id": region_id,
                    "calculated_risk": assessment.calculated_risk,
                    "flood_probability": assessment.flood_probability,
                    "drought_probability": assessment.drought_probability,
                    "confidence_score": assessment.confidence_score,
                },
            )
        except Exception as exc:
            await db.rollback()
            logger.error("Risk recalculation failed region=%d: %s", region_id, exc)


async def run_all_risk_assessments() -> None:
    """Periodic task: assess risk for all regions."""
    from sqlalchemy import select

    from app.models.region import Region

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Region))
        regions = result.scalars().all()

    for region in regions:
        try:
            await recalculate_region_risk(region.id, region.organization_id)
        except Exception as exc:
            logger.error(
                "Periodic risk assessment failed region=%d: %s", region.id, exc
            )
