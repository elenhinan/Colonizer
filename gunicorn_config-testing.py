command = '/usr/local/bin/gunicorn'
pythonpath = '/app/Colonizer-testing'
bind = 'unix:/app/Colonizer-testing/run/colonizer.sock'
workers = 4
user = 'colonizer'
pidfile = '/app/Colonizer-testing/run/colonizer.pid'
max_requests = 200
max_requests_jitter = 50