import asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.main_db import AsyncSessionMain
from app.api.user.user_model import User
from app.api.user.user_schema import UserCreate
from app.utils.login_user_utils import get_password_hash

async def verify():
    print("Verifying datetime fix...")
    async with AsyncSessionMain() as session:
        # 1. Check admin user created during seeding
        result = await session.execute(select(User).where(User.email == "admin@gps.com"))
        admin = result.scalar_one_or_none()
        if admin:
            print(f"Admin user found. created_at: {admin.created_at}, expiration_date: {admin.expiration_date}")
            assert admin.created_at.tzinfo is None
            assert admin.expiration_date.tzinfo is None
            print("Admin user datetimes are naive (SUCCESS)")
        else:
            print("Admin user NOT found!")

        # 2. Simulate registration
        print("Simulating user registration...")
        test_email = f"test_{int(datetime.now().timestamp())}@example.com"
        new_user = User(
            name="Test User",
            email=test_email,
            password=get_password_hash("test123"),
            expiration_date=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=30),
            alive=True
        )
        session.add(new_user)
        try:
            await session.commit()
            print(f"Registration simulation SUCCESS for {test_email}")
        except Exception as e:
            print(f"Registration simulation FAILED: {e}")
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(verify())
