import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
import os
import httpx
import logging
from datetime import date
import asyncio

load_dotenv()

BASE_URL = os.getenv("BASE_URL")
ACCESS_ID = os.getenv("ACCESS_ID")

log = logging.getLogger(__name__)

async def get_station_info_by_id(stop_id: str, duration=30):
    today = date.today().strftime("%Y-%m-%d")

    async with httpx.AsyncClient(http2=False) as client:
        response = await client.get(f"{BASE_URL}/departureBoard", params={
            "accessId": ACCESS_ID,
            "id": stop_id,
            "rtMode": "SERVER_DEFAULT",
            "date": today,
            "duration": duration,
            "maxJourneys": 5,
            "format": "json",
        })
        data = response.json()

        departures = data.get("Departure", [])
        if not departures: return []

        stop_name = departures[0].get("stop")
        next_departures = []

        for dep in departures:
            dep_date = dep.get("date")
            est_time = dep.get("rtTime")
            if est_time is None:
                est_time = dep.get("time")
            line_name = dep.get("name")
            direction = dep.get("direction")
            next_departures.append({
                "line": line_name,
                "direction": direction,
                "time": est_time,
                "date": dep_date
            })
        
        return {
            "stop_name": stop_name,
            "departures": next_departures
        }

if __name__ == "__main__":
    stop_id_hard = "A=1@O=S Halensee (Berlin)@X=13290147@Y=52496698@U=86@L=900040101@p=1772151637@"
    asyncio.run(get_station_info_by_id(stop_id_hard))

