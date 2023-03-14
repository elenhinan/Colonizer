import zmq
import time
import numpy as np
from typing import Union

context = zmq.Context()
socket = None

default_settings = {
   'flash': 'ring',
   'exposure': 50000,
   'wb': [2.3,2.3],
   'crop': (516, 16, 3008, 3008),
   'image': True,
   'hflip': False,
   'vflip': True
}

def start_socket(adr: str = 'localhost') -> bool:
   global socket
   if socket is not None:
      socket.close()
   socket = context.socket(zmq.REQ)
   port = 3117
   #socket.connect("ipc:///tmp/settleplate_hw")
   socket.connect(f"tcp://{adr}:{port}")
   # set timeout
   socket.RCVTIMEO = 5000 # ms
   socket.setsockopt(zmq.LINGER, 0)

   # todo check connection and return False if it fails
   return True

def capture_image(capture_settings=default_settings) -> Union(bool, np.ndarray):
    # maximum wait time for image capture
    timeout = 5000 # ms

    t0 = time.time_ns()

    # request image
    request = default_settings.copy()
    request['CMD'] = 'array'

    # send
    socket.send_json(request)
    # wait for data

    try:
        response = socket.recv_json()
        if 'error' in response:
            print(response['error'])
        else:
            buffer = socket.recv(copy=True)
            t1 = time.time_ns()
            image = np.frombuffer(buffer, dtype=response['dtype'])
            image = image.reshape(response['shape'])
            print(f"Capture time {(t1-t0)*1e-6:.0f} ms")
            return True, image
    except Exception as e:
        print(f"ZMQ error: {e}")
        start_socket() # restart socket
        return False, None