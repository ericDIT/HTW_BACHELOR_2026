import httpx
import asyncio
import os
from dotenv import load_dotenv
from connectors.hafas_api_extraction.get_stop_id import get_stop_id
from datetime import date


load_dotenv()

BASE_URL = os.getenv("BASE_URL")
ACCESS_ID = os.getenv("ACCESS_ID")

async def get_trip(origin: str, destination: str):
    origin_id = await get_stop_id(origin)
    destination_id = await get_stop_id(destination)

    if not origin_id or not destination_id:
        print("Haltestelle nicht gefunden")
        return

    print(f"Von: {origin} ({origin_id})")
    print(f"Nach: {destination} ({destination_id})")

    today = date.today().strftime("%Y-%m-%d")

    async with httpx.AsyncClient(http2=False, timeout=30.0) as client:
        response = await client.get(f"{BASE_URL}/trip", params={
            "accessId": ACCESS_ID,
            "originId": origin_id,
            "destId": destination_id,
            "date": "2026-03-30",
            "time": "09:00",
            "rtMode": "FULL",
            "format": "json"
        })
        data = response.json()

        trips = data.get("Trip", [])
        print(f"\n── {len(trips)} Verbindungen gefunden ───────────────")

        for i, trip in enumerate(trips):
            legs = trip.get("LegList", {}).get("Leg", [])
            duration = trip.get("duration")
            print(f"\nVerbindung {i+1} – Dauer: {duration}")

            for leg in legs:
                leg_name = leg.get("name", "Fußweg")
                dep_stop = leg.get("Origin", {}).get("name")
                arr_stop = leg.get("Destination", {}).get("name")
                dep_time = leg.get("Origin", {}).get("time")
                arr_time = leg.get("Destination", {}).get("time")
                print(f"  {leg_name}: {dep_stop} {dep_time} → {arr_stop} {arr_time}")

asyncio.run(get_trip("S Halensee", "S Tempelhof"))