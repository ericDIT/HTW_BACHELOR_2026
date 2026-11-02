from datetime import date

import httpx
import os
from dotenv import load_dotenv
import asyncio
from connectors.hafas_api_extraction.get_stop_id import get_stop_id

load_dotenv()

BASE_URL = os.getenv("BASE_URL")
ACCESS_ID = os.getenv("ACCESS_ID")

async def get_delays(stop_name: str):
    stop_id = await get_stop_id(stop_name)

    today = date.today().strftime("%Y-%m-%d")
    
    async with httpx.AsyncClient(http2=False) as client:
        response = await client.get(f"{BASE_URL}/departureBoard", params={
            "accessId": ACCESS_ID,
            "id": stop_id,
            "rtMode": "SERVER_DEFAULT",
            "date": today,
            "format": "json",
            "catOut": "S"
        })
        data = response.json()
        
        departures = data.get("Departure", [])
        
        for dep in departures:
            name = dep.get("name")
            direction = dep.get("direction")
            planned_time = dep.get("time")
            real_time = dep.get("rtTime")
            cancelled = dep.get("cancelled", False) 

            if real_time and real_time != planned_time:
                print(f"⚠️  {name} → {direction}: geplant {planned_time}, tatsächlich {real_time}")
            elif cancelled:
                print(f"❌ {name} → {direction}: FÄLLT AUS")
            else:
                print(f"✅ {name} → {direction}: pünktlich um {planned_time}")

asyncio.run(get_delays("Halensee"))                