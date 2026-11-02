import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_lake_management import ensure_data_lake_dir, load_into_dl
from dotenv import load_dotenv
import os
import httpx
import logging
from datetime import date
import asyncio

load_dotenv()
BASE_URL = os.getenv("BASE_URL")
ACCESS_ID = os.getenv("ACCESS_ID")
DATA_LAKE_PATH = os.getenv("DATA_LAKE_PATH")
if not BASE_URL or not ACCESS_ID or not DATA_LAKE_PATH:
    raise RuntimeError(f"Missing required env vars: BASE_URL={BASE_URL!r}, ACCESS_ID={'set' if ACCESS_ID else None}, DATA_LAKE_PATH={DATA_LAKE_PATH!r}")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
log = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 5

async def fetch_departure_board(client: httpx.AsyncClient, params: dict) -> dict:
    url = f"{BASE_URL.rstrip('/')}/departureBoard"

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            status = e.response.status_code

            if 400 <= status < 500:
                log.error(f"Client error {status} calling HAFAS API, not retrying: {e}")
                raise

            if attempt < MAX_RETRIES:
                wait = RETRY_BACKOFF_SECONDS * (2 ** (attempt - 1))
                log.warning(
                    f"Server error {status} calling HAFAS API "
                    f"(attempt {attempt}/{MAX_RETRIES}), retrying in {wait}s: {e}"
                )
                await asyncio.sleep(wait)
            else:
                log.error(f"Server error {status} calling HAFAS API, giving up after {MAX_RETRIES} attempts: {e}")
                raise

        except httpx.RequestError as e:
            
            if attempt < MAX_RETRIES:
                wait = RETRY_BACKOFF_SECONDS * (2 ** (attempt - 1))
                log.warning(
                    f"Network error type: {type(e).__name__}, details: {repr(e)}"
                    f"(attempt {attempt}/{MAX_RETRIES}), retrying in {wait}s: {e}"
                )
                await asyncio.sleep(wait)
            else:
                log.error(f"Network error calling HAFAS API, giving up after {MAX_RETRIES} attempts: {e}")
                raise


async def get_and_load_planned_dep(stop_id: str, cat="S", duration=60, max_journeys=50):
    today = date.today().strftime("%Y-%m-%d")

    async with httpx.AsyncClient(http2=False) as client:
        try:
            data = await fetch_departure_board(client, {
                "accessId": ACCESS_ID,
                "id": stop_id,
                "rtMode": "SERVER_DEFAULT",
                "date": today,
                "duration": duration,
                "maxJourneys": max_journeys,
                "format": "json",
                "catOut": cat,
            })
        except (httpx.HTTPStatusError, httpx.RequestError):
            log.error(f"Failed to fetch departures for stop {stop_id} after retries.")
            return []

        departures = data.get("Departure", [])
        if not departures: 
            log.info("No departures")
            return []

        stop_name = departures[0].get("stop")
        year, month, day = today.split("-")
        dir_type = "raw"
        file_type = dir_type + "_planned"

        dl_dir, stop_name_safe = ensure_data_lake_dir(stop_name, year, month, day, dir_type)
        dl_load_successful = load_into_dl(departures, dl_dir, stop_name_safe, today, file_type)

        return [
            {
                "tripId": dep.get("JourneyDetailRef", {}).get("ref"),
                "scheduledTime": dep.get("time"),
                "routeIdx": dep.get("Product", [{}])[0].get("routeIdxFrom"),
                "is_cancelled": dep.get("cancelled", False)
            }
            for dep in departures
        ]

if __name__ == "__main__":
    stop_id_hard = "A=1@O=S Halensee (Berlin)@X=13290147@Y=52496698@U=86@L=900040101@p=1772151637@"
    asyncio.run(get_and_load_planned_dep(stop_id_hard))