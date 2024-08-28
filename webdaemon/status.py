from threading import Timer
from webdaemon.database import db
from sqlalchemy import text
from settings import settings
import os
import hwlayer.client
import atexit

class ServiceMonitor(Timer):
	status = {}

	def __init__(self, interval=30):
		self._app = None
		atexit.register(self.cancel)
		super().__init__(interval, self.check_services)

	def init(self, app):
		self._app = app
		self.check_services()
		self.start()

	def run(self):
		while not self.finished.wait(self.interval):
			self.function(*self.args, **self.kwargs)

	def check_services(self):
		# check sql status
		try:
			with self._app.app_context():
				db.session.execute(text('SELECT 1'))
		except:
			self.status['sql'] = False
		else:
			self.status['sql'] = True

		# check camera status
		self.status['camera'] = hwlayer.client.is_ready()

		# check storage status
		self.status['storage'] = os.path.ismount(settings['general']['mountpoint'])

servicemonitor = ServiceMonitor()