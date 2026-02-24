from __future__ import annotations

import pytest

from app.services.forecast_engine import (
    ForecastEngine,
    LinearRegressionForecast,
    MovingAverageForecast,
)


class TestLinearRegressionForecast:
    def test_predict_increasing_trend(self):
        forecast = LinearRegressionForecast()
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        pred, conf = forecast.predict(values)
        assert pred > 50.0
        assert 0.0 <= conf <= 1.0

    def test_predict_decreasing_trend(self):
        forecast = LinearRegressionForecast()
        values = [50.0, 40.0, 30.0, 20.0, 10.0]
        pred, conf = forecast.predict(values)
        assert pred < 10.0
        assert 0.0 <= conf <= 1.0

    def test_predict_flat_trend(self):
        forecast = LinearRegressionForecast()
        values = [25.0, 25.0, 25.0, 25.0, 25.0]
        pred, conf = forecast.predict(values)
        assert pred == pytest.approx(25.0, abs=0.1)

    def test_predict_single_value(self):
        forecast = LinearRegressionForecast()
        values = [42.0]
        pred, conf = forecast.predict(values)
        assert pred == pytest.approx(42.0)
        assert conf == pytest.approx(0.5)

    def test_predict_empty(self):
        forecast = LinearRegressionForecast()
        pred, conf = forecast.predict([])
        assert pred == 0.0
        assert conf == 0.0

    def test_confidence_is_r_squared(self):
        forecast = LinearRegressionForecast()
        # Perfect linear sequence → R² should be ~1.0
        values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]
        _, conf = forecast.predict(values)
        assert conf == pytest.approx(1.0, abs=0.01)

    def test_confidence_bounded(self):
        import random

        forecast = LinearRegressionForecast()
        random.seed(42)
        noisy = [random.gauss(10, 5) for _ in range(20)]
        _, conf = forecast.predict(noisy)
        assert 0.0 <= conf <= 1.0


class TestMovingAverageForecast:
    def test_predict_uses_last_window(self):
        ma = MovingAverageForecast()
        values = [1.0, 1.0, 1.0, 100.0, 100.0, 100.0, 100.0]
        pred, _ = ma.predict(values)
        # Last 7 items: window = 7, mean includes the 1.0s
        assert pred == pytest.approx(sum(values[-7:]) / 7, abs=0.01)

    def test_predict_empty(self):
        ma = MovingAverageForecast()
        pred, conf = ma.predict([])
        assert pred == 0.0
        assert conf == 0.0

    def test_predict_less_than_window(self):
        ma = MovingAverageForecast()
        values = [10.0, 20.0, 30.0]
        pred, conf = ma.predict(values)
        assert pred == pytest.approx(20.0)
        assert 0.0 <= conf <= 1.0

    def test_confidence_grows_with_data(self):
        ma = MovingAverageForecast()
        short_values = [10.0, 20.0]
        long_values = [10.0] * 14  # 2x window
        _, short_conf = ma.predict(short_values)
        _, long_conf = ma.predict(long_values)
        assert long_conf >= short_conf

    def test_predict_single_value(self):
        ma = MovingAverageForecast()
        pred, conf = ma.predict([55.0])
        assert pred == pytest.approx(55.0)


class TestForecastEngineIntegration:
    def test_default_strategy_is_linear_regression(self):
        engine = ForecastEngine()
        assert isinstance(engine.strategy, LinearRegressionForecast)

    def test_custom_strategy_injection(self):
        ma = MovingAverageForecast()
        engine = ForecastEngine(strategy=ma)
        assert engine.strategy is ma

    @pytest.mark.asyncio
    async def test_forecast_no_data(
        self,
        test_db,
        sample_region,
        sample_org,
    ):
        """Returns zero probabilities when no historical readings exist."""
        engine = ForecastEngine()
        result = await engine.forecast_region(
            test_db, sample_region.id, sample_org.id, horizon_days=7
        )
        assert result.flood_probability == 0.0
        assert result.drought_probability == 0.0
        assert result.confidence_score == 0.0
        assert result.horizon_days == 7

    @pytest.mark.asyncio
    async def test_forecast_wrong_org(
        self,
        test_db,
        sample_region,
    ):
        """Should raise ValueError for wrong org_id."""
        engine = ForecastEngine()
        with pytest.raises(ValueError, match="not found"):
            await engine.forecast_region(
                test_db, sample_region.id, org_id=99999, horizon_days=7
            )

    @pytest.mark.asyncio
    async def test_forecast_with_readings(
        self,
        test_db,
        sample_region,
        sample_org,
        sample_readings,
    ):
        engine = ForecastEngine()
        result = await engine.forecast_region(
            test_db, sample_region.id, sample_org.id, horizon_days=14
        )
        assert 0.0 <= result.flood_probability <= 1.0
        assert 0.0 <= result.drought_probability <= 1.0
        assert 0.0 <= result.confidence_score <= 1.0
        assert result.horizon_days == 14
