#!/usr/bin/env python3
import os
import pyodbc
import datetime
from flask import Flask
from flask_bootstrap import Bootstrap4
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from WebDaemon.Settings import settings
import HWlayer.client as hwclient

# create flask app
app = Flask(__name__)

# config
app.config.update(
	SECRET_KEY = os.urandom(32),
	SQLALCHEMY_TRACK_MODIFICATIONS = False,
	BOOTSTRAP_SERVE_LOCAL = True
)

# Enable Bootstrap extension
app.logger.info('Enabling Bootstrap4...')
bootstrap = Bootstrap4(app)


# Enable session
app.logger.info('Setting up local session storage...')
app.config.update(
	SESSION_TYPE = 'filesystem'
	#SESSION_COOKIE_SAMESITE = "Strict",
	#PERMANENT_SESSION_LIFETIME = datetime.timedelta(seconds=settings['general']['timeout'])
)
Session(app)

# initialize database
app.logger.info('Connecting to SQL database...')
config = 'db_test'
sql_info = settings['dbs'][settings['general']['database']]
if (sql_info['driver'] == "SQLITE"):
	app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{filepath}'.format(**sql_info)
elif (sql_info['driver'] in ["ODBC", "FreeTDS"]):
	app.config['SQLALCHEMY_DATABASE_URI'] = 'mssql+pyodbc://{user}:{password}@{host}:{port}/{dbname}?driver={driver}'.format(**sql_info)
try:
	db = SQLAlchemy(app)
except:
	app.logger.error("Could not initialize database")

# initialize camera
app.logger.info('Connecting to RPI HW server...')
hwclient.start_socket('localhost')

app.logger.info('Setting up routes...')
from WebDaemon import Routes
