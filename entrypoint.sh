#!/bin/sh
set -e

ROLE="${ROLE:-web}"
PORT="${PORT:-8008}"

if [ "$ROLE" = "web" ]; then
  echo "Running migrations..."
  python3 manage.py migrate --noinput
  echo "Collecting static files..."
  python3 manage.py collectstatic --noinput
  echo "Starting Uvicorn..."
  exec gunicorn core.asgi:application \
  -k uvicorn.workers.UvicornWorker \
  --workers 1 \
  --threads 1 \
  --bind 0.0.0.0:$PORT \
  --timeout 120

elif [ "$ROLE" = "worker" ]; then
  echo "Starting Celery worker..."
  exec celery -A core worker -l info
elif [ "$ROLE" = "beat" ]; then
  echo "Starting Celery beat..."
  exec celery -A core beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
else
  echo "Unknown ROLE: $ROLE"
  exit 1
fi
