#!/bin/sh
set -eu

echo "Starting Celery beat..."
exec celery -A core beat --loglevel=info \
  --scheduler django_celery_beat.schedulers:DatabaseScheduler \
  --pidfile=/tmp/celerybeat.pid
