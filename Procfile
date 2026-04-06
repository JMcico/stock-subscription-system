web: cd backend && python manage.py migrate && gunicorn core.wsgi
worker: cd backend && python manage.py qcluster
