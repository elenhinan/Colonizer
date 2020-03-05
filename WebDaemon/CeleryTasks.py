from celery import Celery
from celery.utils.log import get_task_logger
from WebDaemon import app, db
from WebDaemon.ImageTools import to_png
from WebDaemon.Settleplate import Settleplate

logger = get_task_logger(__name__)

def CeleryWorker(app):
	celery = Celery(
		app.import_name,
		backend=app.config['CELERY_RESULT_BACKEND'],
		broker=app.config['CELERY_BROKER_URL']
	)
	celery.conf.update(app.config)

	class ContextTask(celery.Task):
		def __call__(self, *args, **kwargs):
			with app.app_context():
				return self.run(*args, **kwargs)

			celery.Task = ContextTask
			return celery


class TaskFailure(Exception):
	logger.exception(Exception)


@celery.task
def add_scan_async(sp, image):
	# query for registration
	query = db.session.query(Settleplate.Location, Settleplate.Batch, Settleplate.Lot_no, Settleplate.ScanDate, Settleplate.Expires, Settleplate.Lot_no)
	filters = query.filter(Settleplate.Barcode.like(sp.Barcode), Settleplate.Counts == -1)
	try:
		plateinfo = filters.one()
		sp.Lot_no = plateinfo.Lot_no
		sp.Expires = plateinfo.Expires
		sp.Location = plateinfo.Location
		sp.Batch = plateinfo.Batch
	except:
		raise TaskFailure('Could not find serial in DB')

	try:
		sp.Image = to_png(image)
	except:
		raise TaskFailure('Image data corrupted')

	try:
		db.session.add(sp)
		db.session.commit()
	except Exception as e:
		raise TaskFailure('Could not write to SQL: %s'%str(e))
