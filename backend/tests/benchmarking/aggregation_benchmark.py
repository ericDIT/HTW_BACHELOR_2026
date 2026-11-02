import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


import time
import statistics

from transforming.daily_facts_by_station import transform_day_to_facts_by_station
from db.database import connection_pool


def clear_cache_entry(fact_date: str, station_id: str):
    conn = connection_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM public.delay_facts_daily_by_station WHERE fact_date = %s AND station_id = %s",
                (fact_date, station_id)
            )
        conn.commit()
    finally:
        connection_pool.putconn(conn)


def benchmark_aggregation(fact_date: str, station_id: str, warm_runs: int = 5) -> dict:
    #facts_date should not exits yet!!!!!!!!
    clear_cache_entry(fact_date, station_id)

    try:
        start = time.perf_counter()
        transform_day_to_facts_by_station(fact_date, station_id)
        cold_duration = time.perf_counter() - start
    except Exception as e:
        print(f"Kaltstart-Benchmark fehlgeschlagen für {station_id} @ {fact_date}: {e}")
        return None

    warm_durations = []
    for _ in range(warm_runs):
        start = time.perf_counter()
        transform_day_to_facts_by_station(fact_date, station_id)
        warm_durations.append(time.perf_counter() - start)

    warm_avg = statistics.mean(warm_durations)
    warm_median = statistics.median(warm_durations)
    warm_stdev = statistics.stdev(warm_durations) if len(warm_durations) > 1 else 0.0
    warm_min = min(warm_durations)
    warm_max = max(warm_durations)

    print(f"--- {station_id} @ {fact_date} ---")
    print(f"Kaltstart:                          {cold_duration:.4f}s")
    print(f"Cache-Treffer Ø ({warm_runs} Läufe):  {warm_avg:.4f}s  (Median: {warm_median:.4f}s, StdAbw: {warm_stdev:.4f}s)")
    print(f"Cache-Treffer Min/Max:               {warm_min:.4f}s / {warm_max:.4f}s")
    print(f"Speedup (Kaltstart / Ø Cache):        {cold_duration / warm_avg:.1f}x")

    return {
        "fact_date": fact_date,
        "station_id": station_id,
        "cold_duration": cold_duration,
        "warm_avg": warm_avg,
        "warm_median": warm_median,
        "warm_stdev": warm_stdev,
        "warm_min": warm_min,
        "warm_max": warm_max,
        "warm_runs": warm_runs,
    }


def benchmark_multiple(cases: list[tuple[str, str]], warm_runs: int = 5) -> list[dict]:
    results = []
    for fact_date, station_id in cases:
        result = benchmark_aggregation(fact_date, station_id, warm_runs)
        if result:
            results.append(result)
    return results


if __name__ == "__main__":
    HALENSEE_ID = "A=1@O=S Halensee (Berlin)@X=13290147@Y=52496698@U=86@L=900040101@"
    results = benchmark_multiple([
        ("2026-08-04", HALENSEE_ID)
    ])