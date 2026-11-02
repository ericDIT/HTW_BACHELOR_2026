import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from exceptions.exceptions import StationNotFoundError, NoDataFoundError
from db.database import connection_pool

import psycopg2
import logging

log = logging.getLogger(__name__)

"""
This script accesses information from the delays-table, aggregates various values and
loads it into the delay_facts_daily_by_station table.

This table then represents facts of a day by station, differentiating in morning and evening times.

Author: @E. Meyer
"""
def transform_day_to_facts_by_station(fact_date: str, station_id: str):

    conn=None

    try:
        conn = connection_pool.getconn()

        with conn.cursor() as cur:

            station_exists, data_exists = station_and_date_status(cur, fact_date, station_id)

            if not station_exists:
                raise StationNotFoundError(f"Station {station_id} could not be found")
            
            if not data_exists:
                raise NoDataFoundError(f"No data available for: {fact_date}")

            cur.execute("""
                SELECT avg_delay, delay_rate, morning_avg_delay, evening_avg_delay,
                       morning_departures, evening_departures, total_departures,
                       occupancy_occurance_l, occupancy_occurance_m, occupancy_occurance_h,
                       max_delay, avg_bus_delay, avg_train_delay
                FROM public.delay_facts_daily_by_station
                WHERE fact_date = %s
                AND station_id = %s
            """, (fact_date, station_id))

            already_existing = cur.fetchone()
            if already_existing:
                log.info(f"Facts already exist for {fact_date} on station {station_id} -> returning cached.")
                return {
                    "average_delay": already_existing[0],
                    "delay_rate": already_existing[1],
                    "morning_avg_delay": already_existing[2],
                    "evening_avg_delay": already_existing[3],
                    "morning_departures": already_existing[4],
                    "evening_departures": already_existing[5],
                    "total_departures": already_existing[6],
                    "occupancy_occurance_l": already_existing[7],
                    "occupancy_occurance_m": already_existing[8],
                    "occupancy_occurance_h": already_existing[9],
                    "max_delay": already_existing[10],
                    "avg_bus_delay": already_existing[11],
                    "avg_train_delay": already_existing[12]
                }

            cur.execute("""
                        SELECT d.delay_minutes, d.occupancy, d.scheduled_time, l.transport_type, d.cancelled
                        FROM delays d
                        JOIN lines l ON d.line_id = l.line_id
                        WHERE delay_day = %s 
                        AND station_id = %s
                    """, (fact_date, station_id))
            
            rows = cur.fetchall()

            if not rows:
                log.warning(f"No data for {fact_date}, station {station_id}")
                return
            
            rows = [row for row in rows if row[0] is not None]

            #count_entries = len(rows)
            count_not_cancelled = sum(1 for row in rows if not row[4])

            pos_delay_sum = sum(int(row[0]) for row in rows if int(row[0]) >= 0 and not row[4])
            #sum_delay = sum(int(row[0]) for row in rows)
            count_delayed_dep = sum(1 for row in rows if int(row[0]) >= 1 and not row[4])

            avg_delay = round(pos_delay_sum / count_not_cancelled if count_not_cancelled > 0 else 0, 1)
            delay_rate = round(count_delayed_dep / count_not_cancelled if count_not_cancelled > 0 else 0, 2)

            occupancy_occurance_l = sum(1 for row in rows if str(row[1])=="L" and not row[4])
            occupancy_occurance_m = sum(1 for row in rows if str(row[1])=="M" and not row[4])
            occupancy_occurance_h = sum(1 for row in rows if str(row[1])=="H" and not row[4])

            max_delay = max((int(row[0]) for row in rows), default=0)

            #--- Aggregates for the morning from 07:00-10:00 ---
            morning = [
                row for row in rows
                if 7 <= row[2].hour < 10
                and not row[4]
            ]
            count_morning_dep = len(morning)
            pos_sum_morning_delay = sum(int(d[0]) for d in morning if int(d[0])>=0)
            #sum_morning_delay = sum(int(d[0]) for d in morning)
            morning_avg_delay = round(pos_sum_morning_delay / count_morning_dep if count_morning_dep > 0 else 0, 1)

            #--- Aggregates for the evening from 16:00-19:00 ---
            evening = [
                row for row in rows
                if 16 <= row[2].hour < 19
                and not row[4]
            ]
            count_evening_dep = len(evening)
            pos_sum_evening_delay = sum(int(d[0]) for d in evening if int(d[0])>=0)
            #sum_evening_delay = sum(int(d[0]) for d in evening)
            evening_avg_delay = round(pos_sum_evening_delay / count_evening_dep if count_evening_dep > 0 else 0, 1)

            #--- Aggregates for bus and train departures ---
            bus_entries = [row for row in rows if str(row[3]) == "Bus" and not row[4]]
            train_entries = [row for row in rows if str(row[3]) == "S" and not row[4]]
            
            sum_bus_delays = sum(int(row[0]) for row in bus_entries)
            sum_train_delays = sum(int(row[0]) for row in train_entries)

            avg_bus_delay = round(sum_bus_delays / len(bus_entries), 1) if bus_entries else 0
            avg_train_delay = round(sum_train_delays / len(train_entries), 1) if train_entries else 0

            # note: 15 parameters
            cur.execute("""
                        INSERT INTO public.delay_facts_daily_by_station
                        (station_id, fact_date,
                         avg_delay, delay_rate, morning_avg_delay,
                        evening_avg_delay, morning_departures, evening_departures,
                        occupancy_occurance_l, occupancy_occurance_m, occupancy_occurance_h,
                        total_departures, max_delay, avg_bus_delay, avg_train_delay)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (station_id, fact_date) DO UPDATE SET
                            avg_delay = EXCLUDED.avg_delay,
                            delay_rate = EXCLUDED.delay_rate,
                            morning_avg_delay = EXCLUDED.morning_avg_delay,
                            evening_avg_delay = EXCLUDED.evening_avg_delay,
                            morning_departures = EXCLUDED.morning_departures,
                            evening_departures = EXCLUDED.evening_departures,
                            occupancy_occurance_l = EXCLUDED.occupancy_occurance_l,
                            occupancy_occurance_m = EXCLUDED.occupancy_occurance_m,
                            occupancy_occurance_h = EXCLUDED.occupancy_occurance_h,
                            total_departures = EXCLUDED.total_departures,
                            max_delay = EXCLUDED.max_delay,
                            avg_bus_delay = EXCLUDED.avg_bus_delay,
                            avg_train_delay = EXCLUDED.avg_train_delay""",
                        (station_id, fact_date, avg_delay, delay_rate, morning_avg_delay,
                         evening_avg_delay, count_morning_dep, count_evening_dep, occupancy_occurance_l,
                         occupancy_occurance_m, occupancy_occurance_h, count_not_cancelled, max_delay,
                         avg_bus_delay, avg_train_delay)
                        )
            log.info(f"Data aggregated for day: {fact_date}")
        
        conn.commit()

        return {
            "average_delay": avg_delay,
            "max_delay": max_delay,
            "delay_rate": delay_rate,
            "morning_avg_delay": morning_avg_delay,
            "evening_avg_delay": evening_avg_delay,
            "morning_departures": count_morning_dep,
            "evening_departures": count_evening_dep,
            "total_departures": count_not_cancelled,
            "occupancy_occurance_l": occupancy_occurance_l,
            "occupancy_occurance_m": occupancy_occurance_m,
            "occupancy_occurance_h": occupancy_occurance_h,
            "avg_bus_delay": avg_bus_delay,
            "avg_train_delay": avg_train_delay
        }

    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        log.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            connection_pool.putconn(conn)

def station_and_date_status(cur, fact_date: str, station_id: str):
    cur.execute("""
        SELECT
            EXISTS(SELECT 1 FROM stations WHERE station_id = %s) AS station_exists,
            EXISTS(SELECT 1 FROM delays WHERE station_id = %s AND delay_day = %s) AS data_exists
    """, (station_id, station_id, fact_date))
    return cur.fetchone()

if __name__ == "__main__":
    test_params = [
        "2026-06-06",
        "A=1@O=S Halensee (Berlin)@X=13290147@Y=52496698@U=86@L=900040101@",
    ]
    transform_day_to_facts_by_station(test_params[0], test_params[1])