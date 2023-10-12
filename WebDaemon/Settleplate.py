from datetime import datetime
from WebDaemon import db
from sqlalchemy.orm import deferred
from flask_wtf import FlaskForm
from wtforms import StringField, DateTimeField, DateField, FloatField, IntegerField, validators, HiddenField, FieldList

# using sqlacodegen db_uri

class Settleplate(db.Model):
	__tablename__ = 'SETTLEPLATE'
	ID = db.Column(db.Integer, primary_key=True)
	Username = db.Column(db.TEXT(32))
	ScanDate = db.Column(db.DateTime)
	Barcode = db.Column(db.TEXT(128))
	Lot_no = db.Column(db.TEXT(128))
	Expires = db.Column(db.Date)
	Counts = db.Column(db.Integer)
	Version = db.Column(db.TEXT(32))
	Location = db.Column(db.TEXT(32))
	Batch = db.Column(db.TEXT(128))
	# deferred so only loaded when accessed, not when queried
	Image = deferred(db.Column(db.LargeBinary))
	Colonies = db.Column(db.LargeBinary)
	Exported = db.Column(db.BINARY(1))

	def __init__(self, **kwargs):
			super(Settleplate, self,).__init__(**kwargs)
			self.ScanDate = datetime.now()
			self.Exported = False
			self.Version = 'WebApp 1.0'

	def __repr__(self):
		return '<Settleplate %r>' % self.ID

class SettleplateForm(FlaskForm):
	Username = StringField('Name', [validators.DataRequired("Please enter study name")])
	ScanDate = DateTimeField('Study Date')
	Barcode = StringField('Barcode', [validators.DataRequired("Settleplate barcode needed")])
	Lot_no = StringField('Lot number')
	Expires = DateField('Expire Date')
	Counts = IntegerField('Counts')
	Location = StringField('Location', [validators.DataRequired("Location needed")])
	Batch = StringField('Batch', [validators.DataRequired("Batch# needed")])
	Colonies = HiddenField('Colonies')

	def validate_Colonies(form, field):
		if type(field.data) is str:
			field.data = field.data.encode('utf8')
		return type(field.data) is bytes

db.create_all()