#!/bin/bash
find /var/flaskapp/colonizer/flask_session -mtime +1 -exec rm -f {} \;
