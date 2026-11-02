import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from exceptions.exceptions import NoDataFoundError, StationNotFoundError
from db.database import connection_pool

import psycopg2
import logging

log = logging.getLogger(__name__)

def read_last_30_days(station_id: str):

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
                        SELECT fact_date, avg_delay, delay_rate, morning_avg_delay, 
                            evening_avg_delay, morning_departures, evening_departures, total_departures,
                            occupancy_occurance_l, occupancy_occurance_m, occupancy_occurance_h,
                            max_delay, avg_bus_delay, avg_train_delay
                        FROM delay_facts_daily_by_station
                        WHERE station_id = %s
                        AND fact_date >= CURRENT_DATE - INTERVAL '30 days'
                        ORDER BY fact_date
                        """, (station_id,))
            
            rows = cur.fetchall()

            if len(rows)<1:
                raise NoDataFoundError(f"No data found for the last 30 days at the station with id: {station_id}")
            
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