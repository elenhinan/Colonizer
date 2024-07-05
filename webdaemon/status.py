from threading import Timer
from webdaemon.database import db
from webdaemon.settings import settings
import os
import hwlayer.client
import atexit

class ServiceMonitor(Timer):
	status = {}

	def __init__(self, interval=30):
		atexit.register(self.cancel)
		super().__init__(interval, self.check_services)

	def run(self):
		while not self.finished.wait(self.interval):
			self.function(*self.args, **self.kwargs)

	def check_services(self):
		# check sql status
		try:
			db.session.execute('SELECT 1')
		except:
			self.status['sql'] = False
		else:
			self.status['sql'] = True

		# check camera status
		self.status['camera'] = hwlayer.client.is_ready()

		# check storage status
		self.status['storage'] = os.path.ismount(settings['general']['mountpoint'])

servicemonitor = ServiceMonitor()