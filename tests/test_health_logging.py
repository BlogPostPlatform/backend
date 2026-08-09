import sys
from io import StringIO
from types import SimpleNamespace

from core.logging import (
    HealthCheckAccessLogGenerator,
    install_daphne_health_check_access_log_filter,
)


def _http_details(path, status):
    return {
        "client": "127.0.0.1:12345",
        "method": "GET",
        "path": path,
        "status": status,
        "size": 64,
    }


def test_daphne_access_log_suppresses_successful_health_checks():
    stream = StringIO()
    access_logger = HealthCheckAccessLogGenerator(stream)

    access_logger("http", "complete", _http_details("/health/ready/", 200))

    assert stream.getvalue() == ""


def test_daphne_access_log_keeps_failed_health_checks():
    stream = StringIO()
    access_logger = HealthCheckAccessLogGenerator(stream)

    access_logger("http", "complete", _http_details("/health/ready/", 503))

    assert '"GET /health/ready/" 503 64' in stream.getvalue()


def test_daphne_access_log_keeps_successful_application_requests():
    stream = StringIO()
    access_logger = HealthCheckAccessLogGenerator(stream)

    access_logger("http", "complete", _http_details("/api/posts/", 200))

    assert '"GET /api/posts/" 200 64' in stream.getvalue()


def test_installer_replaces_daphne_access_log_generator(monkeypatch):
    daphne_cli = SimpleNamespace(AccessLogGenerator=object())
    monkeypatch.setitem(sys.modules, "daphne.cli", daphne_cli)

    install_daphne_health_check_access_log_filter()

    assert daphne_cli.AccessLogGenerator is HealthCheckAccessLogGenerator
