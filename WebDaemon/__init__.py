#!/usr/bin/env python3
import os
import pyodbc
#import urllib
#import flask_login
import datetime
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_fontawesome import FontAwesome
from flask_session import Session
from WebDaemon.Settings import settings
from WebDaemon.CameraUeye import CameraUeye
from WebDaemon.Illumination import Illumination
#from WebDaemon.CeleryTasks import CeleryWorker

# create flask app
app = Flask(__name__)

# config
app.config.update(
	SECRET_KEY = os.urandom(32),
	SQLALCHEMY_TRACK_MODIFICATIONS = False,
	BOOTSTRAP_SERVE_LOCAL = True
)

# Setup celery
app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379',
    CELERY_RESULT_BACKEND='redis://localhost:6379'
)
#celery = CeleryWorker(app)

# Install Bootstrap extension
Bootstrap(app)

# Install Font Awesome
FontAwesome(app)

# Install session
app.config.update(
	SESSION_TYPE = 'filesystem',
	SESSION_COOKIE_SAMESITE = "Strict",
	PERMANENT_SESSION_LIFETIME = datetime.timedelta(seconds=settings.getint('general','timeout'))
)
Session(app)

# create database
sql_info = {
	'filepath' : settings['db_prod']['filepath'],
	'driver'   : settings['db_prod']['driver'],
	'host'     : settings['db_prod']['hostname'],
	'port'     : settings['db_prod']['port'],
	'user'     : settings['db_prod']['user'],
	'password' : settings['db_prod']['password'],
	'dbname'   : settings['db_prod']['name'],
	'args'     : settings['db_prod']['arg'],
	'table'    : settings['db_prod']['table']
}
if (sql_info['driver'] == "SQLITE"):
	app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{filepath}'.format(**sql_info)
elif (sql_info['driver'] in ["ODBC", "FreeTDS"]):
	app.config['SQLALCHEMY_DATABASE_URI'] = 'mssql+pyodbc://{user}:{password}@{host}:{port}/{dbname}?driver={driver}'.format(**sql_info)

db = SQLAlchemy(app)
db.init_app(app)
# update database model objects to reflect database table
# db.reflect(app=app)
db.create_all()

# initialize camera
ueye = CameraUeye(app)

# initialize leds
leds = Illumination(app)

from WebDaemon import Routes
