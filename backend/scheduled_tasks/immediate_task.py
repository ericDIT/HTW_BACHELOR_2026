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

async def test_30min_period(add_job):
    planned = await get_and_load_planned_dep(station_direction[0], duration=30, max_journeys=20)

    now = datetime.now()

    for i, dep in enumerate(planned):
        run_at = datetime.strptime(dep["scheduledTime"], "%H:%M:%S").replace(
            year=now.year, month=now.month, day=now.day
        ) + timedelta(minutes=10)

        log.info(f"Scheduling update for trip {dep['tripId']} at {run_at}")

        add_job(
            update_actual_delay,
            "date",
            run_date=run_at,
            args=[
                station_direction[0],
                dep["tripId"],
                dep["scheduledTime"],
                dep["routeIdx"]
            ],
            misfire_grace_time=60
        )