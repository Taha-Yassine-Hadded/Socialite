#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# Create superuser if credentials are provided
if [[ $DJANGO_SUPERUSER_USERNAME && $DJANGO_SUPERUSER_PASSWORD && $DJANGO_SUPERUSER_EMAIL ]]; then
    python manage.py createsuperuser --noinput || true
fi
