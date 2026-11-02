from contextlib import asynccontextmanager
import logging
from connectors.hafas_api_extraction.get_station_information import get_station_info_by_id
from endpoint_requests.read_month import read_last_30_days
from endpoint_requests.fill_station_lines import fill_lines_by_station
from endpoint_requests.request_all_lines import get_all_lines_for_station
from endpoint_requests.read_trend import read_timeframe_by_station
from exceptions.exceptions import StationNotFoundError, NoDataFoundError, LineNotFoundError
from scheduled_tasks.scheduler import scheduler, start_scheduler, stop_scheduler
from app.job_starter import start_jobs, stop_jobs
from app.schemas import JobRequest, LineStationsRequest
from fastapi import Depends, APIRouter, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from db.read_queries import get_station_by_id
from connectors.hafas_api_extraction.loading_stops import get_stop_data_and_load
from transforming.daily_facts_by_line import transform_day_to_facts_by_line
from transforming.daily_facts_by_station import transform_day_to_facts_by_station
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.security import verify_api_key

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
router = APIRouter(prefix="/api")

@router.get("/")
def root():
    return {"message": "API läuft"}

#--- PUBLIC ENDPOINTS ---

@router.get("/station")
@limiter.limit("10/minute")
def get_station(request: Request, station_id: str):
    station_data_for_db = get_station_by_id(station_id)
    if station_data_for_db is None:
        raise HTTPException(status_code=404, detail="Station not found")
    return station_data_for_db # Note: im frontend muss ich "station_id=${encodeURIComponent(station.id)"

@router.get("/station/info")
@limiter.limit("10/minute")
async def get_station_info(request: Request, station_id: str):
    station_info = await get_station_info_by_id(station_id)
    if not station_info:
        raise HTTPException(status_code=404, detail="Station not found")
    return station_info

@router.get("/station/lines")
@limiter.limit("10/minute")
async def get_lines_of_station(request: Request, station_id: str):
    try:
        line_and_ids = await get_all_lines_for_station(station_id)
    except StationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return line_and_ids

@router.post("/daily_facts/by_line")
@limiter.limit("5/minute")
def get_daily_facts_by_line(request: Request, fact_date: str, station_id: str, line_id: str):
    try:
        return transform_day_to_facts_by_line(fact_date, station_id, line_id)
    except StationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except LineNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except NoDataFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/daily_facts/by_station")
@limiter.limit("5/minute")
def get_daily_facts_by_station(request: Request, fact_date: str, station_id: str):
    try:
        return transform_day_to_facts_by_station(fact_date, station_id)
    except StationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except NoDataFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/daily_facts/trend")
@limiter.limit("5/minute")
def get_daily_facts_trend(request: Request, station_id: str, from_date: str, to_date: str):
    try:
        return read_timeframe_by_station(station_id, from_date, to_date)
    except StationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except NoDataFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

#@router.get("/monthly_facts/by_station")
#@limiter.limit("5/minute")
#def get_monthly_facts_by_station(request: Request, station_id: str):
#    try:
#        return read_last_30_days(station_id)
#    except StationNotFoundError as e:
#        raise HTTPException(status_code=404, detail=str(e))
#    except NoDataFoundError as e:
#        raise HTTPException(status_code=404, detail=str(e))

#--- PRIVATE ENDPOINTS ---
@router.post("/station")
async def post_station(request: Request, station_id: str, _: None = Depends(verify_api_key)):
    if not station_id.strip():
        raise HTTPException(status_code=422, detail="station_id can not be empty")

    result = await get_stop_data_and_load(station_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Station not found")
    
    return result

@router.post("/station/lines")
def fill_linestations_by_station(payload: LineStationsRequest, _: None = Depends(verify_api_key)):
    try:
        filled_lines = fill_lines_by_station(payload.station_id, payload.line_id_list)
    except StationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if not filled_lines:
        raise HTTPException(status_code=400, detail="No lines filled")

    return {"station_id": payload.station_id, "filled_lines": filled_lines}


@router.get("/jobs")
async def jobs(_: None = Depends(verify_api_key)):
    return [
        {
            "id": job.id,
            "next_run": job.next_run_time
        }
        for job in scheduler.get_jobs()
    ]

@router.post("/jobs/start")
def start_job(req: JobRequest,  _: None = Depends(verify_api_key)):
    if not start_jobs(req.job, req.station_id):
        return {"error": "unknown job"}

    return {"status": f"{req.job} started, for station with ID: {req.station_id}"}

@router.post("/jobs/stop")
def stop_job(req: JobRequest, _: None = Depends(verify_api_key)):
    if not stop_jobs(req.job):
        return {"error": "unknown job"}

    return {"status": f"{req.job} stopped"}

app.include_router(router)