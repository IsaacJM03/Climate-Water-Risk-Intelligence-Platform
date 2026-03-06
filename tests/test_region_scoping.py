from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.organization import Organization
from app.models.reading import EnvironmentalReading
from app.models.region import Region
from app.models.risk import RiskAssessment
from app.services.risk_engine import RiskEngine


class TestOrganizationScoping:
    """Ensure all data access is correctly scoped to organization_id."""

    @pytest.mark.asyncio
    async def test_region_belongs_to_different_org(
        self,
        test_db: AsyncSession,
        sample_region: Region,
    ):
        """
        Accessing a region with the wrong org_id should raise ValueError
        (which the API layer converts to 404).
        """
        wrong_org_id = sample_region.organization_id + 9999
        engine = RiskEngine()
        with pytest.raises(ValueError, match="not found"):
            await engine.compute_region_risk(
                test_db, sample_region.id, org_id=wrong_org_id
            )

    @pytest.mark.asyncio
    async def test_readings_scoped_to_org(
        self,
        test_db: AsyncSession,
        sample_org: Organization,
        sample_region: Region,
        sample_readings: list[EnvironmentalReading],
    ):
        """Readings fetched by organization_id must only return that org's data."""
        # Create a second org with its own region and reading
        other_org = Organization(name="Other Org", type="NGO")
        test_db.add(other_org)
        await test_db.flush()
        await test_db.refresh(other_org)

        other_region = Region(
            name="Other Region",
            population=100,
            vulnerability_index=0.5,
            organization_id=other_org.id,
        )
        test_db.add(other_region)
        await test_db.flush()
        await test_db.refresh(other_region)

        from datetime import datetime

        other_reading = EnvironmentalReading(
            latitude=1.0,
            longitude=1.0,
            rainfall=10.0,
            temperature=25.0,
            water_level=1.0,
            recorded_at=datetime.utcnow(),
            region_id=other_region.id,
            organization_id=other_org.id,
        )
        test_db.add(other_reading)
        await test_db.flush()

        # Fetch readings for sample_org only
        result = await test_db.execute(
            select(EnvironmentalReading).where(
                EnvironmentalReading.organization_id == sample_org.id
            )
        )
        org_readings = result.scalars().all()

        org_ids = {r.organization_id for r in org_readings}
        assert org_ids == {sample_org.id}, "Readings contain data from a different org"

        # Readings for other_org should NOT be in sample_org results
        reading_ids = {r.id for r in org_readings}
        assert other_reading.id not in reading_ids

    @pytest.mark.asyncio
    async def test_risk_assessment_org_isolation(
        self,
        test_db: AsyncSession,
        sample_org: Organization,
        sample_region: Region,
        sample_readings: list[EnvironmentalReading],
    ):
        """Risk assessments computed for org A must not appear in org B queries."""
        # Create a second org and region
        org_b = Organization(name="Org B", type="government")
        test_db.add(org_b)
        await test_db.flush()
        await test_db.refresh(org_b)

        region_b = Region(
            name="Region B",
            population=200,
            vulnerability_index=0.5,
            organization_id=org_b.id,
        )
        test_db.add(region_b)
        await test_db.flush()
        await test_db.refresh(region_b)

        # Compute risk for sample_org
        engine = RiskEngine()
        assessment = await engine.compute_region_risk(
            test_db, sample_region.id, sample_org.id
        )
        assert assessment.region_id == sample_region.id

        # Query assessments linked to regions belonging to org_b
        result = await test_db.execute(
            select(RiskAssessment)
            .join(Region, RiskAssessment.region_id == Region.id)
            .where(Region.organization_id == org_b.id)
        )
        org_b_assessments = result.scalars().all()
        assessment_ids = {a.id for a in org_b_assessments}
        assert assessment.id not in assessment_ids, (
            "Risk assessment for org A leaked into org B query"
        )

    @pytest.mark.asyncio
    async def test_alert_scoped_to_org(
        self,
        test_db: AsyncSession,
        sample_org: Organization,
        sample_region: Region,
    ):
        """Alerts created for org A should not be visible when querying org B."""
        alert = Alert(
            region_id=sample_region.id,
            level="high",
            message="Test alert",
            acknowledged=False,
            organization_id=sample_org.id,
        )
        test_db.add(alert)
        await test_db.flush()
        await test_db.refresh(alert)

        # Query with wrong org_id
        wrong_org_id = sample_org.id + 9999
        result = await test_db.execute(
            select(Alert).where(Alert.organization_id == wrong_org_id)
        )
        wrong_org_alerts = result.scalars().all()
        alert_ids = {a.id for a in wrong_org_alerts}
        assert alert.id not in alert_ids, "Alert leaked into wrong org query"

    @pytest.mark.asyncio
    async def test_region_list_org_isolation(
        self,
        test_db: AsyncSession,
        sample_org: Organization,
        sample_region: Region,
    ):
        """Listing regions for org A should not return regions from org B."""
        org_b = Organization(name="Org B isolate", type="NGO")
        test_db.add(org_b)
        await test_db.flush()
        await test_db.refresh(org_b)

        region_b = Region(
            name="Region B isolate",
            population=50,
            vulnerability_index=0.3,
            organization_id=org_b.id,
        )
        test_db.add(region_b)
        await test_db.flush()
        await test_db.refresh(region_b)

        result = await test_db.execute(
            select(Region).where(Region.organization_id == sample_org.id)
        )
        org_a_regions = result.scalars().all()
        org_a_region_ids = {r.id for r in org_a_regions}

        assert region_b.id not in org_a_region_ids
        assert sample_region.id in org_a_region_ids
