from unittest.mock import MagicMock, patch

from django.db.utils import OperationalError


def test_liveness_probe_returns_success(client):
    response = client.get("/health/live/")

    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_readiness_probe_returns_success_when_dependencies_are_healthy(client):
    with (
        patch("core.health.connections") as connections,
        patch("core.health.redis.Redis") as redis_factory,
    ):
        redis_client = MagicMock()
        redis_factory.return_value = redis_client

        response = client.get("/health/ready/")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "checks": {"database": "ok", "redis": "ok"},
    }
    connections["default"].cursor.assert_called_once_with()
    redis_factory.assert_called_once_with(
        host="127.0.0.1",
        port=6379,
        password=None,
    )
    redis_client.ping.assert_called_once_with()


def test_readiness_probe_returns_unavailable_when_database_fails(client):
    with (
        patch("core.health.connections") as connections,
        patch("core.health.redis.Redis") as redis_factory,
    ):
        connections["default"].cursor.side_effect = OperationalError

        response = client.get("/health/ready/")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "checks": {"database": "failed", "redis": "ok"},
    }
    redis_factory.return_value.ping.assert_called_once_with()


def test_readiness_probe_returns_unavailable_when_redis_fails(client):
    with (
        patch("core.health.connections"),
        patch("core.health.redis.Redis", side_effect=ConnectionError),
    ):
        response = client.get("/health/ready/")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "checks": {"database": "ok", "redis": "failed"},
    }
