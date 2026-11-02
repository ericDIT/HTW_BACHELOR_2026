import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from backend.connectors.hafas_api_extraction.get_and_load_dep import get_and_load_planned_dep
from backend.connectors.hafas_api_extraction.actual_delay import update_actual_delay
import asyncio
import logging

#TRUNCATE TABLE Delays RESTART IDENTITY CASCADE;
#TRUNCATE TABLE Lines RESTART IDENTITY CASCADE;

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s – %(message)s"
)
log = logging.getLogger(__name__)

load_dotenv()

scheduler = AsyncIOScheduler()
station_direction = ["A=1@O=S Halensee (Berlin)@X=13290147@Y=52496698@U=86@L=900040101@", "S42"]

async def run_test():
    log.info("Lade geplante Abfahrten...")
    try:
        planned = await get_and_load_planned_dep(station_direction[0], duration=20)  # nur ~20 Abfahrten
    except Exception as e:
        log.error(f"Error loading departures: {e}")
        return

    log.info(f"{len(planned)} Abfahrten geladen")

    now = datetime.now()
    cutoff = now + timedelta(minutes=50)  # scheduledTime + 20min, also 30min Fenster + 20min buffer
    scheduled_count = 0
    skipped_past = 0
    skipped_future = 0

    for dep in planned:
        run_at = datetime.strptime(dep["scheduledTime"], "%H:%M:%S").replace(
            year=now.year, month=now.month, day=now.day
        ) + timedelta(minutes=20)

        if run_at <= now:
            skipped_past += 1
            continue
        if run_at > cutoff:
            skipped_future += 1
            continue

        scheduler.add_job(
            update_actual_delay,
            "date",
            run_date=run_at,
            args=[station_direction[0], dep["tripId"], dep["scheduledTime"]],
            misfire_grace_time=60
        )
        log.info(f"Job geplant: {run_at.strftime('%H:%M:%S')} – Trip {dep['tripId']} (scheduledTime: {dep['scheduledTime']})")
        scheduled_count += 1

    log.info(f"{scheduled_count} Jobs geplant | {skipped_past} bereits vergangen | {skipped_future} außerhalb Fenster")

async def main():
    await run_test()
    scheduler.start()
    log.info("Scheduler gestartet, warte auf Jobs...")
    await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())