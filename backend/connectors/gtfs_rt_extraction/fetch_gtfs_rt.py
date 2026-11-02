import asyncio

import httpx
from google.transit import gtfs_realtime_pb2

FOR_THIS_STATION="de:11000:900040101"
GTFS_RT_URL="https://production.gtfsrt.vbb.de/data"


async def fetch_gtfs_rt_feed(url: str) -> gtfs_realtime_pb2.FeedMessage:
    async with httpx.AsyncClient(http2=False) as client:
        response = await client.get(url)
        response.raise_for_status()

    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(response.content)
    return feed

async def return_feed_entities(stop_id_filter: str = None):
    
    feed = await fetch_gtfs_rt_feed(GTFS_RT_URL)

    print(f"Total entities in feed: {len(feed.entity)}")

    matches = 0
    
    for entity in feed.entity:
        if entity.HasField("trip_update"):
            trip_update = entity.trip_update
            trip_id = trip_update.trip.trip_id
            route_id = trip_update.trip.route_id
    
            for stop_time_update in trip_update.stop_time_update:
                stop_id = stop_time_update.stop_id

                if stop_id_filter and stop_id_filter not in stop_id:
                    continue

                arrival_delay = stop_time_update.arrival.delay if stop_time_update.HasField("arrival") else None
                departure_delay = stop_time_update.departure.delay if stop_time_update.HasField("departure") else None

                matches += 1
    
                print(f"Trip {trip_id} @ Stop {stop_id}: arrival_delay={arrival_delay}s, departure_delay={departure_delay}s")

    print(f"Matched {matches} stop updates for stop_id={stop_id_filter}")

if __name__ == "__main__":
    asyncio.run(return_feed_entities(stop_id_filter=FOR_THIS_STATION))