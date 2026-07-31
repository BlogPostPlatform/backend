set shell := ["powershell.exe", "-c"]

default:
    just --list

run port="8000":
    uv run python manage.py runserver 0.0.0.0:{{port}}


migrate:
    uv run python manage.py migrate

makemigrations:
    uv run python manage.py makemigrations

worker:
    uv run celery -A core worker --pool=solo -l DEBUG

beat:
    uv run celery -A core beat -l DEBUG --scheduler django_celery_beat.schedulers:DatabaseScheduler

shell:
    uv run python manage.py shell
