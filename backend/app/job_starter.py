from datetime import datetime, timedelta

import pytz

from scheduled_tasks.scheduler import scheduler, add_job
from app.schemas import JOBS
import logging

log = logging.getLogger(__name__)

def start_jobs(job: str, station_id: str):
    if job not in JOBS:
        log.warning(f"Job with name '{job}' is an unknown job")
        return False

    if scheduler.get_job(job):
        log.warning(f"Job with name '{job}' is already in scheduler")
        return False
    
    if job=="test_30min_period":
        berlin = pytz.timezone("Europe/Berlin")
        log.info(f"Starting immediate job: {job}")
        scheduler.add_job(JOBS[job], "date", run_date=datetime.now(berlin) + timedelta(seconds=5), id=job, args=[add_job])
    else:
        log.info(f"Starting scheduled job: {job}")
        scheduler.add_job(JOBS[job], "cron", hour="7,8,9,16,17,18", minute=0, id=job, args=[add_job, station_id])

    return True

def stop_jobs(job: str):
    if scheduler.get_job(job) is None:
        return False

    scheduler.remove_job(job)    
    return True

# Syntax ist
#{
#    "job": "daily_3h_period"
#}
    
