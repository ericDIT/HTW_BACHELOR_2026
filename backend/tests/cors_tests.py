class TestCORS:
    def test_allows_configured_origin(self, client):
        response = client.get(
            "/api/",
            headers={"Origin": "http://localhost:5173"}
        )
        assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"

    def test_preflight_rejects_unknown_origin(self, client):
        response = client.options(
            "/api/station",
            headers={
                "Origin": "http://evil-site.com",
                "Access-Control-Request-Method": "GET"
            }
        )
        assert "access-control-allow-origin" not in response.headers or \
               response.headers.get("access-control-allow-origin") != "http://evil-site.com"