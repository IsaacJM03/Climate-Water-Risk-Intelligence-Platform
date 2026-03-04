import asyncio
from sqlalchemy import select

from app.core.database import get_sessionmaker
from app.models.user import User
from app.models.organization import Organization
from app.core.security import hash_password

async def main():
    session_maker = get_sessionmaker()
    async with session_maker() as db:
        # Ensure there is at least one organization to satisfy FK constraints
        org_result = await db.execute(select(Organization).limit(1))
        org = org_result.scalars().first()
        if org is None:
            org = Organization(name="Default Organization", type="NGO")
            db.add(org)
            await db.flush()

        # Create admin user if it doesn't already exist
        user_result = await db.execute(select(User).where(User.email == "admin@example.com"))
        existing_user = user_result.scalars().first()
        if existing_user is None:
            user = User(
                email="admin@example.com",
                hashed_password=hash_password("admin"),
                role="admin",
                organization_id=org.id,
            )
            db.add(user)
            await db.commit()
        else:
            print("admin user already exists, skipping")

asyncio.run(main())