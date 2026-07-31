#!/bin/sh
set -eu

PORT="${PORT:-8000}"

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Daphne on port ${PORT}..."
exec daphne --bind 0.0.0.0 --port "${PORT}" core.asgi:application
