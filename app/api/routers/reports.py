from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from ..traccar.schema import ReportSummary, ReportTrip, ReportStop, Alert
from ..traccar.services import TraccarService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["Reports"])

def get_traccar_service():
    return TraccarService()

@router.get("/summary", response_model=List[ReportSummary])
async def get_summary_report(
    from_time: str = Query(..., alias="from"),
    to_time: str = Query(..., alias="to"),
    deviceId: List[int] = Query(...),
    traccar_service: TraccarService = Depends(get_traccar_service)
):
    try:
        return await traccar_service.get_report_summary(from_time, to_time, deviceId)
    except Exception as e:
        logger.error(f"Failed to fetch summary report: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch report from Traccar")

@router.get("/trips", response_model=List[ReportTrip])
async def get_trips_report(
    from_time: str = Query(..., alias="from"),
    to_time: str = Query(..., alias="to"),
    deviceId: List[int] = Query(...),
    traccar_service: TraccarService = Depends(get_traccar_service)
):
    try:
        return await traccar_service.get_report_trips(from_time, to_time, deviceId)
    except Exception as e:
        logger.error(f"Failed to fetch trips report: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch report from Traccar")

@router.get("/stops", response_model=List[ReportStop])
async def get_stops_report(
    from_time: str = Query(..., alias="from"),
    to_time: str = Query(..., alias="to"),
    deviceId: List[int] = Query(...),
    traccar_service: TraccarService = Depends(get_traccar_service)
):
    try:
        return await traccar_service.get_report_stops(from_time, to_time, deviceId)
    except Exception as e:
        logger.error(f"Failed to fetch stops report: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch report from Traccar")

@router.get("/events", response_model=List[Alert])
async def get_events_report(
    from_time: str = Query(..., alias="from"),
    to_time: str = Query(..., alias="to"),
    deviceId: List[int] = Query(None),
    allDevices: bool = Query(False),
    traccar_service: TraccarService = Depends(get_traccar_service)
):
    try:
        # Reusing the existing get_events but filtering by device if provided
        # get_events currently fetches allDevices=true, let's adapt it to use params
        params = [("from", from_time), ("to", to_time)]
        if allDevices:
            params.append(("allDevices", "true"))
        elif deviceId:
            for did in deviceId:
                params.append(("deviceId", str(did)))
                
        response = await traccar_service.client.get(
            "/api/reports/events",
            params=params,
            headers={"Accept": "application/json"}
        )
        response.raise_for_status()
        data = response.json()
        if data:
            return [Alert(**e) for e in data]
        return []
    except Exception as e:
        logger.error(f"Failed to fetch events report: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch report from Traccar")
