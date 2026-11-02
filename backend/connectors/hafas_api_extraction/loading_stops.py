from dotenv import load_dotenv
import os
import httpx
from psycopg2 import pool
import logging
import asyncio
import psycopg2
from db.database import connection_pool

load_dotenv()

BASE_URL = os.getenv("BASE_URL")
ACCESS_ID = os.getenv("ACCESS_ID")

log = logging.getLogger(__name__)

async def get_stop_data_and_load(stop_id: str):
    try:
        async with httpx.AsyncClient(http2=False) as client:
            response = await client.get(f"{BASE_URL}/location.name", params={
                "accessId": ACCESS_ID,
                "input": stop_id,
                "format": "json"
            })
            response.raise_for_status()
    except httpx.HTTPStatusError as e:
        log.error(f"API Error: {e}")
        raise 
    except httpx.RequestError as e:
        log.error(f"Error connecting to API: {e}")
        raise

    data = response.json()
    stops = data.get("stopLocationOrCoordLocation", [])

    if not stops:
        log.error(f"No stop found for ID: {stop_id}")
        return None
    
    stop = stops[0].get("StopLocation", {})
    location_notes = stop.get("LocationNotes", {}).get("LocationNote", [])
    note_values = [note.get("value", "") for note in location_notes]
    station_id = stop.get("id")
    station_id = station_id.split("@p=")[0] + "@"
    station_name = stop.get("name")
    lon = stop.get("lon")
    lat = stop.get("lat")
    elevator = "Aufzug" in note_values
    blind_strip = "Blindenleitstreifen" in note_values

    if not all([station_id, station_name, lon, lat]):
        log.error(f"Incomplete station data: {stop}")
        return None

    conn = None
    try:
        conn = connection_pool.getconn()
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO Stations (station_id, station_name, lon, lat, elevator, blind_strip)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (station_id) DO NOTHING""",
                (station_id, station_name, lon, lat, elevator, blind_strip)
            )
        conn.commit()
        log.info(f"Data from station '{station_name}' successfully inserted into station table.")
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        log.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            connection_pool.putconn(conn)
    
    return {
        "station_id": station_id,
        "station_name": station_name,
        "lon": lon,
        "lat": lat,
        "elevator": elevator,
        "blind_strip": blind_strip
    }

if __name__ == "__main__":
    asyncio.run(get_stop_data_and_load("A=1@O=S+U Friedrichstr. Bhf (Berlin)@X=13387257@Y=52520304@U=86@L=900100001@p=1776640808@"))