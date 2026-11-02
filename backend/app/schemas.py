from scheduled_tasks.period_task import run_1h_period
from scheduled_tasks.immediate_task import test_30min_period
from pydantic import BaseModel

JOBS = {
    "daily_1h_period": run_1h_period,
    "test_30min_period": test_30min_period #diesen 
}

class JobRequest(BaseModel):
    job: str 
    station_id: str

class StationResponse(BaseModel):
    station_id: str
    station_name: str
    lon: float
    lat: float
    elevator: bool
    blind_strip: bool

class LineStationsRequest(BaseModel):
    station_id: str
    line_id_list: list[str]