import os
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from app.db.base_main import BaseMain
from app.utils.logger_config import logger

load_dotenv()

# We use the new env names from our updated .env
postgres_user = os.getenv('POSTGRES_USER')
postgres_password = os.getenv('POSTGRES_PASSWORD')
postgres_db = os.getenv('POSTGRES_ENTERPRISE') # This is the main DB name
postgres_host = os.getenv('POSTGRES_HOST')
postgres_port = os.getenv('POSTGRES_PORT')

SQL_URL_ADMIN = f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/postgres"
admin_engine = create_engine(SQL_URL_ADMIN, isolation_level='AUTOCOMMIT')

def create_database():
    with admin_engine.connect() as conn:
        result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = :db"), {"db": postgres_db})
        exists = result.scalar()
        if not exists:
            conn.execute(text(f"CREATE DATABASE {postgres_db} ENCODING 'UTF8'"))
            logger.info(f"Base de datos '{postgres_db}' creada.")

DATABASE_URL = f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"
# Sync Connection for Initialization
engine_enterprise = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionEnterprise = sessionmaker(autocommit=False, autoflush=False, bind=engine_enterprise)

# Async Connection for SQLAlchemy 2.0
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
async_main_engine = create_async_engine(ASYNC_DATABASE_URL, pool_pre_ping=True)
AsyncSessionMain = async_sessionmaker(async_main_engine, expire_on_commit=False)

def get_db():
    db = SessionEnterprise()
    try:
        yield db
    finally:
        db.close()


def init_enterprise_db():
    # Ensure models are imported so they register with BaseMain
    from app.api.user.user_model import User
    from app.api.enterprise.enterprise_model import Enterprise
    from app.api.enterprise_user.enterprise_user_model import EnterpriseUserLink
    
    BaseMain.metadata.create_all(bind=engine_enterprise)

def init_db():
    create_database()
    init_enterprise_db()
