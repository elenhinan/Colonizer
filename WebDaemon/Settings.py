from os import path
from configparser import ConfigParser
#import json
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


_inifile_path = "./settleplate.ini"

settings = ConfigParser()
_defaults = {
	'db_prod': {
		'driver'      : 'SQLITE',
		'filepath'    : 'database_prod.sqlite',
		'hostname'    : 'localhost',
		'port'        : '1433',
		'user'        : 'user',
		'password'    : 'pass',
		'name'        : 'settleplate',
		'arg'         : '',
		'table'       : 'SETTLEPLATE'
	},
	'db_test': {
		'driver'      : 'SQLITE',
		'filepath'    : 'database_test.sqlite',
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
		'settleplate' : r'^(?P<serial>\d+(?P<lot>\d{11})(?P<year>\d{2})(?P<month>\d{2})(?P<day>\d{2}))$' + '\n' + r'^(?P<serial>\d+\s?(?P<lot>\d{10})(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})\w+)$'
	},
	'general': {
		'adminpwd'    : 'admin',
		'user_min'    : 4,
		'user_max'    : 8,
		'timeout'     : 300,
		'testserver'  : 'False',
		'datapath'    : ''
	},
	'users': {
		'admin'       : 'admin'
	}
}
settings.read_dict(_defaults)

if path.exists(_inifile_path):
	settings.read(_inifile_path)
else:
	with open(_inifile_path, 'w') as inifile:
		settings.write(inifile)

def user_validator(username, password):
	user_min = settings.getint('general','user_min')
	user_max = settings.getint('general','user_max')

	if username == 'admin':
		if password == settings.get('general','adminpwd'):
			return True, ''
		else:
			return False, 'Wrong password'
	elif user_min <= len(username) <= user_max:
		return True, ''
	else:
		return False, 'Invalid username'