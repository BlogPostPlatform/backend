#!/bin/sh
set -e

# Wait for database to be ready (if using Postgres/MySQL)
# until nc -z db 5432; do
#   echo "Waiting for database..."
#   sleep 2
# done

echo "Running migrations..."
python3 manage.py migrate --noinput

echo "Collecting static files..."
python3 manage.py collectstatic --noinput

echo "Starting Gunicorn..."
exec gunicorn core.wsgi:application \
    --bind 0.0.0.0:8006 \
    --workers 4 \
    --threads 2 \
    --timeout 120

#echo "Starting Django server..."
#exec python3 manage.py runserver 0.0.0.0:8006

#echo "Starting Daphne..."
#exec daphne -b 0.0.0.0 -p 8006 core.wsgi:application
