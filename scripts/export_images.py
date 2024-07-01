#!/usr/bin/env python3
import pyodbc
import sqlalchemy as db
from os import path
from sqlalchemy.orm import Session
from sqlalchemy.ext.automap import automap_base
from configparser import ConfigParser
from hashlib import md5

# settings
outpath="/mnt/petra/Data/Colonizer/eksport"
_inifile_path = "./settleplate.ini"
settings = ConfigParser()
settings.read(_inifile_path)
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
        db_uri =  'sqlite:///{filepath}'.format(**sql_info)
elif (sql_info['driver'] in ["ODBC", "FreeTDS"]):
        db_uri = 'mssql+pyodbc://{user}:{password}@{host}:{port}/{dbname}?driver={driver}'.format(**sql_info)

engine = db.create_engine(db_uri)
connection = engine.connect()
session = Session(engine)
base = automap_base()
base.prepare(engine, reflect=True)
SettlePlate = base.classes.SETTLEPLATE

# start querying
query = session.query(SettlePlate.ID, SettlePlate.Barcode, SettlePlate.ScanDate, SettlePlate.Counts).filter(SettlePlate.Counts >= '0')
results = query.all()
for i,row in zip(range(len(results)),results):
	query_t0 = session.query(SettlePlate.ScanDate).filter(db.and_(SettlePlate.Barcode.like(row.Barcode), SettlePlate.Counts == '-1'))
	age = round( (row.ScanDate - query_t0.one().ScanDate).total_seconds() / (60*60) )
	name = md5(row.Barcode.encode()).hexdigest()
	counts = row.Counts
	filename = "{}-{}-{}.jpg".format(name,age,counts)
	imagedata = session.query(SettlePlate.Image).filter(SettlePlate.ID == row.ID).one().Image
	with open(path.join(outpath,filename), 'wb') as f:
		f.write(imagedata)
		print("{}/{} saved: {}".format(i,1,len(results),filename))
