from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging
import pytz

log = logging.getLogger(__name__)
scheduler = AsyncIOScheduler(timezone=pytz.timezone("Europe/Berlin"))

def start_scheduler():
    log.info("Starting scheduler")
    scheduler.start()

def stop_scheduler():
    scheduler.shutdown(wait=False)

def add_job(*args, **kwargs):
    scheduler.add_job(*args, **kwargs)