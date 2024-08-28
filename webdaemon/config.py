#from flask_wtf import FlaskForm
#from wtforms import StringField, TextAreaField, FloatField, IntegerField, validators, PasswordField, HiddenField, FieldList, FormField

# class DatabaseForm(FlaskForm):
# 	driver       = StringField('Driver', [validators.DataRequired("enter DB driver")])
# 	filepath     = StringField('Filepath')
# 	hostname     = StringField('Host')
# 	port         = IntegerField('Port')
# 	user         = StringField('Username')
# 	password     = StringField('Password')
# 	name         = StringField('DB name')
# 	table        = StringField('Table name')
# 	arg          = StringField('Extra arguments')

# class RegexForm(FlaskForm):
# 	user         = StringField('User')
# 	batch        = StringField('Batch')
# 	location     = StringField('Location')
# 	settleplate  = TextAreaField('Settleplates')

# class UserForm(FlaskForm):
# 	username     = StringField('Username')
# 	password     = PasswordField('Password')

# class SettingsForm(FlaskForm):
# 	db = FormField(DatabaseForm)
# 	regex = FormField(RegexForm)
# 	users = FieldList(FormField(UserForm), min_entries=2)
# 	def populate(self):
# 		pass