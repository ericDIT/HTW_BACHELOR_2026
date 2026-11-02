from db.database import connection_pool
import logging

log = logging.getLogger(__name__)

def get_station_by_id(station_id: str):
    conn = connection_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT station_name, lon, lat, elevator, blind_strip FROM stations WHERE station_id = %s", (station_id,))
            row = cur.fetchone()
            if row is None:
                log.info(f"Station with id {station_id} could not be read from the db")
                return None
            return {
                "name": row[0],
                "lon": row[1],
                "lat": row[2],
                "elevator": row[3],
                "blind_strip": row[4]
            }
    except Exception as e:
        log.error(f"Database error: {e}")
        raise
    finally:
        connection_pool.putconn(conn)