import zmq
import numpy as np
from typing import Tuple

context = zmq.Context()
socket = None

default_settings = {
   'flash': 'ring',
   'exposure': 50000,
   'wb': [2.3,2.3],
   'crop': (524, 16, 3008, 3008),
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

def capture_image(capture_settings=default_settings) -> Tuple[bool, np.ndarray]:
    # maximum wait time for image capture
    timeout = 5000 # ms

    # request image
    request = default_settings.copy()
    request['CMD'] = 'array'

    try:
        # send
        socket.send_json(request)
        # wait for data
        response = socket.recv_json()
        if 'error' in response:
            return False, response['error']
        else:
            buffer = socket.recv(copy=True)
            image = np.frombuffer(buffer, dtype=response['dtype'])
            image = image.reshape(response['shape'])
            return True, image
    except Exception as e:
        start_socket() # restart socket
        return False, f"ZMQ error: {e}"

def is_ready():
    request = {'CMD': 'ready'}
    try:
        socket.send_json(request)
        response = socket.recv_json()
        return response['msg']
    except Exception as e:
        return False