#from app import app
import io
import os
from datetime import datetime, timedelta, date
from WebDaemon import app, db, hwclient
from flask import render_template, request, jsonify, redirect, make_response, Response, session, url_for, g
from WebDaemon.Settleplate import Settleplate, SettleplateForm
from WebDaemon.BarcodeParser import Decoder
from WebDaemon.ImageTools import *
from WebDaemon.Settings import settings, user_validator, SettingsForm

# set session to permanent once
@app.before_request
def make_session_permanent():
	app.before_request_funcs[None].remove(make_session_permanent)
	session.permanent = True

# Limit access and set admin flag
@app.before_request
def login_check(admin=False):
	session.modified = True

	if request.path.startswith(('/static/','/bootstrap/','/status')):
		return

	if session.get('user') is None and request.endpoint not in ['login', 'logout']:
		return redirect(url_for('login'))

	g.username = session.get("user")
	g.isAdmin = (g.username == 'admin')

	#g.testserver = settings.getboolean('general','testserver')

# default page
@app.route('/')
def index():
	return redirect(request.base_url + "list")

# Login dialog
@app.route('/login', methods=['GET', 'POST'])
def login():
	error = ''
	if request.method == 'POST':
		valid, error = user_validator(request.form['username'], request.form['password'])
		if valid:
			session['user'] = request.form['username']
			session['user_time'] = datetime.now()
			app.logger.info(f"User {session['user']} logged in")
			return redirect(url_for('index'))
		else:
			app.logger.error(f"Wrong password for user {session['user']}")
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

	#try to fetch settleplate
	sp = Settleplate.query.get(int(sp_id))
	if sp is None:
		return "Not found"

	# do user have access to change/delete this?
	# must either be admin, or creator withing 30 minutes
	age = (datetime.now()-sp.ScanDate).total_seconds() / 60
	readonly = not (g.isAdmin or (sp.Username == g.username and age < 30))

	# create form
	form = SettleplateForm(obj=sp)

	# validate form if POST
	if form.validate_on_submit() and not readonly:
		form.populate_obj(sp)
		db.session.add(sp)
		db.session.commit()
		new_url = request.base_url + "?id=%d"%sp.ID
		return redirect(new_url)

	return render_template('settleplate.html', settleplate=sp, form=form, readonly=readonly)
		

@app.route('/images/live', methods=['GET'])
def capture():
	if 'norefresh' not in request.args:
		# get parameters
		crop = request.args.get('crop')
		light = request.args.get('light')
		debug = request.args.get('debug') != None

		# turn on leds and capture image
		leds_ring = (light == 'ring' or light == 'both')
		leds_flash = (light == 'flash' or light == 'both')
		
		success, image = hwclient.capture_image()

		if success:
			# process image
			retval = False
			if crop == 'ring':
				image_cropped, retval = autocrop_ring(image)
			elif crop == 'rect':
				image_cropped, retval = autocrop_rect(image)
			elif retval == False and debug:
				image = draw_mask(image)
			if retval == True:
				image = image_cropped

			session['image'] = image
			session['image_jpeg'] = to_jpg(image)
			session['image_timestamp'] = datetime.now()
		else:
			session['image'] = None
			session['image_jpeg'] = None
			session['image_timestamp'] = None

	# check for valid image_jpeg
	if session['image_jpeg'] is None:
		return redirect("/static/settleplate.svg")
	else:
		resp = make_response(session['image_jpeg'])
		resp.headers.set('Content-Type', 'image/jpeg')
		resp.headers.set('Content-Disposition', 'inline', capture='.jpg')
		resp.headers.set("Cache-Control", "no-store")
		resp.headers.set("Expires", '0')
		resp.headers.set("Pragma", "no-cache")
		return resp
 

