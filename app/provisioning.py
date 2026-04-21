import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta, timezone

from app.db.main_db import init_enterprise_db, create_database
from app.db.dynamic_gps_db import init_enterprise_location_db
from app.api.user.user_model import User
from app.api.enterprise.enterprise_model import Enterprise
from app.api.enterprise_user.enterprise_user_model import EnterpriseUserLink
from app.utils.login_user_utils import get_password_hash
from app.auth.dependencies import AsyncSessionMain

logger = logging.getLogger("app_logger")

async def seed_demo_data():
    """Seeds the initial 'demo' enterprise and 'admin' user using async sessions"""
    async with AsyncSessionMain() as session:
        # Check if Demo enterprise exists
        result = await session.execute(select(Enterprise).where(Enterprise.name == "demo"))
        demo_ent = result.scalar_one_or_none()
        
        if not demo_ent:
            logger.info("Sembrando empresa 'demo'...")
            demo_ent = Enterprise(
                name="demo", 
                fullname="Empresa Demo S.A.", 
                lat=-34.6037, 
                lon=-58.3816
            )
            session.add(demo_ent)
            await session.commit()
            await session.refresh(demo_ent)
            
            # Ensure the tenant DB exists for the new enterprise (uses ID 1)
            # init_enterprise_location_db handles the creation and schema init
            await init_enterprise_location_db(demo_ent.id)
        
        # Check if admin user exists
        result = await session.execute(select(User).where(User.email == "admin@gps.com"))
        admin_user = result.scalar_one_or_none()
        
        if not admin_user:
            logger.info("Sembrando usuario 'admin'...")
            admin_user = User(
                name="Administrador",
                email="admin@gps.com",
                password=get_password_hash("admin123"),
                expiration_date=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=30),
                alive=True
            )
            session.add(admin_user)
            await session.commit()
            await session.refresh(admin_user)
            
            # Link user to demo enterprise
            link = EnterpriseUserLink(enterprise_id=demo_ent.id, user_id=admin_user.id, role="admin")
            session.add(link)
            await session.commit()
            
    logger.info("Finalizado proceso de seeding asíncrono.")

async def perform_initial_setup():
    """Wrapper for all initial setup"""
    # These are sync (from main_db.py)
    create_database()
    init_enterprise_db()
    
    # This is async
    await seed_demo_data()
