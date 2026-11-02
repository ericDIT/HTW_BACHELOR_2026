from exceptions.exceptions import StationNotFoundError, LineNotFoundError, NoDataFoundError

HALENSEE_ID="A=1@O=S Halensee (Berlin)@X=13290147@Y=52496698@U=86@L=900040101@"


def test_root_returns_ok(client):
    response = client.get("/api/")
    assert response.status_code == 200
    assert response.json() == {"message": "API läuft"}


class TestGetStation:
    def test_returns_station_data(self, client, monkeypatch):
        monkeypatch.setattr(
            "app.server.get_station_by_id",
            lambda station_id: {"station_id": station_id, "station_name": "Test Station"}
        )
        response = client.get("/api/station", params={"station_id": HALENSEE_ID})
        assert response.status_code == 200
        assert response.json()["station_name"] == "Test Station"

    def test_returns_404_when_station_not_found(self, client, monkeypatch):
        monkeypatch.setattr("app.server.get_station_by_id", lambda station_id: None)
        response = client.get("/api/station", params={"station_id": "unknown"})
        assert response.status_code == 404

    def test_missing_station_id_returns_422(self, client):
        response = client.get("/api/station")
        assert response.status_code == 422


class TestGetStationInfo:
    def test_returns_station_info(self, client, monkeypatch):
        async def fake_get_station_info_by_id(station_id):
            return {"stop_name": "S Halensee", "departures": []}

        monkeypatch.setattr("app.server.get_station_info_by_id", fake_get_station_info_by_id)
        response = client.get("/api/station/info", params={"station_id": HALENSEE_ID})
        assert response.status_code == 200
        assert response.json()["stop_name"] == "S Halensee"

    def test_returns_404_when_no_info(self, client, monkeypatch):
        async def fake_get_station_info_by_id(station_id):
            return None

        monkeypatch.setattr("app.server.get_station_info_by_id", fake_get_station_info_by_id)
        response = client.get("/api/station/info", params={"station_id": "unknown"})
        assert response.status_code == 404


class TestGetLinesOfStation:
    def test_returns_lines(self, client, monkeypatch):
        async def fake_get_all_lines(station_id):
            return [{"line_id": "S41", "line_name": "S41"}]

        monkeypatch.setattr("app.server.get_all_lines_for_station", fake_get_all_lines)
        response = client.get("/api/station/lines", params={"station_id": HALENSEE_ID})
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_returns_404_when_station_not_found(self, client, monkeypatch):
        async def fake_get_all_lines(station_id):
            raise StationNotFoundError(f"Station {station_id} could not be found")

        monkeypatch.setattr("app.server.get_all_lines_for_station", fake_get_all_lines)
        response = client.get("/api/station/lines", params={"station_id": "unknown"})
        assert response.status_code == 404


class TestDailyFactsByStation:
    def test_returns_facts(self, client, monkeypatch):
        monkeypatch.setattr(
            "app.server.transform_day_to_facts_by_station",
            lambda fact_date, station_id: {"average_delay": 2.3}
        )
        response = client.post(
            "/api/daily_facts/by_station",
            params={"fact_date": "2026-08-02", "station_id": HALENSEE_ID}
        )
        assert response.status_code == 200
        assert response.json()["average_delay"] == 2.3

    def test_returns_404_when_station_not_found(self, client, monkeypatch):
        def raise_error(fact_date, station_id):
            raise StationNotFoundError("not found")

        monkeypatch.setattr("app.server.transform_day_to_facts_by_station", raise_error)
        response = client.post(
            "/api/daily_facts/by_station",
            params={"fact_date": "2026-08-02", "station_id": "unknown"}
        )
        assert response.status_code == 404

    def test_returns_404_when_no_data(self, client, monkeypatch):
        def raise_error(fact_date, station_id):
            raise NoDataFoundError("no data")

        monkeypatch.setattr("app.server.transform_day_to_facts_by_station", raise_error)
        response = client.post(
            "/api/daily_facts/by_station",
            params={"fact_date": "2026-08-06", "station_id": HALENSEE_ID}
        )
        assert response.status_code == 404

    def test_missing_params_returns_422(self, client):
        response = client.post("/api/daily_facts/by_station")
        assert response.status_code == 422


