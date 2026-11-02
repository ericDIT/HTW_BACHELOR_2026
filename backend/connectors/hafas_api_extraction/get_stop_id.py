import httpx
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()

BASE_URL = os.getenv("BASE_URL")
ACCESS_ID = os.getenv("ACCESS_ID")

async def get_stop_id(stop_name: str, type="S"):
    async with httpx.AsyncClient(http2=False) as client:
        response = await client.get(f"{BASE_URL}/location.name", params={
            "accessId": ACCESS_ID,
            "input": stop_name,
            "type": type,
            "format": "json"
        })
        data = response.json()
        stops = data.get("stopLocationOrCoordLocation", [])
        if not stops:
            print(f"Keine Haltestelle gefunden für: {stop_name}")
            return None
        
        print(stops[0].get("StopLocation", {}).get("id"))

        return stops[0].get("StopLocation", {}).get("id"),

asyncio.run(get_stop_id("S Friedrichstraße"))