@app.route('/save_image', methods=['POST'])
def save_image():
	try:
		data = request.get_json()
		# todo get path from settings
		path = '/mnt/petra/Data/Colonizer'
		params = {
			'user' : session.get("user"),
			'timestamp' : session['image_timestamp'].strftime('%Y%m%d_%H%M%S'),
			'ext' : 'jpg',
			'batch_id' : data['batch']
		}
		filename = '{user}-{timestamp}-{batch_id}.{ext}'.format(**params)
		filepath = os.path.join(path, filename)
		with open(filepath,'wb') as f:
			if params['ext'] == 'png':
				img_out = to_png(session['image'])
			elif params['ext'] == 'jpg':
				img_out = session['image_jpeg']
			app.logger.info('Saving image to: %s (%d kB)'%(filename,len(img_out)/1024))
			f.write(img_out)
	except Exception as error:
		app.logger.error('Failed to write image: %s'%error)
		return jsonify({'saved':False, 'error':str(error)})
	else:
		return jsonify({'saved':True, 'filename':filename})

@app.route('/images/<int:image_id>', methods=['GET'])
def get_image(image_id):
	image_binary = Settleplate.query.get(int(image_id)).Image
	if image_binary is None:
		#return Response(status = 200)
		return redirect("/static/settleplate.svg")
	else:
		img = make_response(image_binary)
		img.headers.set('Content-Type', 'image/png')
		img.headers.set('Content-Disposition', 'attachment', filename='%s.png' % image_id)
		return img

@app.route('/list', methods=['GET', 'POST'])
def list_settleplates():
	# if get
	if request.method == 'POST' and g.isAdmin:
		selected = request.form.getlist("selected")
		for settleplate_id in selected:
			settleplate = Settleplate.query.get(int(settleplate_id))
			db.session.delete(settleplate)
		db.session.commit()

	# define search from request data
	date_from = request.args.get('from', (date.today() - timedelta(days=7)).isoformat(), str)
	date_to = request.args.get('to', (date.today()).isoformat(), str)
	batch = request.args.get('batch', "", str)
	#batch.replace('_','__') # escape wildcard

	#define query
	query = Settleplate.query
	# filter date
	try:
		# update to python > 3.7
		#a = date.fromisoformat(date_from)
		#b = date.fromisoformat(date_to)
		# fix for python 3.5
		a = date(*map(int, date_from.split('-')))
		b = date(*map(int, date_to.split('-')))
		query = query.filter(
			Settleplate.ScanDate >= datetime(a.year, a.month, a.day),
			Settleplate.ScanDate <= datetime(b.year, b.month, b.day, 23, 59, 59)
		)

	except:
		query = query.filter(
			Settleplate.ScanDate >= datetime.today() - timedelta(days=7)
		)
	# filter by batch
	if batch != "":
		query = query.filter(Settleplate.Batch.contains(batch))
	# return	results
	settleplates = query.order_by(Settleplate.ScanDate.desc()).all()
	return render_template('list.html', settleplates=settleplates, date_from=date_from, date_to=date_to, batch=batch)

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
		limit=25
		results = db.session.query(Settleplate.ScanDate, Settleplate.Barcode, Settleplate.Location).filter(Settleplate.Batch.like(batch_id)).order_by(Settleplate.ScanDate.desc()).limit(limit).all()
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
	# return sorted and max 10
	scans = filters.order_by(Settleplate.ScanDate.asc()).limit(10).all()
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
			sp.Image = session['image_jpeg']
			sp.Colonies = data['colonies'].encode('utf8')
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

@app.route('/settings', methods=['get'])
def settings():
	form = SettingsForm()
	form.populate()

	if form.validate_on_submit() and g.isAdmin:
		pass

	return render_template('settings.html', form=form)

@app.route('/status', methods=(['GET']))
def status():
	status = {}

	# check sql status
	try:
		db.session.execute('SELECT 1')
	except:
		status['sql'] = False
	else:
		status['sql'] = True

	# check camera status
	status['camera'] = hwclient.is_ready()

	# check storage status
	status['storage'] = False #os.path.ismount(settings['general']['mountpoint'])
	return jsonify(status)
