web: python manage.py migrate --run-syncdb && gunicorn core.wsgi --workers 2 --bind 0.0.0.0:$PORT
