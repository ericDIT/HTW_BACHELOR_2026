import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from exceptions.exceptions import NoDataFoundError
from db.database import connection_pool

import psycopg2
import logging
from datetime import datetime

log = logging.getLogger(__name__)

def parameter_validation(station_id: str, from_day: str, to_day: str) -> None:

    if not station_id or len(station_id) < 1:
        log.error("Invalid station ID")
        raise ValueError("station_id must not be empty")
    
    try:
        from_day = datetime.strptime(from_day, "%Y-%m-%d").date()
        to_day = datetime.strptime(to_day, "%Y-%m-%d").date()
    except ValueError as e:
        raise ValueError(f"from_day/to_day have to be in YYYY-MM-DD format: {e}")

    if from_day == to_day:
        raise ValueError("source_day and target_day should not be identical")

    if to_day < from_day:
        raise ValueError(f"to_day ({to_day}) is before from_day ({from_day})")

def read_timeframe_by_station(station_id: str, from_day: str, to_day: str):

    parameter_validation(station_id, from_day, to_day)

    conn = None

    try:
        conn = connection_pool.getconn()

        with conn.cursor() as cur:

            cur.execute("""
                        SELECT fact_date, avg_delay, delay_rate, morning_avg_delay, 
                            evening_avg_delay, morning_departures, evening_departures, total_departures,
                            occupancy_occurance_l, occupancy_occurance_m, occupancy_occurance_h,
                            max_delay, avg_bus_delay, avg_train_delay
                        FROM delay_facts_daily_by_station
                        WHERE station_id = %s
                        AND fact_date BETWEEN %s AND %s
                        ORDER BY fact_date
                    """, (station_id,from_day,to_day))
            
            rows = cur.fetchall()

            if len(rows)<1:
                raise NoDataFoundError(f"No data found for station {station_id} in the given timeframe")
            
            return [
                {
                    "fact_date": row[0],
                    "average_delay": row[1],
                    "delay_rate": row[2],
                    "morning_avg_delay": row[3],
                    "evening_avg_delay": row[4],
                    "morning_departures": row[5],
                    "evening_departures": row[6],
                    "total_departures": row[7],
                    "occupancy_occurance_l": row[8],
                    "occupancy_occurance_m": row[9],
                    "occupancy_occurance_h": row[10],
                    "max_delay": row[11],
                    "avg_bus_delay": row[12],
                    "avg_train_delay": row[13]
                }
                for row in rows
            ]
        
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        log.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            connection_pool.putconn(conn)