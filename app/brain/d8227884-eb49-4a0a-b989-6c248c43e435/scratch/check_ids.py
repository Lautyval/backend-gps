import asyncio
import sys
import os

sys.path.append(os.getcwd())

from app.db.gps_db import get_async_db_session
from app.api.drivers.driver_model import Driver
from app.api.devices.device_model import Device
from sqlalchemy import select

async def check():
    async with get_async_db_session(1) as db:
        res = await db.execute(select(Driver).where(Driver.unique_id == '43778763'))
        driver = res.scalar_one_or_none()
        if driver:
            print(f"Driver 43778763: ID={driver.id}, TraccarID={driver.traccar_driver_id}")
        else:
            print("Driver 43778763 not found in PG")

        res = await db.execute(select(Device).where(Device.unique_id == '66445887'))
        device = res.scalar_one_or_none()
        if device:
            print(f"Device 66445887: ID={device.id}, TraccarID={device.traccar_device_id}")
        else:
            print("Device 66445887 not found in PG")

if __name__ == "__main__":
    asyncio.run(check())
