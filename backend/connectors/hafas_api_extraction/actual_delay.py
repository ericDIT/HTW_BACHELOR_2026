import asyncio

import httpx
import logging
import datetime
from utils.data_lake_management import ensure_data_lake_dir, load_into_dl
from db.database import connection_pool
import psycopg2
from dotenv import load_dotenv
import os
from datetime import date, datetime, timedelta

load_dotenv()
BASE_URL = os.getenv("BASE_URL")
ACCESS_ID = os.getenv("ACCESS_ID")
if not BASE_URL or not ACCESS_ID:
    raise RuntimeError(f"Missing required env vars: BASE_URL={BASE_URL!r}, ACCESS_ID={'set' if ACCESS_ID else None}")

log = logging.getLogger(__name__)
if not log.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    log.addHandler(handler)

MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 5

async def fetch_journey_detail(client: httpx.AsyncClient, params: dict) -> dict:
    url = f"{BASE_URL.rstrip('/')}/journeyDetail"

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            if 400 <= status < 500:
                log.error(f"Client error {status} calling HAFAS journeyDetail, not retrying: {e}")
                raise
            if attempt < MAX_RETRIES:
                wait = RETRY_BACKOFF_SECONDS * (2 ** (attempt - 1))
                log.warning(f"Server error {status} calling HAFAS journeyDetail (attempt {attempt}/{MAX_RETRIES}), retrying in {wait}s: {e}")
                await asyncio.sleep(wait)
            else:
                log.error(f"Server error {status} calling HAFAS journeyDetail, giving up after {MAX_RETRIES} attempts: {e}")
                raise

        except httpx.RequestError as e:
            if attempt < MAX_RETRIES:
                wait = RETRY_BACKOFF_SECONDS * (2 ** (attempt - 1))
                log.warning(f"Network error type: {type(e).__name__} (attempt {attempt}/{MAX_RETRIES}), retrying in {wait}s: {e}")
                await asyncio.sleep(wait)
            else:
                log.error(f"Network error calling HAFAS journeyDetail, giving up after {MAX_RETRIES} attempts: {e}")
                raise

async def update_actual_delay(stop_id: str, trip_id: str, scheduled_time: str, routeIdx: str, is_cancelled: bool):
    async with httpx.AsyncClient(http2=False) as client:
        try:
            data = await fetch_journey_detail(client, {
                "accessId": ACCESS_ID,
                "id": trip_id,
                "format": "json",
                "rtMode": "SERVER_DEFAULT"
            })
        except (httpx.HTTPStatusError, httpx.RequestError):
            log.error(f"Failed to fetch journey detail for trip {trip_id} after retries.")
            return

        stops = data.get("Stops", {}).get("Stop", [])
        line_id = data.get("Product", [{}])[0].get("lineId")
        line_name = data.get("Product",[{}])[0].get("name")
        transport_type = data.get("Product",[{}])[0].get("catOut")
        operator = data.get("Product",[{}])[0].get("operatorCode")
        stop = next((
        s for s in stops
        if routeIdx is not None
        and s.get("routeIdx") is not None
        and s.get("id") == stop_id
        and int(s.get("routeIdx")) == int(routeIdx)
        ),None)

        if not stop:
            log.warning(f"Stop {stop_id} not found for trip {trip_id}")
            return
        
        log.debug(f"trip: {trip_id} | routeIdx: {routeIdx} | scheduled: {scheduled_time} | depTime: {stop.get('depTime')} | rtDepTime: {stop.get('rtDepTime')}")

        delay_day = data.get("dayOfOperation")
        if not delay_day:
            log.warning(f"No dayOfOperation found for trip {trip_id}, using scheduled date as fallback.")
            delay_day = date.today().strftime("%Y-%m-%d")

        rt_time = stop.get("rtDepTime")
        dep_time = stop.get("depTime")
        log.info(f"trip: {trip_id} | depTime: {dep_time} | rtDepTime: {rt_time}")
        
        OCCUPANCY_MAP = {11: "L", 12: "M", 13: "H"}
        occupancy_list = stop.get("Occupancy")
        occupancy_raw = occupancy_list[0].get("raw") if occupancy_list else None
        occupancy = OCCUPANCY_MAP.get(occupancy_raw, "N")

        actual_time = rt_time or dep_time
        delay_minutes = 0

        if rt_time:
            fmt = "%H:%M:%S"
            diff = datetime.strptime(rt_time, fmt) - datetime.strptime(scheduled_time, fmt)
            if diff.total_seconds() < -12 * 3600:
                diff += timedelta(days=1)
            delay_minutes = int(diff.total_seconds() / 60)

        stop_name = stop.get("name")
        year, month, day = delay_day.split("-")
        dir_type = "raw"
        file_type = dir_type + "_actual"

        dl_dir, stop_name_safe = ensure_data_lake_dir(stop_name, year, month, day, dir_type)
        dl_load_successful = load_into_dl(data, dl_dir, stop_name_safe, delay_day, file_type)

        conn = None
        try:
            conn = connection_pool.getconn()
            with conn.cursor() as cur:

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

                cur.execute(
                    """INSERT INTO Delays
                        (trip_id, station_id, line_id,
                          delay_day, scheduled_time,
                          cancelled, actual_time,
                          delay_minutes, occupancy)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (trip_id, delay_day) DO NOTHING""",
                    (trip_id, stop_id, line_id, delay_day,
                      scheduled_time, is_cancelled,
                      actual_time, delay_minutes, occupancy)
                )
            conn.commit()
            log.info(f"Delay updated for trip {trip_id}: {delay_minutes} min")
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            log.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                connection_pool.putconn(conn)