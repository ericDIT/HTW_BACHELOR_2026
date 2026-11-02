import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
import os
import httpx
import logging
import psycopg2
from datetime import date
from db.database import connection_pool
import asyncio

load_dotenv()
BASE_URL = os.getenv("BASE_URL")
ACCESS_ID = os.getenv("ACCESS_ID")
if not BASE_URL or not ACCESS_ID:
    raise RuntimeError(f"Missing required env vars: BASE_URL={BASE_URL!r}, ACCESS_ID={'set' if ACCESS_ID else None}")

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

        conn = None
        try:
            conn = connection_pool.getconn()
            with conn.cursor() as cur:

                for dep in departures:

                    product   = dep.get("ProductAtStop", {})
                    line_id   = product.get("lineId")
                    if not line_id:
                        log.warning(f"Skipping departure without lineId: trip={dep.get('JourneyDetailRef', {}).get('ref')}")
                        continue

                    line_name = product.get("name")
                    transport_type = product.get("catOut")
                    operator  = product.get("operatorCode")

                    cur.execute(
                        "SELECT line_id FROM lines WHERE line_id = %s AND line_name = %s",
                        (line_id, line_name)
                    )
                    row = cur.fetchone()

                    if row is None:
                        cur.execute(
                            """INSERT INTO Lines (line_id, line_name, transport_type, operator)
                            VALUES (%s, %s, %s, %s)
                            """,
                            (line_id, line_name, transport_type, operator)
                        )

                    trip_id         = dep.get("JourneyDetailRef", {}).get("ref")
                    scheduled_time  = dep.get("time")
                    station_id      = dep.get("stopid")
                    cancelled       = dep.get("cancelled", False)

                    cur.execute(    
                        """INSERT INTO Delays
                            (trip_id, station_id, line_id, delay_day, scheduled_time, cancelled)
                        VALUES (%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (trip_id, delay_day) DO NOTHING""",
                        (trip_id, station_id, line_id, today, scheduled_time, cancelled)
                    )
                    log.info(f"Planned departure {scheduled_time} saved for trip {trip_id}")

            conn.commit()

        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            log.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                connection_pool.putconn(conn)

        return [
            {
                "tripId": dep.get("JourneyDetailRef", {}).get("ref"),
                "scheduledTime": dep.get("time"),
                "routeIdx": dep.get("Product", [{}])[0].get("routeIdxFrom")
            }
            for dep in departures
        ]
    
if __name__ == "__main__":
    stop_id_hard = "A=1@O=S Halensee (Berlin)@X=13290147@Y=52496698@U=86@L=900040101@p=1772151637@"
    asyncio.run(get_and_load_planned_dep(stop_id_hard))