from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.models.alert import Alert
from app.models.organization import Organization
from app.models.reading import EnvironmentalReading
from app.models.region import Region
from app.models.risk import RiskAssessment
from app.models.user import User
from app.services.forecast_engine import ForecastEngine, get_forecast_engine
from app.services.risk_engine import RiskEngine, get_risk_engine

# ---------------------------------------------------------------------------
# Use SQLite in-memory for testing (async via aiosqlite)
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Use a single event loop for the whole test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def test_db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional test session that rolls back after each test."""
    SessionFactory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
    async with SessionFactory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def sample_org(test_db: AsyncSession) -> Organization:
    org = Organization(name="Test Church", type="church")
    test_db.add(org)
    await test_db.flush()
    await test_db.refresh(org)
    return org


@pytest_asyncio.fixture
async def sample_region(test_db: AsyncSession, sample_org: Organization) -> Region:
    region = Region(
        name="River Valley",
        population=5000,
        vulnerability_index=0.7,
        organization_id=sample_org.id,
    )
    test_db.add(region)
    await test_db.flush()
    await test_db.refresh(region)
    return region


@pytest_asyncio.fixture
async def sample_readings(
    test_db: AsyncSession,
    sample_region: Region,
    sample_org: Organization,
) -> list[EnvironmentalReading]:
    now = datetime.utcnow()
    readings = []
    for i in range(20):
        r = EnvironmentalReading(
            latitude=0.0 + i * 0.01,
            longitude=0.0 + i * 0.01,
            rainfall=float(50 + i * 5),       # 50..145 mm
            temperature=float(22 + i * 0.5),  # 22..31.5 °C
            water_level=float(1.0 + i * 0.1), # 1.0..2.9 m
            recorded_at=now - timedelta(hours=i),
            region_id=sample_region.id,
            organization_id=sample_org.id,
        )
        test_db.add(r)
        readings.append(r)
    await test_db.flush()
    for r in readings:
        await test_db.refresh(r)
    return readings


@pytest.fixture
def risk_engine() -> RiskEngine:
    return get_risk_engine()


@pytest.fixture
def forecast_engine() -> ForecastEngine:
    return get_forecast_engine()
