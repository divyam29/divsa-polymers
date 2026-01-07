import os

workers = int(os.environ.get('GUNICORN_WORKERS', '2'))
threads = int(os.environ.get('GUNICORN_THREADS', '4'))
bind = os.environ.get('GUNICORN_BIND', '0.0.0.0:8000')
timeout = 120
worker_class = 'gthread'
accesslog = '-'
errorlog = '-'
loglevel = 'info'
