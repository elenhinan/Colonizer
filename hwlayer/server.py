import sys
import logging
import logging.handlers
import zmq
import time

# setup logging
log_root = logging.getLogger()
log_formatter = logging.Formatter("%(asctime)s | %(name)12s | %(levelname)8s : %(message)s")
#log_filehandler = logging.handlers.TimedRotatingFileHandler('log/ColonizerHW.log', when='midnight', backupCount=7)
#log_filehandler.setFormatter(log_formatter)
#log_filehandler.setLevel('DEBUG')
log_stdhandler = logging.StreamHandler(sys.stdout)
log_stdhandler.setFormatter(log_formatter)
log_stdhandler.setLevel('DEBUG')
#log_root.addHandler(log_filehandler)
log_root.addHandler(log_stdhandler)

log = logging.getLogger('Server')
log.setLevel('DEBUG')
log.info("Starting server")

# declare variables
camera = None
socket = None

def start_socket():
   global socket
   port = 3117
   context = zmq.Context()
   log.info('Creating ZeroMQ socket')
   try:
      socket = context.socket(zmq.REP)
      socket.bind("ipc:///tmp/settleplate_hw")
      #socket.bind(f"tcp://*:{port}")
   except Exception as e:
      log.error('Could not create ZeroMQ socket')

from hwlayer.picamera import PiHQCamera2
def start_camera():
   global camera
   log.info('Setting up camera')
   camera = PiHQCamera2()

def main():
   # time to wait for request before doing housekeeping
   timeout = 5000 # ms
   prev_request = None

   while True:
      if socket.poll(timeout):
         request = socket.recv_json()
         cmd = request.pop('CMD')

         if cmd == 'ready':
            camera.ready_cam()
            response = {
               'msg' : camera.isReady()
            }
            socket.send_json(response)
            continue

         request.setdefault('wb', [None, None])
         request.setdefault('light', None)
         request.setdefault('exposure', None)
         request.setdefault('resolution', None)
         request.setdefault('hflip', False)
         request.setdefault('vflip', False)
         request.setdefault('rotation', None)
         request.setdefault('crop', None)
         request.setdefault('color', [92,92,92])

         # time capture
         t0 = time.time_ns()

         # check if settings changed
         if request != prev_request:
               camera.set_light(request['light'],request['color'])
               camera.set_exposure(request['exposure'])
               camera.set_whitebalance(request['wb'][0],request['wb'][1])
               camera.set_crop(request['crop'])
               camera.set_resolution(request['resolution'])
               camera.set_flip(request['hflip'], request['vflip'])
               camera.set_rotation(request['rotation'])
               prev_request = request
         
         # if capturing array
         try:
               if cmd == 'array':
                  log.debug(request)
                  image = camera.capture_array()
                  response = {
                     'msg:'  : 'ok',
                     'dtype' : str(image.dtype),
                     'shape' : image.shape
                  }
                  socket.send_json(response, flags=zmq.SNDMORE)
                  socket.send(image, copy=True)
                  t1 = time.time_ns()
                  log.debug(f"Response time {(t1-t0)*1e-6:.0f} ms")
               elif cmd == 'jpeg':
                  log.debug(request)
                  data = camera.capture_jpeg()
                  response = {
                     'msg'   : 'ok',
                     'dtype' : 'jpeg'
                  }
                  socket.send_json(response, flags=zmq.SNDMORE)
                  socket.send(data, copy=True)
                  t1 = time.time_ns()
                  log.debug(f"Response time {(t1-t0)*1e-6:.0f} ms")
                  
         except Exception as e:
               logging.error(e)
               response = {
                  'msg'   : 'error',
                  'error' : f"Could not perform {cmd} command"
               }
               socket.send_json(response)
               log.error(response['error'])
               
      camera.update()

if __name__ == '__main__':
    start_socket()
    start_camera()
    try:
        main()
    except KeyboardInterrupt:
        log.info("Shutting down")