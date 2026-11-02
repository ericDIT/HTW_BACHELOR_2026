import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.database import connection_pool
from exceptions.exceptions import StationNotFoundError, NoDataFoundError, LineNotFoundError

import psycopg2
from psycopg2.extras import RealDictCursor
import logging

log = logging.getLogger(__name__)

"""
This script accesses information from the delays-table, aggregates various values and
loads it into the delay_facts_daily_by_line table.

This table then represents facts of a day by line and station.

Author: @E. Meyer
"""
def transform_day_to_facts_by_line(fact_date: str, station_id: str, line_id: str):

    conn = None

    try:
        conn = connection_pool.getconn()

        with conn.cursor() as cur:

            station_exists, line_exists, data_exists = parameter_status(cur, fact_date, station_id, line_id)

            if not station_exists:
                raise StationNotFoundError(f"Station {station_id} could not be found")

            if not line_exists:
                raise LineNotFoundError(f"Line {line_id} could not be found")

            if not data_exists:
                raise NoDataFoundError(f"No data available for: {fact_date}")

            # --- Return cached facts if they already exist ---
            already_existing = get_existing_facts(conn, fact_date, station_id, line_id)
            if already_existing:
                log.info(f"Facts already exist for {fact_date}, station {station_id}, line {line_id} -> returning cached.")
                return already_existing

            cur.execute("""
                SELECT d.delay_minutes, d.occupancy, d.scheduled_time, d.cancelled
                FROM delays d
                WHERE delay_day = %s
                AND station_id = %s
                AND line_id = %s
            """, (fact_date, station_id, line_id))

            rows = cur.fetchall()

            if not rows:
                log.warning(f"No data for {fact_date}, station {station_id}, line {line_id}")
                return

            rows = [row for row in rows if row[0] is not None]

            cancelled_journey_count = sum(1 for row in rows if row[3])

            count_entries = len(rows)
            count_not_cancelled = sum(1 for row in rows if not row[3])

            pos_delay_sum = sum(int(row[0]) for row in rows if int(row[0]) >= 0 and not row[3])
            #sum_delay = sum(int(row[0]) for row in rows)
            count_delayed_dep = sum(1 for row in rows if int(row[0]) >= 1 and not row[3])

            avg_delay = round(pos_delay_sum / count_not_cancelled if count_not_cancelled > 0 else 0, 1)
            delay_rate = round(count_delayed_dep / count_not_cancelled if count_not_cancelled > 0 else 0, 2)
            max_delay = max((int(row[0]) for row in rows), default=0)

            occupancy_occurance_l = sum(1 for row in rows if str(row[1]) == "L" and not row[3])
            occupancy_occurance_m = sum(1 for row in rows if str(row[1]) == "M" and not row[3])
            occupancy_occurance_h = sum(1 for row in rows if str(row[1]) == "H" and not row[3])

            #--- Aggregates for the morning from 07:00-10:00 ---
            morning = [row for row in rows if 7 <= row[2].hour < 10 and not row[3]]
            count_morning_dep = len(morning)
            morning_avg_delay = round(
                sum(int(row[0]) for row in morning) / count_morning_dep
                if count_morning_dep > 0 else 0, 1
            )

            #--- Aggregates for the evening from 16:00-19:00 ---
            evening = [row for row in rows if 16 <= row[2].hour < 19 and not row[3]]
            count_evening_dep = len(evening)
            evening_avg_delay = round(
                sum(int(row[0]) for row in evening) / count_evening_dep
                if count_evening_dep > 0 else 0, 1
            )

            # note: 15 parameters
            cur.execute("""
                INSERT INTO public.delay_facts_daily_by_line
                (station_id, line_id, fact_date,
                 avg_delay, max_delay, delay_rate,
                 morning_avg_delay, evening_avg_delay,
                 morning_departures, evening_departures, total_departures,
                 occupancy_occurance_l, occupancy_occurance_m, occupancy_occurance_h, cancelled_journey_count)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (station_id, line_id, fact_date) DO UPDATE SET
                    avg_delay               = EXCLUDED.avg_delay,
                    max_delay               = EXCLUDED.max_delay,
                    delay_rate              = EXCLUDED.delay_rate,
                    morning_avg_delay       = EXCLUDED.morning_avg_delay,
                    evening_avg_delay       = EXCLUDED.evening_avg_delay,
                    morning_departures      = EXCLUDED.morning_departures,
                    evening_departures      = EXCLUDED.evening_departures,
                    total_departures        = EXCLUDED.total_departures,
                    occupancy_occurance_l   = EXCLUDED.occupancy_occurance_l,
                    occupancy_occurance_m   = EXCLUDED.occupancy_occurance_m,
                    occupancy_occurance_h   = EXCLUDED.occupancy_occurance_h,
                    cancelled_journey_count = EXCLUDED.cancelled_journey_count""",
                (station_id, line_id, fact_date,
                 avg_delay, max_delay, delay_rate,
                 morning_avg_delay, evening_avg_delay,
                 count_morning_dep, count_evening_dep, count_entries,
                 occupancy_occurance_l, occupancy_occurance_m, occupancy_occurance_h,
                 cancelled_journey_count)
            )
            log.info(f"Data aggregated for day: {fact_date}, station: {station_id}, line: {line_id}")

        conn.commit()

        return {
                "average_delay": avg_delay,
                "max_delay": max_delay,
                "delay_rate": delay_rate,
                "morning_avg_delay": morning_avg_delay,
                "evening_avg_delay": evening_avg_delay,
                "morning_departures": count_morning_dep,
                "evening_departures": count_evening_dep,
                "total_departures": count_entries,
                "occupancy_occurance_l": occupancy_occurance_l,
                "occupancy_occurance_m": occupancy_occurance_m,
                "occupancy_occurance_h": occupancy_occurance_h,
                "cancelled_journey_count": cancelled_journey_count
            }

    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        log.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            connection_pool.putconn(conn)


def get_existing_facts(conn, fact_date: str, station_id: str, line_id: str):
    """
    Returns the already aggregated facts as a dict (keys match the API response),
    or None if no entry exists yet.
    """
    with conn.cursor(cursor_factory=RealDictCursor) as dict_cur:
        dict_cur.execute("""
            SELECT
                avg_delay AS average_delay,
                max_delay,
                delay_rate,
                morning_avg_delay,
                evening_avg_delay,
                morning_departures,
                evening_departures,
                total_departures,
                occupancy_occurance_l,
                occupancy_occurance_m,
                occupancy_occurance_h,
                cancelled_journey_count
            FROM public.delay_facts_daily_by_line
            WHERE fact_date = %s
            AND station_id = %s
            AND line_id = %s
        """, (fact_date, station_id, line_id))

        row = dict_cur.fetchone()
        return dict(row) if row else None


def parameter_status(cur, fact_date: str, station_id: str, line_id: str):
    cur.execute("""
        SELECT
            EXISTS(SELECT 1 FROM stations WHERE station_id = %s) AS station_exists,
            EXISTS(SELECT 1 FROM lines WHERE line_id = %s) AS line_exists,
            EXISTS(SELECT 1 FROM delays WHERE station_id = %s AND delay_day = %s AND line_id = %s) AS data_exists
    """, (station_id, line_id, station_id, fact_date, line_id))
    return cur.fetchone()

if __name__ == "__main__":
    test_params = [
        "2026-06-06",
        "A=1@O=S Halensee (Berlin)@X=13290147@Y=52496698@U=86@L=900040101@",
        1
    ]
    transform_day_to_facts_by_line(test_params[0], test_params[1], test_params[2])