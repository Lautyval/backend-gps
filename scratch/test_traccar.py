import asyncio
from app.api.traccar.services import TraccarService

async def main():
    service = TraccarService()
    try:
        devices = await service.get_devices()
        print("Devices:", [d.name for d in devices])
        if not devices:
            return
        did = devices[0].id
        from_t = "2026-04-17T00:00:00Z"
        to_t = "2026-04-18T23:59:00Z"
        
        pos = await service.get_route_history(did, from_t, to_t)
        print(f"Positions for {did}: {len(pos)}")
        
        summ = await service.get_report_summary(from_t, to_t, [did])
        print(f"Summary for {did}: {summ}")
        
    finally:
        await service.close()

if __name__ == "__main__":
    asyncio.run(main())
