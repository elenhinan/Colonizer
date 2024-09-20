from datetime import datetime, timedelta, date
from flask import Blueprint, render_template, g, abort, redirect, url_for
from webdaemon.model import Settleplate
from webdaemon.database import db
from sqlalchemy import func, cast, and_

blueprint = Blueprint("hiscore",__name__,url_prefix="/hiscore")
@blueprint.route('/<when>', methods=['GET'])
def hiscore(when:str):
   # check period of scores
   if when == 'all-time':
      period = 'All Time'
      date_from = None
      date_to = None
   elif when == 'last-year':
      period = 'Last 365 days'
      date_from = date.today() - timedelta(days=365)
      date_to = date.today()
   elif when == 'last-month':
      period = 'Last 30 days'
      date_from = date.today() - timedelta(days=30)
      date_to = date.today()
   elif when.isnumeric():
      when = int(when)
      if 2000 < when <= date.today().year:
         date_from = date(year=when, month=1, day=1)
         date_to = date(year=when, month=12, day=31)
         period = when
      else:
         abort(404)
   else:
      abort(404)

   # cast barcode from text to varchar, sowe can use group_by
   barcode_cast = cast(Settleplate.Barcode,db.VARCHAR(128))
   # return only maximum counts per unique barcode
   max_counts = func.max(Settleplate.Counts).label('max_counts')
   # create subquery for 10 highest counts
   subquery = db.session.query(barcode_cast, max_counts).group_by(barcode_cast)
   subquery = subquery.filter(Settleplate.Counts >= 1)
   if date_from is not None and date_to is not None:
      subquery = subquery.filter(
         Settleplate.ScanDate >= datetime(date_from.year, date_from.month, date_from.day),
         Settleplate.ScanDate <= datetime(date_to.year, date_to.month, date_to.day, 23, 59, 59)
      )
   subquery = subquery.order_by(max_counts.desc()).limit(10).subquery()
   
   # use subquery to look up settleplates at registration date, sorted by number of counts
   query = db.session.query(Settleplate.ID, Settleplate.ScanDate, Settleplate.Username, Settleplate.Location, Settleplate.Barcode, subquery.c.max_counts)
   query = query.join(subquery, and_(barcode_cast == subquery.c.Barcode, Settleplate.Counts == subquery.c.max_counts)).order_by(subquery.c.max_counts.desc())

   results = query.all()
   hiscore_table = []
   for r in results:
      # place results into dict
      sp = {
         'ID': r.ID,
         'Location': r.Location,
         'Counts': r.max_counts,
      }
      # try to get the registering user and date
      try:
         q = db.session.query(Settleplate.Username, Settleplate.ScanDate).filter(Settleplate.Barcode.like(r.Barcode), Settleplate.Counts == -1).one()
         sp['Username'] = q.Username
         sp['ScanDate'] = q.ScanDate.strftime("%Y%m%d")
      except:
         sp['Username'] = '<unknown>'
         sp['ScanDate'] = '<unkown>'
      hiscore_table.append(sp)

   return render_template('hiscore.html', settleplates=hiscore_table, period=period)