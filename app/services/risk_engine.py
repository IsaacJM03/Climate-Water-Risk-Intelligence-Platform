from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.alert import Alert
from app.models.reading import EnvironmentalReading
from app.models.region import Region
from app.models.risk import RiskAssessment

logger = logging.getLogger(__name__)

_RAINFALL_THRESHOLD = 150.0   # mm → score 100
_WATER_LEVEL_THRESHOLD = 5.0  # m  → score 100
_TEMP_BASELINE = 25.0          # °C baseline (no risk)
_TEMP_RANGE = 25.0             # ±25°C deviation → score 100


class RiskEngine:
    """
    Computes risk scores from environmental readings.

    Risk formula:
      base_score = weighted average of:
        - rainfall_score    (normalized 0-100, threshold 150 mm)
        - water_level_score (normalized 0-100, threshold 5.0 m)
        - temperature_score (normalized 0-100, deviation from 25 °C)

      final_risk = base_score * vulnerability_index (mapped from 0-1 → 0.5-1.5)
      clamped to [0, 100]
    """

    async def compute_region_risk(
        self,
        db: AsyncSession,
        region_id: int,
        org_id: int,
    ) -> RiskAssessment:
        # 1. Fetch region with org check
        result = await db.execute(
            select(Region).where(
                and_(Region.id == region_id, Region.organization_id == org_id)
            )
        )
        region = result.scalar_one_or_none()
        if region is None:
            raise ValueError(f"Region {region_id} not found for org {org_id}")

        # 2. Fetch last 24 h readings
        since = datetime.utcnow() - timedelta(hours=24)
        readings_result = await db.execute(
            select(EnvironmentalReading).where(
                and_(
                    EnvironmentalReading.region_id == region_id,
                    EnvironmentalReading.recorded_at >= since,
                )
            )
        )
        readings = readings_result.scalars().all()

        # 3. Aggregate
        aggregated = self._aggregate_readings(list(readings))

        # 4 & 5. Score and apply vulnerability weighting
        rainfall_score = self._score_rainfall(aggregated["avg_rainfall"])
        water_score = self._score_water_level(aggregated["avg_water_level"])
        temp_score = self._score_temperature(aggregated["avg_temperature"])

        base_score = (rainfall_score * 0.4 + water_score * 0.4 + temp_score * 0.2)

        # Map vulnerability_index [0,1] → multiplier [0.5, 1.5]
        multiplier = 0.5 + region.vulnerability_index
        final_risk = min(max(base_score * multiplier, 0.0), 100.0)

        # Derive probabilities
        flood_prob = min((rainfall_score * 0.5 + water_score * 0.5) / 100.0, 1.0)
        drought_prob = min(
            max(
                (100.0 - aggregated["avg_rainfall"] / _RAINFALL_THRESHOLD * 100.0)
                * (temp_score / 100.0)
                / 100.0,
                0.0,
            ),
            1.0,
        )
        confidence = min(len(readings) / 24.0, 1.0)  # Full confidence with 24 readings

        # 6. Persist RiskAssessment
        assessment = RiskAssessment(
            region_id=region_id,
            calculated_risk=round(final_risk, 2),
            flood_probability=round(flood_prob, 4),
            drought_probability=round(drought_prob, 4),
            confidence_score=round(confidence, 4),
        )
        db.add(assessment)
        await db.flush()
        await db.refresh(assessment)

        logger.info(
            "Risk computed region=%d risk=%.2f flood=%.4f drought=%.4f",
            region_id,
            final_risk,
            flood_prob,
            drought_prob,
        )
        return assessment

    # ------------------------------------------------------------------
    # Scoring helpers
    # ------------------------------------------------------------------

    def _score_rainfall(self, rainfall_mm: float) -> float:
        """0-100 scale; 150 mm maps to 100."""
        if rainfall_mm <= 0:
            return 0.0
        return min(rainfall_mm / _RAINFALL_THRESHOLD * 100.0, 100.0)

    def _score_water_level(self, level: float) -> float:
        """0-100 scale; 5.0 m maps to 100."""
        if level <= 0:
            return 0.0
        return min(level / _WATER_LEVEL_THRESHOLD * 100.0, 100.0)

    def _score_temperature(self, temp: float) -> float:
        """Deviation from 25 °C baseline; ±25 °C deviation maps to 100."""
        deviation = abs(temp - _TEMP_BASELINE)
        return min(deviation / _TEMP_RANGE * 100.0, 100.0)

    def _aggregate_readings(self, readings: list) -> dict:
        """Return dict with avg_rainfall, avg_water_level, avg_temperature."""
        if not readings:
            return {
                "avg_rainfall": 0.0,
                "avg_water_level": 0.0,
                "avg_temperature": _TEMP_BASELINE,
            }
        n = len(readings)
        return {
            "avg_rainfall": sum(r.rainfall for r in readings) / n,
            "avg_water_level": sum(r.water_level for r in readings) / n,
            "avg_temperature": sum(r.temperature for r in readings) / n,
        }


def get_risk_engine() -> RiskEngine:
    return RiskEngine()
