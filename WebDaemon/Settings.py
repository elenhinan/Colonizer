from os import path
from configparser import ConfigParser
#import json
#from flask_wtf import FlaskForm
#from wtforms import StringField, DateTimeField, DateField, FloatField, IntegerField, validators, HiddenField, FieldList

# class SettingsForm(FlaskForm):
#   driver    = StringField('Driver', [validators.Required("Please enter study name")])
#   ScanDate     = DateTimeField('Study Date')
#   Barcode      = StringField('Barcode', [validators.Required("Settleplate barcode needed")])
#   Lot_no       = StringField('Lot number')
#   Expires      = DateField('Expire Date')
#   Counts       = IntegerField('Counts')
#   Location     = StringField('Location', [validators.Required("Location needed")] )
#   Batch        = StringField('Batch', [validators.Required("Batch# needed")])

_inifile_path = "./settleplate.ini"

Settings = ConfigParser()
_defaults = {
	'db': {
		'driver'      : 'ODBC',
		'filepath'    : 'database.sqlite',
		'hostname'    : 'localhost',
		'port'        : '1433',
		'user'        : 'user',
		'password'    : 'pass',
		'name'        : 'settleplate',
		'arg'         : '',
		'table'       : 'SETTLEPLATE'
	},
	'regex': {
		'user'        : r'^user:(?P<user>.+)$',
		'batch'       : r'^(?P<batch>[A-Za-z]{3,5}\d{7})$',
		'location'    : r'^loc:(?P<location>.+)$',
		'settleplate' : r'^(?P<serial>\d+(?P<lot>\d{11})(?P<year>\d{2})(?P<month>\d{2})(?P<day>\d{2}))$' + '\n' + r'^(?P<serial>\d+ (?P<lot>\d{10})(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})\w+)$'
	},
	'general': {
		'adminpwd'    : 'pet4life',
		'user_min'    : 4,
		'user_max'    : 8,
		'timeout'     : 300
	}
}
Settings.read_dict(_defaults)

if path.exists(_inifile_path):
	Settings.read(_inifile_path)
else:
	with open(_inifile_path, 'w') as inifile:
		Settings.write(inifile)

def user_validator(username, password):
	user_min = int(Settings['general']['user_min'])
	user_max = int(Settings['general']['user_max'])

	if username == 'admin':
		if password == Settings['general']['adminpwd']:
			return True, ''
		else:
			return False, 'Wrong password'
	elif user_min <= len(username) <= user_max:
		return True, ''
	else:
		return False, 'Invalid username'