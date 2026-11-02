import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from exceptions.exceptions import StationNotFoundError
from db.database import connection_pool

import psycopg2
from psycopg2.extras import execute_values
import logging

log = logging.getLogger(__name__)

def fill_lines_by_station(station_id:str, line_id_list: list[str]):

    conn = None

    try:
        conn = connection_pool.getconn()

        with conn.cursor() as cur:

            station_exists, existing_lines = parameter_status(cur, station_id, line_id_list)

            if not station_exists:
                raise StationNotFoundError(f"Station {station_id} could not be found")
            
            valid_line_ids = [lid for lid, exists in existing_lines.items() if exists]
            missing_line_ids = [lid for lid, exists in existing_lines.items() if not exists]

            if missing_line_ids:
                log.warning(f"Line IDs not found, skipping: {missing_line_ids}")

            if not valid_line_ids:
                log.warning(f"No valid line IDs to insert for station {station_id}")
                return []
            
            execute_values(cur, """
                INSERT INTO public.line_stations (line_id, station_id)
                VALUES %s
                ON CONFLICT (line_id, station_id) DO NOTHING
            """, [(line_id, station_id) for line_id in valid_line_ids])

            log.info(f"Inserted {cur.rowcount} line-station relation(s) for station {station_id}")

        conn.commit()
        return valid_line_ids


    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        log.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            connection_pool.putconn(conn)

def parameter_status(cur, station_id, line_ids):

    cur.execute("""
        SELECT
            EXISTS(SELECT 1 FROM stations WHERE station_id = %s) AS station_exists
        """, (station_id,))
    station_exists = cur.fetchone()[0]
    
    cur.execute("""
        SELECT line_id FROM lines
            WHERE line_id = ANY(%s)
        """, (line_ids,))
    existing_ids = {row[0] for row in cur.fetchall()}
    
    existing_lines = {line_id: (line_id in existing_ids) for line_id in line_ids}

    return station_exists, existing_lines