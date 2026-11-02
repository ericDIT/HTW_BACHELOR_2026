from datetime import datetime
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.database import connection_pool

import psycopg2
import logging

log = logging.getLogger(__name__)

async def get_timeframe_facts_by_station(from_date: str, to_date: str, station_id: str):

    conn = None

    try:
        conn = connection_pool.getconn()

        with conn.cursor() as cur:

            date_format = '%Y-%m-%d'
            from_date_obj = datetime.strptime(from_date, date_format).date()
            to_date_obj = datetime.strptime(to_date, date_format).date()

            if from_date_obj>=to_date_obj:
                log.error(f"From date has to be at least 1 day before to date - From date: {from_date_obj} | To date: {to_date_obj}")

            cur.execute("""
                SELECT 1 FROM delays
                WHERE delay_date BETWEEN %s AND %s
                AND station_id = %s
            """, (from_date_obj, to_date_obj, station_id))

            exists = cur.fetchone()[0]
            if not exists:
                log.warning(f"No data found for {from_date}-{to_date} for station with ID: {station_id}")
                return None
            
            cur.execute("""
                SELECT delays.delay_minutes, delays.cancelled, delays.occupancy, lines.transport_type
                FROM delays
                LEFT JOIN lines ON delays.lines_id = lines.line_id
                WHERE delays.delay_date BETWEEN %s AND %s
                AND delays.station_id = %s
            """, (from_date_obj, to_date_obj, station_id))

            rows = cur.fetchall()
            
            
    
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        log.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            connection_pool.putconn(conn)