from os import path
import json
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, IntegerField, validators, PasswordField, HiddenField, FieldList, FormField

class DatabaseForm(FlaskForm):
	driver       = StringField('Driver', [validators.DataRequired("enter DB driver")])
	filepath     = StringField('Filepath')
	hostname     = StringField('Host')
	port         = IntegerField('Port')
	user         = StringField('Username')
	password     = StringField('Password')
	name         = StringField('DB name')
	table        = StringField('Table name')
	arg          = StringField('Extra arguments')

class RegexForm(FlaskForm):
	user         = StringField('User')
	batch        = StringField('Batch')
	location     = StringField('Location')
	settleplate  = TextAreaField('Settleplates')

class UserForm(FlaskForm):
	username     = StringField('Username')
	password     = PasswordField('Password')

class SettingsForm(FlaskForm):
	db = FormField(DatabaseForm)
	regex = FormField(RegexForm)
	users = FieldList(FormField(UserForm), min_entries=2)
	def populate(self):
		pass

_jsonfile_path = "./config.json"

#settings = ConfigParser()
_defaults = {
	'dbs': {
		'Production':
		{
			'driver'      : 'SQLITE',
			'hostname'    : 'localhost',
			'port'        : 1433,
			'user'        : 'user',
			'password'    : 'pass',
			'name'        : 'settleplate',
			'arg'         : '',
			'table'       : 'SETTLEPLATE'
		},
		'Test' : {
			'driver'      : 'SQLITE',
			'filepath'    : 'database.sqlite',
			'name'        : 'settleplate',
			'table'       : 'SETTLEPLATE'
		}
	},
	'regex': {
		'user'        : [r'^user:(?P<user>.+)$'],
		'batch'       : [r'^(?P<batch>[A-Za-z]{3,5}\d{7})$'],
		'location'    : [r'^loc:(?P<location>.+)$'],
		'settleplate' : [
			r'^(?P<serial>\d+(?P<lot>\d{11})(?P<year>\d{2})(?P<month>\d{2})(?P<day>\d{2}))$',
			r'^(?P<serial>\d+\s?(?P<lot>\d{10})(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})\w+)$'
		]
	},
	'general': {
		'adminpwd'    : 'admin',
		'user_min'    : 4,
		'user_max'    : 8,
		'timeout'     : 300,
		'database'    : 'Test',
		'mountpoint'  : '/mnt/data'
	},
	'users': {
		'admin'       : 'admin'
	}
}

try:
	with open(_jsonfile_path,'r') as f:
		settings = json.load(f)
except:
	print(f"Error loading settings from {_jsonfile_path}, using defaults")
	settings = _defaults.copy()
	with open(_jsonfile_path,'w') as f:
		json.dump(settings,f, indent=3)

def user_validator(username, password):
	user_min = settings['general']['user_min']
	user_max = settings['general']['user_max']

	if username == 'admin':
		if password == settings['general']['adminpwd']:
			return True, ''
		else:
			return False, 'Wrong password'
	elif user_min <= len(username) <= user_max:
		return True, ''
	else:
		return False, 'Invalid username'