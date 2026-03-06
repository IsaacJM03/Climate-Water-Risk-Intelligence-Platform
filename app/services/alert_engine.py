from __future__ import annotations

import json
import logging
from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.alert import Alert
from app.models.region import Region

logger = logging.getLogger(__name__)

_THROTTLE_KEY_PREFIX = "alert_throttle:critical:"


class AlertEngine:
    """
    Creates alerts with throttling to prevent duplicate CRITICAL alerts.
    Throttle window: config.ALERT_THROTTLE_MINUTES
    """

    async def maybe_create_alert(
        self,
        db: AsyncSession,
        redis_client,
        region_id: int,
        org_id: int,
        risk_score: float,
        flood_prob: float,
        drought_prob: float,
    ) -> Optional[Alert]:
        level = self._determine_level(risk_score)
        if level is None:
            return None

        # Throttle CRITICAL alerts to avoid flooding
        if level == "critical":
            throttle_key = f"{_THROTTLE_KEY_PREFIX}{region_id}"
            if redis_client is not None:
                existing = await redis_client.get(throttle_key)
                if existing:
                    logger.debug("Alert throttled for region %d", region_id)
                    return None

        message = self._build_message(level, risk_score, flood_prob, drought_prob)
        alert = Alert(
            region_id=region_id,
            level=level,
            message=message,
            acknowledged=False,
            organization_id=org_id,
        )
        db.add(alert)
        await db.flush()
        await db.refresh(alert)

        # Set throttle key in Redis for CRITICAL alerts
        if level == "critical" and redis_client is not None:
            throttle_key = f"{_THROTTLE_KEY_PREFIX}{region_id}"
            await redis_client.setex(
                throttle_key,
                settings.ALERT_THROTTLE_MINUTES * 60,
                "1",
            )

        logger.info(
            "Alert created region=%d level=%s risk=%.2f",
            region_id,
            level,
            risk_score,
        )
        return alert

    def _determine_level(self, risk_score: float) -> Optional[str]:
        if risk_score >= 85:
            return "critical"
        if risk_score >= 70:
            return "high"
        if risk_score >= 50:
            return "medium"
        if risk_score >= 30:
            return "low"
        return None

    def _build_message(
        self,
        level: str,
        risk_score: float,
        flood_prob: float,
        drought_prob: float,
    ) -> str:
        flood_pct = round(flood_prob * 100, 1)
        drought_pct = round(drought_prob * 100, 1)
        base = (
            f"Risk level {level.upper()} detected. "
            f"Composite risk score: {risk_score:.1f}/100. "
            f"Flood probability: {flood_pct}%. "
            f"Drought probability: {drought_pct}%."
        )
        if level == "critical":
            base += " Immediate action required. Activate emergency response protocols."
        elif level == "high":
            base += " Heightened vigilance recommended. Prepare contingency resources."
        elif level == "medium":
            base += " Monitor conditions closely and review readiness plans."
        else:
            base += " Continue routine monitoring."
        return base

    async def acknowledge_alert(
        self, db: AsyncSession, alert_id: int, org_id: int
    ) -> Alert:
        result = await db.execute(
            select(Alert).where(
                and_(Alert.id == alert_id, Alert.organization_id == org_id)
            )
        )
        alert = result.scalar_one_or_none()
        if alert is None:
            raise ValueError(f"Alert {alert_id} not found for org {org_id}")
        alert.acknowledged = True
        await db.flush()
        await db.refresh(alert)
        return alert


def get_alert_engine() -> AlertEngine:
    return AlertEngine()
