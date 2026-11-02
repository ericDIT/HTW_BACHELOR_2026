import httpx
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL")
ACCESS_ID = os.getenv("ACCESS_ID")

#This function gets you all stop on a given lineage,
#you also have to name a stop on the line
async def get_lineage_stops(lineage_name: str, stop_on_lineage: str):

    async with httpx.AsyncClient(http2=False) as client:

        location_response = await client.get(f"{BASE_URL}/location.name", params={
            "accessId": ACCESS_ID,
            "input": stop_on_lineage,
            "type": "S",
            "format": "json"
        })
        location_data = location_response.json()

        stops = location_data.get("stopLocationOrCoordLocation", [])
        if not stops:
            print("No Stops found")
            return

        stop_id = stops[0].get("StopLocation", {}).get("id")
        print(f"Stop-ID Halensee: {stop_id}")

        departure_response = await client.get(f"{BASE_URL}/departureBoard", params={
            "accessId": ACCESS_ID,
            "id": stop_id,
            "format": "json"
        })
        departure_data = departure_response.json()

        departures = departure_data.get("Departure", [])
        journey_id = None

        for dep in departures:
            if lineage_name in dep.get("name", ""):
                journey_id = dep.get("JourneyDetailRef", {}).get("ref")
                break

        if not journey_id:
            print(f"No {lineage_name}-Departure found")
            return

        detail_response = await client.get(f"{BASE_URL}/journeyDetail", params={
            "accessId": ACCESS_ID,
            "id": journey_id,
            "format": "json"
        })
        detail_data = detail_response.json()

        journey_stops = detail_data.get("Stops", {}).get("Stop", [])

        print(f"\n── Stops of {lineage_name} ──────────────────────")
        for stop in journey_stops:
            print(f"{stop.get('name')} – lat: {stop.get('lat')}, lon: {stop.get('lon')}")

        return journey_stops

asyncio.run(get_lineage_stops("U7", "Rudow"))