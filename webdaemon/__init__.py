#!/usr/bin/env python3
import os
import pyodbc
import datetime
from flask import Flask
from flask_session import Session
from webdaemon.settings import settings
from webdaemon.status import servicemonitor
from webdaemon.database import init_database
import hwlayer.client as hwclient

# create flask app
app = Flask(__name__)

# config
app.config.update(
	SECRET_KEY = os.urandom(32),
	SQLALCHEMY_TRACK_MODIFICATIONS = False
)

# Enable session
app.logger.info('Setting up local session storage...')
app.config.update(
	SESSION_TYPE = 'filesystem',
	SESSION_COOKIE_SAMESITE = "Strict"
	#PERMANENT_SESSION_LIFETIME = datetime.timedelta(seconds=settings['general']['timeout'])
)
Session(app)

# initialize database
init_database(app)

# initialize camera
app.logger.info('Connecting to RPI HW server...')
hwclient.start_socket('localhost')

app.logger.info('Setting up routes...')

# init service checker
servicemonitor.start()

from webdaemon import routes
