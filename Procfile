web: gunicorn wsgi:app --timeout 60 --workers 2 --max-requests 1000
release: flask db upgrade && flask seed-datos-iniciales
