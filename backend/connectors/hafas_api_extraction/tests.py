from dotenv import load_dotenv
import os
import httpx
from datetime import date
import asyncio
import logging

log = logging.getLogger(__name__)

load_dotenv()

BASE_URL = os.getenv("BASE_URL")
ACCESS_ID = os.getenv("ACCESS_ID")

stop_id_hard="A=1@O=S Halensee (Berlin)@X=13290147@Y=52496698@U=86@L=900040101@"
line_name_hard="S42"

async def testFunc(stop_id: str,line_name: str, cat="S", duration=180):
    today = date.today().strftime("%Y-%m-%d")

    async with httpx.AsyncClient(http2=False) as client:
        response = await client.get(f"{BASE_URL}/departureBoard", params={
            "accessId": ACCESS_ID,
            "id": stop_id,
            "rtMode": "SERVER_DEFAULT",
            "date": today,
            "duration": duration,
            "maxJourneys": 150,
            "format": "json",
            "catOut": cat,
            "line": line_name
        })
        data = response.json()

        departures = data.get("Departure", [])
        if not departures:
            print("no deps")
            return []

        dep_0 = departures[0]

        line_id = dep_0.get("lineId")
        line_type = dep_0.get("catOut")
        operator = dep_0.get("operator")


        for dep in departures[:len(departures)//4]:
            trip_id = dep.get("JourneyDetailRef", {}).get("ref")
            scheduled_time = dep.get("time")
            station_id = dep.get("stopid")
            cancelled = dep.get("cancelled", False)

            print("========================================================================")
            print(f"trip id: {trip_id}")
            print(f"station_id: {station_id}")
            print(f"line_id: {line_id}")
            print(f"today: {today}")
            print(f"scheduled_time: {scheduled_time}")
            print(f"cancelled: {cancelled}")

            async with httpx.AsyncClient(http2=False) as client:
                response = await client.get(f"{BASE_URL}/journeyDetail", params={
                    "accessId": ACCESS_ID,
                    "id": trip_id,
                    "format": "json"
                })
                data = response.json()

                stops = data.get("Stops", {}).get("Stop", [])
                stop = next((s for s in stops if s.get("id") == stop_id), None)

                if not stop:
                    log.warning(f"Stop {stop_id} not found for trip {trip_id}")
                    return

                rt_time = stop.get("rtDepTime")
                dep_time = stop.get("depTime")

                print(f"rt_time: {rt_time} and dep_time: {dep_time}")    
                print("========================================================================")

                await asyncio.sleep(5)
                



asyncio.run(testFunc(stop_id_hard, line_name_hard))