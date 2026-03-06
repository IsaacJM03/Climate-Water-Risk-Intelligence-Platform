from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Protocol, runtime_checkable

import numpy as np
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reading import EnvironmentalReading
from app.models.region import Region
from app.schemas.risk import ForecastResponse

logger = logging.getLogger(__name__)


@runtime_checkable
class ForecastStrategy(Protocol):
    def predict(self, values: list[float]) -> tuple[float, float]:
        """Returns (prediction, confidence)."""
        ...


class MovingAverageForecast:
    window: int = 7

    def predict(self, values: list[float]) -> tuple[float, float]:
        if not values:
            return 0.0, 0.0
        window = min(self.window, len(values))
        prediction = float(np.mean(values[-window:]))
        # Confidence based on data volume relative to window
        confidence = min(len(values) / self.window, 1.0)
        return prediction, confidence


class LinearRegressionForecast:
    def predict(self, values: list[float]) -> tuple[float, float]:
        if not values:
            return 0.0, 0.0
        if len(values) == 1:
            return values[0], 0.5

        x = np.arange(len(values), dtype=float)
        y = np.array(values, dtype=float)

        # Fit degree-1 polynomial (linear regression)
        coeffs = np.polyfit(x, y, deg=1)
        next_x = float(len(values))
        prediction = float(np.polyval(coeffs, next_x))

        # R² as confidence proxy
        y_hat = np.polyval(coeffs, x)
        ss_res = float(np.sum((y - y_hat) ** 2))
        ss_tot = float(np.sum((y - np.mean(y)) ** 2))
        r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 1.0
        confidence = max(0.0, min(r_squared, 1.0))

        return prediction, confidence


class ForecastEngine:
    def __init__(self, strategy: ForecastStrategy | None = None) -> None:
        self.strategy: ForecastStrategy = strategy or LinearRegressionForecast()

    async def forecast_region(
        self,
        db: AsyncSession,
        region_id: int,
        org_id: int,
        horizon_days: int = 7,
    ) -> ForecastResponse:
        # Validate region belongs to org
        region_result = await db.execute(
            select(Region).where(
                and_(Region.id == region_id, Region.organization_id == org_id)
            )
        )
        region = region_result.scalar_one_or_none()
        if region is None:
            raise ValueError(f"Region {region_id} not found for org {org_id}")

        # Fetch daily aggregates for last 30 days
        since = datetime.utcnow() - timedelta(days=30)
        result = await db.execute(
            select(
                func.date(EnvironmentalReading.recorded_at).label("day"),
                func.avg(EnvironmentalReading.rainfall).label("avg_rainfall"),
                func.avg(EnvironmentalReading.water_level).label("avg_water_level"),
                func.avg(EnvironmentalReading.temperature).label("avg_temperature"),
            )
            .where(
                and_(
                    EnvironmentalReading.region_id == region_id,
                    EnvironmentalReading.recorded_at >= since,
                )
            )
            .group_by(func.date(EnvironmentalReading.recorded_at))
            .order_by(func.date(EnvironmentalReading.recorded_at))
        )
        rows = result.all()

        if not rows:
            return ForecastResponse(
                region_id=region_id,
                flood_probability=0.0,
                drought_probability=0.0,
                confidence_score=0.0,
                horizon_days=horizon_days,
            )

        rainfall_series = [float(r.avg_rainfall or 0) for r in rows]
        water_series = [float(r.avg_water_level or 0) for r in rows]
        temp_series = [float(r.avg_temperature or 25) for r in rows]

        # Predict next value for each metric
        pred_rainfall, conf_r = self.strategy.predict(rainfall_series)
        pred_water, conf_w = self.strategy.predict(water_series)
        pred_temp, conf_t = self.strategy.predict(temp_series)

        _RAINFALL_THRESHOLD = 150.0
        _WATER_THRESHOLD = 5.0
        _TEMP_BASELINE = 25.0

        flood_prob = min(
            (
                max(pred_rainfall, 0) / _RAINFALL_THRESHOLD * 0.5
                + max(pred_water, 0) / _WATER_THRESHOLD * 0.5
            ),
            1.0,
        )

        # Drought: low rainfall trend + high temperature deviation
        drought_from_rain = max(0.0, 1.0 - max(pred_rainfall, 0) / _RAINFALL_THRESHOLD)
        drought_from_temp = min(abs(pred_temp - _TEMP_BASELINE) / 25.0, 1.0)
        drought_prob = min(drought_from_rain * 0.6 + drought_from_temp * 0.4, 1.0)

        confidence = float(np.mean([conf_r, conf_w, conf_t]))

        logger.info(
            "Forecast region=%d flood=%.4f drought=%.4f conf=%.4f",
            region_id,
            flood_prob,
            drought_prob,
            confidence,
        )

        return ForecastResponse(
            region_id=region_id,
            flood_probability=round(flood_prob, 4),
            drought_probability=round(drought_prob, 4),
            confidence_score=round(confidence, 4),
            horizon_days=horizon_days,
        )


def get_forecast_engine() -> ForecastEngine:
    return ForecastEngine()
