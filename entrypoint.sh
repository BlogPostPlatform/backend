#!/bin/sh
set -e

ROLE="${ROLE:-web}"
PORT="${PORT:-8008}"

if [ "$ROLE" = "web" ]; then
  echo "Running migrations..."
  python3 manage.py migrate --noinput
  echo "Collecting static files..."
  python3 manage.py collectstatic --noinput
  echo "Starting Gunicorn..."
  exec gunicorn core.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers "${GUNICORN_WORKERS:-4}" \
    --threads "${GUNICORN_THREADS:-2}" \
    --timeout "${GUNICORN_TIMEOUT:-120}"
elif [ "$ROLE" = "worker" ]; then
  echo "Starting Celery worker..."
  exec celery -A core worker --pool=gevent -l info
elif [ "$ROLE" = "beat" ]; then
  echo "Starting Celery beat..."
  exec celery -A core beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
else
  echo "Unknown ROLE: $ROLE"
  exit 1
fi
