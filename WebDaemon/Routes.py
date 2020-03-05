#from app import app
import io
import os
from datetime import datetime, timedelta
from WebDaemon import app, db, ueye, leds
from flask import render_template, request, jsonify, redirect, make_response, Response, session, url_for, g
from WebDaemon.Settleplate import Settleplate, SettleplateForm
from WebDaemon.BarcodeParser import Decoder
from WebDaemon.ImageTools import autocrop_rect, autocrop_ring, to_png, to_jpg
from WebDaemon.Settings import Settings, user_validator
#from WebDaemon.CeleryTasks import add_scan_async

@app.route('/')
def index():
	return redirect(request.base_url + "list")

@app.before_request
def login_check():
	session.permanent = True
	session.modified = True

	if request.path.startswith('/static/'):
		return

	if session.get('user') is None and request.endpoint not in ['login', 'logout']:
		return redirect(url_for('login'))

	g.username = session.get("user")

@app.route('/login', methods=['GET', 'POST'])
def login():
	error = ''
	if request.method == 'POST':
		valid, error = user_validator(request.form['username'], request.form['password'])
		if valid:
			session['user'] = request.form['username']
			session['user_time'] = datetime.now()
			return redirect(url_for('index'))
		else:
			session['user'] = None
	
	return render_template('login.html', error=error)

@app.route('/logout', methods=['GET'])
def logout():
	session['user'] = None
	return redirect(url_for('login'))

@app.route('/register', methods=['GET'])
def register():
	return render_template('register.html')

@app.route('/scan', methods=['GET', 'POST'])
def scan_settleplate():
	# create
	sp = Settleplate()
	
	# create form
	form = SettleplateForm(obj=sp)
	
	# # validate form if POST
	if request.method == 'POST' and form.validate():
	   form.populate_obj(sp)
	   db.session.add(sp)
	   db.session.commit()
	   new_url = request.base_url + "?id=%d"%sp.id
	   return redirect(new_url)

	return render_template('scan.html', settleplate=sp, form=form)


@app.route('/settleplate', methods=['GET', 'POST'])
def show_settleplate():
	sp_id = request.args.get('id')

	# check if existing study requested
	if (sp_id == "new") or (sp_id is None):
		sp = Settleplate()
	else:
		sp = Settleplate.query.get(int(sp_id))
	# fetch if in DB

	# create form
	form = SettleplateForm(obj=sp)

	# validate form if POST
	if form.validate_on_submit():
	   form.populate_obj(sp)
	   db.session.add(sp)
	   db.session.commit()
	   new_url = request.base_url + "?id=%d"%sp.ID
	   return redirect(new_url)

	if sp is not None:
		return render_template('settleplate.html', settleplate=sp, form=form)
	else:
		return "Not found"

@app.route('/images/live', methods=['GET'])
def capture():
	if 'norefresh' in request.args:
		image = session['image']
	else:
		# get parameters
		crop = request.args.get('crop')
		light = request.args.get('light')
		
		# turn on leds and capture image
		leds_ring = (light == 'ring' or light == 'both')
		leds_flash = (light == 'flash' or light == 'both')
		
		leds.Flash(leds_flash)
		leds.Ring(leds_ring)
		image = ueye.capture()
		leds.Flash(False)
		leds.Ring(False)

		# process image
		retval = False
		if crop == 'ring':
			image_cropped, retval = autocrop_ring(image)
		elif crop == 'rect':
			image_cropped, retval = autocrop_rect(image)
		if retval == True:
			image = image_cropped

		session['image'] = image
		session['image_timestamp'] = datetime.now()

	image_jpeg = to_jpg(image)
	resp = make_response(image_jpeg)
	resp.headers.set('Content-Type', 'image/jpeg')
	resp.headers.set('Content-Disposition', 'attachment', capture='.jpg')
	resp.headers.set("Cache-Control", "no-cache, no-store, must-revalidate, public, max-age=0")
	resp.headers.set("Expires", '0')
	resp.headers.set("Pragma", "no-cache")
	return resp
  

@app.route('/save_image', methods=['POST'])
def save_image():
	ext = '.png'
	path = '/mnt/petra/Data/Colonizer'
	filename = session['image_timestamp'].strftime('%Y%m%d_%H%M%S') + '.png'
	
	filepath = os.path.join(path, filename)
	try:
		with open(filepath,'wb') as f:
			img_png = to_png(session['image'])
			f.write(img_png)
	except:
		app.logger.error('Failed to write image')
		return jsonify({'saved':False})
	else:
		return jsonify({'saved':True, 'filename':filename})

@app.route('/images/<int:image_id>.png', methods=['GET'])
def get_image(image_id):
	image_binary = Settleplate.query.get(int(image_id)).Image
	if image_binary is None:
		return Response(status = 200)
	else:
		img = make_response(image_binary)
		img.headers.set('Content-Type', 'image/png')
		img.headers.set('Content-Disposition', 'attachment', filename='%s.png' % image_id)
		return img

