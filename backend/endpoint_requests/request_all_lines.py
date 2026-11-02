import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from exceptions.exceptions import StationNotFoundError
from db.database import connection_pool

import psycopg2
import logging

log = logging.getLogger(__name__)

#WORK IN PROGRESS
async def get_all_lines_for_station(station_id: str):

    conn = None

    try:
        conn = connection_pool.getconn()

        with conn.cursor() as cur:

            cur.execute("""
                SELECT EXISTS(SELECT 1 FROM stations WHERE station_id = %s)
            """, (station_id,))
            station_exists = cur.fetchone()[0]

            if not station_exists:
                raise StationNotFoundError(f"Station {station_id} could not be found")
            
            cur.execute("""
                SELECT l.line_name, l.line_id
                FROM line_stations ls
                JOIN lines l ON l.line_id=ls.line_id
                WHERE ls.station_id = %s
                ORDER BY l.line_id
            """, (station_id,))

            rows = cur.fetchall()
            lines_dict = {row[1]: row[0] for row in rows}

        return lines_dict


    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        log.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            connection_pool.putconn(conn)

