#!/bin/bash
set -e

python manage.py syncdb --migrate --noinput
exec python manage.py runserver 0.0.0.0:80