@app.route('/list', methods=['GET', 'POST'])
def list_settleplates():
	# if get
	if request.method == 'POST':
		selected = request.form.getlist("selected")
		for study_id in selected:
			study = Study.query.get(int(study_id))
			db.session.delete(study)
		db.session.commit()
	lastweek = datetime.today() - timedelta(days=7)
	settleplates = Settleplate.query.filter(Settleplate.ScanDate >= lastweek).order_by(Settleplate.ScanDate.desc()).all()
	return render_template('list.html', settleplates=settleplates)

@app.route('/camera', methods=['get'])
def camera():
	return render_template('camera.html')

@app.route('/parse', methods=['POST'])
def parse_string():
	data = request.get_json()
	result = Decoder.parse_input(data)
	if result is None:
		return jsonify({})
	if 'user' in result:
	   session['user'] = result['user']
	if 'batch' in result:
	   session['batch'] = result['batch']
	if 'serial' in result:
		result['used'] = len(db.session.query(Settleplate.ScanDate).filter(Settleplate.Barcode.like(result['serial'])).all())
	return jsonify(result)

@app.route('/batch_bydate', methods=(['POST']))
def get_batch_date():
	data = request.get_json()
	batch_id = data['batch']
	if len(batch_id):
		results = db.session.query(Settleplate.ScanDate, Settleplate.Lot_no, Settleplate.Location).filter(Settleplate.Batch.like(batch_id)).order_by(Settleplate.ScanDate.desc()).all()
		if len(results):
			response = [r._asdict() for r in results]
			return jsonify(response)
	return ""

@app.route('/db/plate_info', methods=(['POST']))
def plate_info():
	data = request.get_json()
	barcode = data['barcode']
	if not len(barcode):
		return jsonify({'error':'missing serial'})
	
	# query for registration
	query = db.session.query(Settleplate.ScanDate, Settleplate.Location, Settleplate.Batch)
	filters = query.filter(Settleplate.Barcode.like(barcode), Settleplate.Counts == -1)
	try:
		plateinfo = filters.one()
	except:
		return jsonify({'error':'serial not in db'})

	# query for scans
	query = db.session.query(Settleplate.ID, Settleplate.ScanDate, Settleplate.Counts)
	filters = query.filter(Settleplate.Barcode.like(barcode), Settleplate.Counts >= 0)
	scans = filters.order_by(Settleplate.ScanDate.asc()).all()
	timepoints = []
	for scan in scans:
		dt = round((scan.ScanDate - plateinfo.ScanDate).total_seconds() / 3600) # convert to hours
		timepoints.append({
			'ID' : scan.ID,
			'Counts' : scan.Counts,
			'dT' : dt
		})

	# return plate info and scan times
	response = plateinfo._asdict()
	response['Timepoints'] = timepoints
	return jsonify(response)

@app.route('/scan_add_new', methods=['POST'])
def scan_add_new():
	data = request.get_json()
	sp = Settleplate()
	sp.Username = session['user']
	sp.ScanDate = session['image_timestamp']
	sp.Barcode = data['barcode']
	sp.Counts = data['counts']
	#print(add_scan_async(sp, session['image']))

	return jsonify({'committed':True})

@app.route('/scan_add', methods=['POST'])
def scan_add():
	data = request.get_json()
	if "barcode" in data:
		# query for registration
		query = db.session.query(Settleplate.Location, Settleplate.Batch, Settleplate.Lot_no, Settleplate.ScanDate, Settleplate.Expires, Settleplate.Lot_no)
		filters = query.filter(Settleplate.Barcode.like(data['barcode']), Settleplate.Counts == -1)
		plateinfo = filters.one()
		if len(plateinfo):
			sp = Settleplate()
			sp.Username = session['user']
			sp.ScanDate = session['image_timestamp']
			sp.Barcode = data['barcode']
			sp.Lot_no = plateinfo.Lot_no
			sp.Expires = plateinfo.Expires
			sp.Counts = data['counts']
			sp.Location = plateinfo.Location
			sp.Batch = plateinfo.Batch
			sp.Image = to_png(session['image'])
			try:
				db.session.add(sp)
				db.session.commit()
			except Exception as e:
				app.logger.error('Failed to write to DB: %s'%str(e))
				return jsonify({'committed':False})
			else:
				dt = round((sp.ScanDate - plateinfo.ScanDate).total_seconds() / 3600) # convert to hours
				app.logger.info('Saved %s to DB with %d counts'%(sp.Barcode, sp.Counts))
				return jsonify({'committed':True, 'Counts': sp.Counts, 'ID': sp.ID, 'dT': dt })
		else:
			return jsonify({'committed':False})


@app.route('/register_new', methods=['POST'])
def commit_new():
	data = request.get_json()
	data.update(Decoder.parse_input(data['serial'])) # parse serial and add result to data dictionary
		
	required = ['user', 'batch', 'serial', 'location']
	if all([k in data for k in required]):
		new_sp = Settleplate()
		new_sp.Username = data['user']
		new_sp.Batch = data['batch']
		new_sp.Barcode = data['serial']
		new_sp.Location = data['location']
		if 'lot' in data:
			new_sp.Lot_no = data['lot']
		if 'expire' in data:
			new_sp.Expires = data['expire']
		new_sp.Counts = -1
		db.session.add(new_sp)
		db.session.commit()

	return jsonify({'commited':True})