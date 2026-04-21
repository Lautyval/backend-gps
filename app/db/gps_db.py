from contextlib import asynccontextmanager
from app.db.dynamic_gps_db import get_main_session_factory, get_mqtt_session_factory

@asynccontextmanager
async def get_async_db_session(enterprise_id: int):
    """
    Proporciona una sesión de base de datos asíncrona y transaccional.
    Realiza commit en caso de éxito y rollback en caso de error.
    """
    session_factory = get_main_session_factory(enterprise_id)
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

@asynccontextmanager
async def get_mqtt_async_db_session(enterprise_id: int):
    """
    Proporciona una sesión de base de datos asíncrona para el WORKER MQTT.
    """
    session_factory = get_mqtt_session_factory(enterprise_id)
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
