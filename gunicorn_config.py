import os
path=os.getcwd()
command = f'{path}/venv/bin/gunicorn'
pythonpath = f'{path}'
bind = f'unix:{path}/run/colonizer.sock'
workers = 4
user = 'colonizer'
pidfile = f'{path}/run/colonizer.pid'
max_requests = 200
max_requests_jitter = 50