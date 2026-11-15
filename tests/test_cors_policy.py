"""Self-host CORS: no wildcard with credentials.

The self-host API has no login. With ``allow_origins=["*"]`` and credentials
any web page the user opened could call it from their browser. The default is
now the local dashboard origins, ALLOWED_ORIGINS widens it.
"""
import asyncio

import httpx
import pytest

app_module = pytest.importorskip("app")


def test_self_host_default_is_the_local_dashboard_not_a_wildcard():
    origins = app_module._cors_origins(False, env={})
    assert "*" not in origins
    assert "http://localhost:5175" in origins
    assert "http://localhost:5173" in origins


def test_allowed_origins_env_overrides_the_default():
    env = {"ALLOWED_ORIGINS": "https://studio.example.com, https://b.example.com"}
    assert app_module._cors_origins(False, env=env) == [
        "https://studio.example.com", "https://b.example.com"]


def test_blank_allowed_origins_falls_back_to_the_default():
    assert app_module._cors_origins(False, env={"ALLOWED_ORIGINS": " , "}) == \
        app_module._SELF_HOST_CORS_ORIGINS


def _preflight(origin):
    async def _do():
        transport = httpx.ASGITransport(app=app_module.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as c:
            return await c.options("/api/config", headers={
                "Origin": origin, "Access-Control-Request-Method": "GET"})
    return asyncio.run(_do())


def test_a_foreign_site_gets_no_cors_grant_from_the_running_app():
    r = _preflight("https://evil.example.com")
    # Without Access-Control-Allow-Origin the browser refuses the response.
    assert r.status_code == 400
    assert r.headers.get("access-control-allow-origin") is None


def test_the_local_dashboard_is_still_allowed():
    r = _preflight("http://localhost:5175")
    assert r.headers.get("access-control-allow-origin") == "http://localhost:5175"
