import os
from datetime import datetime, timedelta, date
from webdaemon import app
from flask import render_template, request, jsonify, redirect, make_response, Response, session, url_for, g, abort
import hwlayer.client
from webdaemon.model import Settleplate, SettleplateForm
from webdaemon.database import db
from webdaemon.barcodeparser import Decoder
from webdaemon.imagetools import *
from settings import settings, user_validator #, SettingsForm
from webdaemon.status import servicemonitor

# set session to permanent once
#@app.before_request
#def make_session_permanent():
#	app.before_request_funcs[None].remove(make_session_permanent)
#	session.permanent = True

# Limit access and set admin flag
@app.before_request
def login_check(admin=False):
	session.modified = True

	if request.path.startswith(('/static/','/status')):
		return

	if session.get('user') is None and request.endpoint not in ['login', 'logout']:
		return redirect(url_for('login'))

	g.username = session.get("user")
	g.isAdmin = (g.username == 'admin')

	#g.testserver = settings.getboolean('general','testserver')

# default page
@app.route('/')
def index():
	return redirect(url_for('list_settleplates'))

# Login dialog
@app.route('/login', methods=['GET', 'POST'])
def login():
	error = ''
	if request.method == 'POST':
		username = request.form['username']
		password = request.form['password']
		valid, error = user_validator(username, password)
		if valid:
			session['user'] = username
			session['user_time'] = datetime.now()
			app.logger.info(f"User {session['user']} logged in")
			return redirect(url_for('index'))
		else:
			app.logger.error(f"Wrong password for user {username}")
			session['user'] = None
	return render_template('login.html', error=error)

@app.route('/logout', methods=['GET'])
def logout():
	session['user'] = None
	return redirect(url_for('login'))

@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404

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

	return render_template('scan.html', settleplate=sp, form=form, autocount=settings['general']['autocount'])


@app.route('/settleplate', methods=['GET', 'POST'])
def show_settleplate():
	sp_id = request.args.get('id')

	#try to fetch settleplate
	sp = Settleplate.query.get(int(sp_id))
	if sp is None:
		abort(404)

	# do user have access to change/delete this?
	# must either be admin, or creator withing 30 minutes
	age = (datetime.now()-sp.ScanDate).total_seconds() / 60
	readonly = not (g.isAdmin or (sp.Username == g.username and age < 30))

	# create form
	form = SettleplateForm(obj=sp)

	# validate form if POST
	action = request.form.get('send', None)
	if action == "update" and not readonly:
		if form.validate_on_submit():
			form.populate_obj(sp)
			db.session.add(sp)
			db.session.commit()
			app.logger.info(f"Updating settleplate : {sp.id}")
			new_url = request.base_url + "?id=%d"%sp.ID
			return redirect(new_url)
	elif action == "delete" and not readonly:
		db.session.delete(sp)
		db.session.commit()
		app.logger.info(f"Deleting settleplate : {sp_id}")
		return redirect(url_for('list_settleplates'))

	return render_template('settleplate.html', settleplate=sp, form=form, readonly=readonly)
		

@app.route('/images/live', methods=['GET'])
def capture():
	# get parameters
	mode = request.args.get('mode')

	capture_settings = {}
	capture_settings.update(settings['camera']['default'])

	if mode in settings['camera'].keys():
		capture_settings.update(settings['camera'][mode])

	# request image
	success, image = hwlayer.client.capture_image(capture_settings)

	if success:
		# process image
		if capture_settings['autocrop'] == 'ring':
			image = autocrop_ring(image)
		elif capture_settings['autocrop'] == 'rect':
			image = autocrop_rect(image)
		elif capture_settings['mask']:
			image = mask_image(image)
		elif capture_settings['drawmask']:
			image = draw_mask(image)

		#session['image'] = image
		session['image_jpeg'] = to_jpg(image)
		session['image_timestamp'] = datetime.now()
	else:
		#session['image'] = None
		session['image_jpeg'] = None
		session['image_timestamp'] = None

	# check for valid image_jpeg
	if session['image_jpeg'] is None:
		return redirect("/static/settleplate.svg")
	else:
		resp = make_response(session['image_jpeg'])
		resp.headers.set('Content-Type', 'image/jpeg')
		#resp.headers.set('Content-Disposition', 'inline', capture='.jpg')
		resp.cache_control.no_cache = True
		resp.cache_control.must_revalidate = True
		resp.cache_control.max_age = 5
		resp.last_modified = session['image_timestamp']
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
			'batch_id' : data['batch']
		}
		filename = '{user}-{timestamp}-{batch_id}.jpg'.format(**params)
		filepath = os.path.join(path, filename)
		with open(filepath,'wb') as f:
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
	sp = Settleplate.query.get(int(image_id))
	if sp is None:
		return redirect("/static/settleplate.svg")
	elif sp.Image is None:
		return redirect("/static/settleplate.svg")
	else:
		img = make_response(sp.Image)
		img.headers.set('Content-Type', 'image/jpg')
		img.headers.set('Content-Disposition', 'attachment', filename=f"{image_id}.jpg")
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
		app.logger.info(f"Deleting settleplates : {selected}")

	# define search from request data
	date_from = request.args.get('from', (date.today() - timedelta(days=7)).isoformat(), str)
	date_to = request.args.get('to', (date.today()).isoformat(), str)
	batch = request.args.get('batch', "", str)
	#batch.replace('_','__') # escape wildcard

	#define query
	query = Settleplate.query
	# filter date
	try:
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
	return jsonify([])

@app.route('/db/plate_info', methods=(['POST']))
def plate_info():
	data = request.get_json()
	barcode = data['barcode']
	if not len(barcode):
		return jsonify({'error':'missing serial'})
	
	# query for registration
	query = db.session.query(Settleplate.ScanDate, Settleplate.Location, Settleplate.Batch, Settleplate.Username)
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
	# check if user scanning plate is same as user registering, and check if settings allow this
	response['SameUser'] = (g.username == plateinfo.Username) and settings['general']['sameuser']
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
				app.logger.info(f'Saved {sp.Barcode} to DB with {sp.Counts} counts')
				return jsonify({'committed':True, 'Counts': sp.Counts, 'ID': sp.ID, 'dT': dt })
		else:
			return jsonify({'committed':False})


@app.route('/register_new', methods=['POST'])
def commit_new():
	data = request.get_json()
	data.update(Decoder.parse_input(data['serial'])) # parse serial and add result to data dictionary
		
	required = ['batch', 'serial', 'location']
	if all([k in data for k in required]):
		new_sp = Settleplate()
		new_sp.Username = g.username
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
def admin_settings():
	#form = SettingsForm()
	#form.populate()

	#if form.validate_on_submit() and g.isAdmin:
	#	pass

	return render_template('settings.html', settings=settings.data)#, form=form)

@app.route('/status', methods=(['GET']))
def status():
	return jsonify(servicemonitor.status)
