from webdaemon import app

from flask import render_template, redirect, url_for

from . import admin
from . import edit
from . import images
from . import list
from . import register
from . import scan
from . import tools
from . import users

app.register_blueprint(admin.blueprint)
app.register_blueprint(edit.blueprint)
app.register_blueprint(images.blueprint)
app.register_blueprint(list.blueprint)
app.register_blueprint(register.blueprint)
app.register_blueprint(scan.blueprint)
app.register_blueprint(tools.blueprint)
app.register_blueprint(users.blueprint)

# default page
@app.route('/')
def index():
	return redirect(url_for('list.settleplates'))

# 404 not found
@app.errorhandler(404)
def page_not_found(e):
	# note that we set the 404 status explicitly
	return render_template('404.html'), 404