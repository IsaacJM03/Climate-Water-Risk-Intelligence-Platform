from __future__ import annotations

from datetime import datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization
from app.models.reading import EnvironmentalReading
from app.models.region import Region
from app.services.risk_engine import RiskEngine


class TestRiskEngineScoring:
    def test_score_rainfall_zero(self):
        engine = RiskEngine()
        assert engine._score_rainfall(0) == 0.0

    def test_score_rainfall_max(self):
        engine = RiskEngine()
        assert engine._score_rainfall(150) == 100.0

    def test_score_rainfall_overflow(self):
        engine = RiskEngine()
        assert engine._score_rainfall(300) == 100.0

    def test_score_rainfall_midpoint(self):
        engine = RiskEngine()
        assert engine._score_rainfall(75) == pytest.approx(50.0)

    def test_score_rainfall_negative(self):
        engine = RiskEngine()
        assert engine._score_rainfall(-10) == 0.0

    def test_score_water_level_zero(self):
        engine = RiskEngine()
        assert engine._score_water_level(0) == 0.0

    def test_score_water_level_half(self):
        engine = RiskEngine()
        assert engine._score_water_level(2.5) == pytest.approx(50.0)

    def test_score_water_level_max(self):
        engine = RiskEngine()
        assert engine._score_water_level(5.0) == 100.0

    def test_score_water_level_overflow(self):
        engine = RiskEngine()
        assert engine._score_water_level(10.0) == 100.0

    def test_score_water_level_negative(self):
        engine = RiskEngine()
        assert engine._score_water_level(-1.0) == 0.0

    def test_score_temperature_at_baseline(self):
        engine = RiskEngine()
        assert engine._score_temperature(25.0) == 0.0

    def test_score_temperature_high(self):
        engine = RiskEngine()
        # 50°C: deviation = 25, score = 100
        assert engine._score_temperature(50.0) == 100.0

    def test_score_temperature_low(self):
        engine = RiskEngine()
        # 0°C: deviation = 25, score = 100
        assert engine._score_temperature(0.0) == 100.0

    def test_score_temperature_mild_deviation(self):
        engine = RiskEngine()
        # 37.5°C: deviation = 12.5 → score = 50
        assert engine._score_temperature(37.5) == pytest.approx(50.0)


class TestRiskEngineAggregate:
    def test_aggregate_readings_empty(self):
        engine = RiskEngine()
        result = engine._aggregate_readings([])
        assert result["avg_rainfall"] == 0.0
        assert result["avg_water_level"] == 0.0
        assert result["avg_temperature"] == 25.0

    def test_aggregate_readings_values(self):
        engine = RiskEngine()

        class FakeReading:
            def __init__(self, rainfall, water_level, temperature):
                self.rainfall = rainfall
                self.water_level = water_level
                self.temperature = temperature

        readings = [
            FakeReading(100.0, 3.0, 30.0),
            FakeReading(200.0, 5.0, 20.0),
        ]
        result = engine._aggregate_readings(readings)
        assert result["avg_rainfall"] == pytest.approx(150.0)
        assert result["avg_water_level"] == pytest.approx(4.0)
        assert result["avg_temperature"] == pytest.approx(25.0)


@pytest.mark.asyncio
class TestRiskEngineCompute:
    async def test_risk_calculation_no_readings(
        self,
        test_db: AsyncSession,
        sample_region: Region,
        sample_org: Organization,
    ):
        """Should return near-zero risk when no readings exist."""
        engine = RiskEngine()
        assessment = await engine.compute_region_risk(
            test_db, sample_region.id, sample_org.id
        )
        assert assessment.calculated_risk == pytest.approx(0.0)
        assert assessment.confidence_score == 0.0

    async def test_risk_calculation_with_readings(
        self,
        test_db: AsyncSession,
        sample_region: Region,
        sample_org: Organization,
        sample_readings,
    ):
        """Should return non-zero risk when readings are present."""
        engine = RiskEngine()
        assessment = await engine.compute_region_risk(
            test_db, sample_region.id, sample_org.id
        )
        assert assessment.calculated_risk >= 0.0
        assert assessment.calculated_risk <= 100.0
        assert 0.0 <= assessment.flood_probability <= 1.0
        assert 0.0 <= assessment.drought_probability <= 1.0
        assert 0.0 <= assessment.confidence_score <= 1.0

    async def test_risk_calculation_wrong_org(
        self,
        test_db: AsyncSession,
        sample_region: Region,
    ):
        """Should raise ValueError for wrong org_id."""
        engine = RiskEngine()
        with pytest.raises(ValueError, match="not found"):
            await engine.compute_region_risk(test_db, sample_region.id, org_id=99999)

    async def test_risk_clamped_to_100(
        self,
        test_db: AsyncSession,
        sample_org: Organization,
    ):
        """High-vulnerability region with extreme readings should be clamped to 100."""
        region = Region(
            name="Extreme Region",
            population=1000,
            vulnerability_index=1.0,  # multiplier = 1.5
            organization_id=sample_org.id,
        )
        test_db.add(region)
        await test_db.flush()
        await test_db.refresh(region)

        # Add an extreme reading
        reading = EnvironmentalReading(
            latitude=0.0,
            longitude=0.0,
            rainfall=300.0,    # well above 150 mm threshold
            temperature=60.0,  # extreme heat
            water_level=10.0,  # well above 5 m threshold
            recorded_at=datetime.utcnow(),
            region_id=region.id,
            organization_id=sample_org.id,
        )
        test_db.add(reading)
        await test_db.flush()

        engine = RiskEngine()
        assessment = await engine.compute_region_risk(
            test_db, region.id, sample_org.id
        )
        assert assessment.calculated_risk == pytest.approx(100.0)
