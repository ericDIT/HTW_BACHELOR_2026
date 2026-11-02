import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.database import connection_pool

import psycopg2
import logging
from datetime import datetime

log = logging.getLogger(__name__)


def _validate_params(target_day: str, source_day: str, start_time: str, end_time: str) -> None:
    """Checks validity of parameters before a connection is being established"""
    try:
        target_date = datetime.strptime(target_day, "%Y-%m-%d").date()
        source_date = datetime.strptime(source_day, "%Y-%m-%d").date()
    except ValueError as e:
        raise ValueError(f"target_day/source_day have to be in YYYY-MM-DD format: {e}")

    try:
        start = datetime.strptime(start_time, "%H:%M:%S").time()
        end = datetime.strptime(end_time, "%H:%M:%S").time()
    except ValueError as e:
        raise ValueError(f"start_time/end_time have to be in HH:MM:SS format: {e}")

    if start >= end:
        raise ValueError(f"start_time ({start_time}) has to be before end_time ({end_time})")

    if source_date == target_date:
        raise ValueError("source_day and target_day should not be identical")

    if target_date < source_date:
        log.warning(f"target_day ({target_day}) is before source_day ({source_day}) (might be okay)")


def back_fill_db_information(station_id: str, target_day: str, source_day: str, start_time: str, end_time: str) -> bool:

    _validate_params(target_day, source_day, start_time, end_time)

    conn = None

    try:
        conn = connection_pool.getconn()

        with conn.cursor() as cur:

            # Does source data even exist?
            cur.execute("""
                        SELECT count(*) FROM delays
                        WHERE delay_day = %s
                          AND scheduled_time BETWEEN %s AND %s
                          AND station_id = %s
                    """, (source_day, start_time, end_time, station_id))
            source_count = cur.fetchone()[0]
            if not source_count:
                log.warning(f"No data found as a source for: {source_day} ({start_time}-{end_time}) and station with ID: {station_id}")
                return False

            # Does target data exist?
            cur.execute("""
                        SELECT count(*) FROM delays
                        WHERE delay_day = %s
                          AND scheduled_time BETWEEN %s AND %s
                          AND station_id = %s
                    """, (target_day, start_time, end_time, station_id))

            target_count = cur.fetchone()[0]
            if target_count:
                log.warning(f"Data for target day: {target_day} and station with ID: {station_id} already exists")
                return False

            cur.execute("""
                        INSERT INTO delays
                            (trip_id, station_id, line_id, delay_day, scheduled_time, cancelled, actual_time, delay_minutes, occupancy)
                        SELECT
                            trip_id, station_id, line_id, %s::date, scheduled_time, cancelled, actual_time, delay_minutes, occupancy
                        FROM delays
                        WHERE delay_day = %s
                          AND scheduled_time BETWEEN %s AND %s
                          AND station_id = %s;
                    """, (target_day, source_day, start_time, end_time, station_id))

            inserted = cur.rowcount
            conn.commit()

            log.info(f"Successfully backfilled {inserted} row(s) into {target_day} from {source_day} for station {station_id}")
            return True

    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        log.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            connection_pool.putconn(conn)


if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    bf_params = {
        "station_id": "A=1@O=S Halensee (Berlin)@X=13290147@Y=52496698@U=86@L=900040101@",
        "target_day": "2026-07-16",
        "source_day": "2026-07-05",
        "start_time": "06:54:00",
        "end_time": "10:05:00"
    }

    back_fill_db_information(bf_params["station_id"], bf_params["target_day"],
                              bf_params["source_day"], bf_params["start_time"],
                              bf_params["end_time"])