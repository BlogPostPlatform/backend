import logging
import re
import sys
from urllib.parse import urlsplit

HEALTH_CHECK_PATH_PREFIX = "/health/"

_HTTP_METHODS = {
    "CONNECT",
    "DELETE",
    "GET",
    "HEAD",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
    "TRACE",
}
_REQUEST_LINE_RE = re.compile(
    r"\b(?:CONNECT|DELETE|GET|HEAD|OPTIONS|PATCH|POST|PUT|TRACE)\s+(?P<path>\S+)\s+HTTP/"
)
_REQUEST_STATUS_RE = re.compile(
    r"\b(?:CONNECT|DELETE|GET|HEAD|OPTIONS|PATCH|POST|PUT|TRACE)\s+\S+\s+"
    r"HTTP/\d(?:\.\d)?\"?\s+(?P<status>[1-5]\d{2})\b"
)


def is_health_check_path(path):
    return isinstance(path, str) and path.startswith(HEALTH_CHECK_PATH_PREFIX)


class SuccessfulHealthCheckAccessLogFilter(logging.Filter):
    """Drop only successful health check access log records."""

    def filter(self, record):
        path = _record_path(record)
        status_code = _record_status_code(record)

        if is_health_check_path(path) and status_code == 200:
            return False

        return True


class HealthCheckAccessLogGenerator:
    def __init__(self, stream):
        from daphne.access import AccessLogGenerator

        self.access_log_generator = AccessLogGenerator(stream)

    def __call__(self, protocol, action, details):
        if _is_successful_health_check_details(protocol, action, details):
            return

        self.access_log_generator(protocol, action, details)


def install_daphne_health_check_access_log_filter():
    daphne_cli = sys.modules.get("daphne.cli")
    if daphne_cli is None:
        return

    if getattr(daphne_cli, "AccessLogGenerator", None) is HealthCheckAccessLogGenerator:
        return

    daphne_cli.AccessLogGenerator = HealthCheckAccessLogGenerator


def _record_path(record):
    request = getattr(record, "request", None)
    path = getattr(request, "path", None) or getattr(request, "path_info", None)
    if path:
        return _normalize_path(path)

    args = getattr(record, "args", None)
    path = _path_from_args(args)
    if path:
        return path

    try:
        message = record.getMessage()
    except Exception:
        return None

    match = _REQUEST_LINE_RE.search(message)
    if match:
        return _normalize_path(match.group("path"))

    return None


def _record_status_code(record):
    status_code = getattr(record, "status_code", None)
    if status_code is None:
        status_code = _status_code_from_args(getattr(record, "args", None))
    if status_code is None:
        try:
            status_code = _status_code_from_message(record.getMessage())
        except Exception:
            return None

    try:
        return int(status_code)
    except (TypeError, ValueError):
        return None


def _path_from_args(args):
    if isinstance(args, dict):
        path = args.get("path")
        if path:
            return _normalize_path(path)

        for value in args.values():
            path = _path_from_request_line(value)
            if path:
                return path
        return None

    if not isinstance(args, (list, tuple)):
        return None

    for value in args:
        path = _path_from_request_line(value)
        if path:
            return path

    return None


def _path_from_request_line(value):
    if not isinstance(value, str):
        return None

    parts = value.split()
    if len(parts) >= 2 and parts[0] in _HTTP_METHODS:
        return _normalize_path(parts[1])

    return None


def _status_code_from_args(args):
    if isinstance(args, dict):
        for key in ("status_code", "status"):
            status_code = _status_code_from_value(args.get(key))
            if status_code is not None:
                return status_code

        candidates = args.values()
    elif isinstance(args, (list, tuple)):
        candidates = args
    else:
        return None

    for value in candidates:
        status_code = _status_code_from_value(value)
        if status_code is not None:
            return status_code

    return None


def _status_code_from_message(message):
    match = _REQUEST_STATUS_RE.search(message)
    if match:
        return match.group("status")

    return None


def _status_code_from_value(value):
    if isinstance(value, int):
        return value if 100 <= value <= 599 else None

    if isinstance(value, str) and value.isdigit() and len(value) == 3:
        return value

    return None


def _is_successful_health_check_details(protocol, action, details):
    if protocol != "http" or action != "complete" or not isinstance(details, dict):
        return False

    return (
        is_health_check_path(_normalize_path(details.get("path")))
        and _status_code_from_value(details.get("status")) == 200
    )


def _normalize_path(path):
    if isinstance(path, bytes):
        path = path.decode(errors="ignore")

    if not isinstance(path, str):
        return None

    return urlsplit(path).path
