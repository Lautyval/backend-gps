import asyncio
from app.api.traccar.services import TraccarService

async def main():
    service = TraccarService()
    try:
        did = 3
        # These are the exact strings the frontend sends for "17/04/2026 00:00" -> "17/04/2026 23:59" (in UTC-3)
        from_t = "2026-04-17T03:00:00.000Z"
        to_t = "2026-04-18T02:59:00.000Z"
        
        trips = await service.get_report_trips(from_t, to_t, [did])
        print(f"Trips for {did}: {trips}")

        stops = await service.get_report_stops(from_t, to_t, [did])
        print(f"Stops for {did}: {stops}")
        
    finally:
        await service.close()

if __name__ == "__main__":
    asyncio.run(main())
