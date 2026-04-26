import asyncio
import sys
import os

# Añadir el path del proyecto para poder importar app
sys.path.append(os.getcwd())

from app.db.main_db import AsyncSessionMain
from app.api.enterprise.enterprise_model import Enterprise
from app.api.user.user_model import User
from app.api.drivers.driver_model import Driver
from app.api.drivers.driver_device_model import DriverDeviceLink
from app.api.enterprise_user.enterprise_user_model import EnterpriseUserLink
from sqlalchemy import select


from app.db.dynamic_gps_db import init_enterprise_location_db

async def sync_all_tables():
    print("Iniciando sincronización de tablas para todas las empresas...")
    try:
        async with AsyncSessionMain() as session:
            result = await session.execute(select(Enterprise.id))
            enterprise_ids = [row[0] for row in result.all()]
            
            if not enterprise_ids:
                print("No se encontraron empresas para sincronizar.")
                return

            for ent_id in enterprise_ids:
                print(f"Sincronizando base de datos para empresa ID: {ent_id}...")
                await init_enterprise_location_db(ent_id)
                
                # SQLAlchemy create_all won't add new columns to existing tables.
                # We do it manually since we aren't using Alembic yet.
                from app.db.dynamic_gps_db import get_main_engine
                from sqlalchemy import text
                engine = get_main_engine(ent_id)
                async with engine.begin() as conn:
                    print(f"  -> Asegurando columna 'disabled' en devices y drivers...")
                    await conn.execute(text("ALTER TABLE devices ADD COLUMN IF NOT EXISTS disabled BOOLEAN DEFAULT FALSE;"))
                    await conn.execute(text("ALTER TABLE drivers ADD COLUMN IF NOT EXISTS disabled BOOLEAN DEFAULT FALSE;"))
                    # Note: We removed assigned_device_unique_id in favor of DriverDeviceLink table



        print("\nSincronización finalizada correctamente.")
        print("Las tablas han sido creadas y las columnas 'disabled' han sido añadidas si faltaban.")

    except Exception as e:
        print(f"Error durante la sincronización: {e}")

if __name__ == "__main__":
    asyncio.run(sync_all_tables())
