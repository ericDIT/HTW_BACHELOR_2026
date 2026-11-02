from datetime import datetime, timedelta
from connectors.hafas_api_extraction.get_and_load_dep import get_and_load_planned_dep
from connectors.hafas_api_extraction.actual_delay import update_actual_delay
import logging

#temporary test parameters
station_direction = [
    "A=1@O=S Halensee (Berlin)@X=13290147@Y=52496698@U=86@L=900040101@",
    "S42"
]

log = logging.getLogger(__name__)
if not log.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    log.addHandler(handler)

DURATION_MINUTES = 60
MAX_JOURNEYS = 50

async def run_1h_period(add_job, station_id):
    planned = await get_and_load_planned_dep(station_id,"S", DURATION_MINUTES, MAX_JOURNEYS)

    if not planned:
        log.warning("No planned departures fetched this run - skipping job scheduling.")
        return

    now = datetime.now()

    for dep in planned:
        scheduled_time = dep["scheduledTime"]
        run_at = datetime.strptime(scheduled_time, "%H:%M:%S").replace(
            year=now.year, month=now.month, day=now.day
        ) + timedelta(minutes=20)

        log.info(f"run_at: {run_at} | now: {now} | routeIdx: {dep['routeIdx']}")

        if run_at > now:
            add_job(
                update_actual_delay,
                "date",
                run_date=run_at,
                id=f"actual_delay_{dep['tripId']}",
                replace_existing=True,
                args=[
                    station_id,
                    dep["tripId"],
                    scheduled_time,
                    dep["routeIdx"],
                    dep["is_cancelled"]
                ],
                misfire_grace_time=60
            )