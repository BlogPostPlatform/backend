#!/bin/sh
set -eu

echo "Starting Celery worker..."
exec celery -A core worker --loglevel=info
