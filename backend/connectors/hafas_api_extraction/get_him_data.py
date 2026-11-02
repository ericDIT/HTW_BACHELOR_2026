import httpx
import asyncio
import os
from dotenv import load_dotenv
from datetime import date
from connectors.hafas_api_extraction.get_stop_id import get_stop_id

load_dotenv()

BASE_URL = os.getenv("BASE_URL")
ACCESS_ID = os.getenv("ACCESS_ID")
today = date.today().strftime("%Y-%m-%d")

#This function gets you HIM data of a given station
async def get_him_information(from_st: str, to_st: str):

    async with httpx.AsyncClient(http2=False) as client:

        from_id = await get_stop_id(from_st)
        to_id = await get_stop_id(to_st)

        print(from_id)

        him_response = await client.get(f"{BASE_URL}/himsearch", params={
            "accessId": ACCESS_ID,
            "fromstation": from_st,
            "tostation": to_st,
            "dateB": today,
            "type": "S",
            "format": "json"
        })
        him_data = him_response.json()
        print(him_data)

asyncio.run(get_him_information("900040101", "900040101"))        