class TestDailyFactsByLine:
    def test_returns_facts(self, client, monkeypatch):
        monkeypatch.setattr(
            "app.server.transform_day_to_facts_by_line",
            lambda fact_date, station_id, line_id: {"average_delay": 1.5}
        )
        response = client.post(
            "/api/daily_facts/by_line",
            params={"fact_date": "2026-08-02", "station_id": HALENSEE_ID, "line_id": "S41"}
        )
        assert response.status_code == 200

    def test_returns_404_when_line_not_found(self, client, monkeypatch):
        def raise_error(fact_date, station_id, line_id):
            raise LineNotFoundError("line not found")

        monkeypatch.setattr("app.server.transform_day_to_facts_by_line", raise_error)
        response = client.post(
            "/api/daily_facts/by_line",
            params={"fact_date": "2026-08-02", "station_id": HALENSEE_ID, "line_id": "unknown"}
        )
        assert response.status_code == 404

class TestRateLimiting:
    def test_daily_facts_by_station_rate_limited_after_5_requests(self, client, monkeypatch):
        from app.server import limiter
        limiter.enabled = True  

        monkeypatch.setattr(
            "app.server.transform_day_to_facts_by_station",
            lambda fact_date, station_id: {"average_delay": 2.3}
        )

        for _ in range(5):
            response = client.post(
                "/api/daily_facts/by_station",
                params={"fact_date": "2026-08-02", "station_id": HALENSEE_ID}
            )
            assert response.status_code == 200

        response = client.post(
            "/api/daily_facts/by_station",
            params={"fact_date": "2026-08-02", "station_id": HALENSEE_ID}
        )
        assert response.status_code == 429

        limiter.enabled = False  # zurücksetzen für nachfolgende Tests

class TestDailyFactsTrend:
    def test_returns_trend_data(self, client, monkeypatch):
        monkeypatch.setattr(
            "app.server.read_timeframe_by_station",
            lambda station_id, from_date, to_date: [{"fact_date": "2026-08-01", "average_delay": 2.0}]
        )
        response = client.get(
            "/api/daily_facts/trend",
            params={"station_id": HALENSEE_ID, "from_date": "2026-08-01", "to_date": "2026-08-06"}
        )
        assert response.status_code == 200

    def test_returns_404_when_station_not_found(self, client, monkeypatch):
        def raise_error(station_id, from_date, to_date):
            raise StationNotFoundError("not found")
        monkeypatch.setattr("app.server.read_timeframe_by_station", raise_error)
        response = client.get(
            "/api/daily_facts/trend",
            params={"station_id": "unknown", "from_date": "2026-08-01", "to_date": "2026-08-06"}
        )
        assert response.status_code == 404

class TestJobsAuth:
    def test_start_job_requires_api_key(self, client):
        response = client.post("/api/jobs/start", json={"job": "daily_1h_period", "station_id": HALENSEE_ID})
        assert response.status_code == 401

    def test_start_job_rejects_wrong_api_key(self, client):
        response = client.post(
            "/api/jobs/start",
            json={"job": "daily_1h_period", "station_id": HALENSEE_ID},
            headers={"X-Api-Key": "wrong-key"}
        )
        assert response.status_code == 401

    def test_start_job_accepts_correct_api_key(self, client, monkeypatch):
        monkeypatch.setattr("app.server.start_jobs", lambda job, station_id: True)
        response = client.post(
            "/api/jobs/start",
            json={"job": "daily_1h_period", "station_id": HALENSEE_ID},
            headers={"X-Api-Key": os.getenv("INTERNAL_API_KEY")}
        )
        assert response.status_code == 200

    def test_start_job_returns_error_for_unknown_job(self, client, monkeypatch):
        monkeypatch.setattr("app.server.start_jobs", lambda job, station_id: False)
        response = client.post(
            "/api/jobs/start",
            json={"job": "nonexistent_job", "station_id": HALENSEE_ID},
            headers={"X-Api-Key": os.getenv("INTERNAL_API_KEY")}
        )
        assert response.status_code == 200
        assert response.json() == {"error": "unknown job"}

    def test_jobs_list_requires_api_key(self, client):
        response = client.get("/api/jobs")
        assert response.status_code == 401