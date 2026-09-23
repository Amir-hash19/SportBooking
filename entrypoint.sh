#!/bin/sh
python manage.py migrate --noinput
python manage.py collectstatic --noinput
exec gunicorn backend.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 9 \
    --threads 2 \
    --worker-class gthread \
    --timeout 60