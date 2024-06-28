command = '/usr/local/bin/gunicorn'
pythonpath = '/app/Colonizer'
bind = 'unix:/app/Colonizer/run/colonizer.sock'
workers = 3
user = 'colonizer'
pidfile = '/app/Colonizer/run/colonizer.pid'
max_requests = 200
max_requests_jitter = 33