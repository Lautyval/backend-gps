from fastapi import HTTPException
import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import ProgrammingError, OperationalError
from dotenv import load_dotenv
import asyncio
import anyio

from app.db.base_gps import BaseGPS
from app.logger_config import logger

# Import our project models
from app.api.enterprise_user.enterprise_user_model import POI, MaintenanceRecord

load_dotenv()
postgres_user = os.getenv('POSTGRES_USER')
postgres_password = os.getenv('POSTGRES_PASSWORD')
postgres_host = os.getenv('POSTGRES_HOST')
postgres_port = os.getenv('POSTGRES_PORT')
enterprise_prefix = os.getenv('POSTGRES_ENTERPRISE_PREFIX', 'enterprise')

SQL_URL_ADMIN = f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/postgres"
admin_engine = create_engine(SQL_URL_ADMIN, isolation_level='AUTOCOMMIT')

def create_enterprise_location_db(enterprise_id: int):
    """Sync creation of the database"""
    db_name = f"{enterprise_prefix}_{enterprise_id}"
    
    with admin_engine.connect() as conn:
        result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = :db"), {"db": db_name})
        exists = result.scalar()
        if not exists:
            conn.execute(text(f"CREATE DATABASE {db_name} ENCODING 'UTF8'"))
            logger.info(f"Base de datos '{db_name}' creada para empresa ID: {enterprise_id}.")
        else:
            logger.debug(f"La base de datos '{db_name}' ya existe.")
    
    return db_name

_main_engine_cache = {}
_mqtt_engine_cache = {}
_main_sessionmaker_cache = {}
_mqtt_sessionmaker_cache = {}

# --- Configurations ---
MAIN_POOL_CONFIG = {
    "pool_size": 3,
    "max_overflow": 1,
    "pool_timeout": 30,
    "pool_recycle": 1800,
    "pool_pre_ping": True,
}

MQTT_POOL_CONFIG = {
    "pool_size": 1,
    "max_overflow": 0,
    "pool_timeout": 45,
    "pool_recycle": 1800,
    "pool_pre_ping": True,
}

def _get_or_create_engine(enterprise_id: int, cache, pool_options):
    if enterprise_id in cache:
        return cache[enterprise_id]

    db_name = f"{enterprise_prefix}_{enterprise_id}"
    db_url = f"postgresql+asyncpg://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{db_name}"
    
    engine = create_async_engine(db_url, **pool_options)
    cache[enterprise_id] = engine
    return engine

def get_main_engine(enterprise_id: int):
    return _get_or_create_engine(enterprise_id, _main_engine_cache, MAIN_POOL_CONFIG)

def get_mqtt_engine(enterprise_id: int):
    return _get_or_create_engine(enterprise_id, _mqtt_engine_cache, MQTT_POOL_CONFIG)

def _get_session_factory(enterprise_id: int, cache, engine_factory):
    if enterprise_id in cache:
        return cache[enterprise_id]
    
    engine = engine_factory(enterprise_id)
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    cache[enterprise_id] = session_factory
    return session_factory

def get_main_session_factory(enterprise_id: int):
    return _get_session_factory(enterprise_id, _main_sessionmaker_cache, get_main_engine)

def get_mqtt_session_factory(enterprise_id: int):
    return _get_session_factory(enterprise_id, _mqtt_sessionmaker_cache, get_mqtt_engine)

async def dispose_all_engines():
      """Close all pools on shutdown"""
      logger.info("Cerrando todos los pools de conexiones de empresa (async)...")
      all_engines = list(_main_engine_cache.values()) + list(_mqtt_engine_cache.values())
      await asyncio.gather(*(engine.dispose() for engine in all_engines))
      _main_engine_cache.clear()
      _mqtt_engine_cache.clear()
      _main_sessionmaker_cache.clear()
      _mqtt_sessionmaker_cache.clear()

async def init_enterprise_location_db(enterprise_id: int):
    """Initialize PostGIS and Tables for a tenant"""
    db_name = create_enterprise_location_db(enterprise_id)
    engine = get_main_engine(enterprise_id)
    
    async with engine.begin() as conn:
        logger.info(f"[{db_name}] Asegurando extensión PostGIS...")
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        # Initialize tables from BaseGPS
        await conn.run_sync(BaseGPS.metadata.create_all)
    
    # Alembic logic will be added when migrations are ready
