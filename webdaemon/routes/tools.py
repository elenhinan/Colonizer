from flask import Blueprint, current_app, request, jsonify, session, g
from webdaemon.model import Settleplate
from webdaemon.database import db
from webdaemon.barcodeparser import Decoder
from webdaemon.status import servicemonitor

blueprint = Blueprint("tools",__name__)

@blueprint.route('/parse', methods=['POST'])
def parse_string():
	data = request.get_json()
	result = Decoder.parse_input(data)
	if result is None:
		return jsonify({})
	if 'batch' in result:
		session['batch'] = result['batch']
	if 'serial' in result:
		result['used'] = len(db.session.query(Settleplate.ScanDate).filter(Settleplate.Barcode.like(result['serial'])).all())
	return jsonify(result)

@blueprint.before_app_request
def include_status():
	g.status = servicemonitor.status