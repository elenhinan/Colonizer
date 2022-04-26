from os import defpath
import zmq

# def start():
# 	while True:
# 		message = socket.recv()
# 		print(f"Recieved request: {message}")

# 		socket.send("test")

class LEDs:
	context = zmq.Context()
	socket = context.socket(zmq.REQ)
	socket.connect("ipc:///tmp/settleplate_leds")

	def __init__(self, app):
		self.logger = app.logger

class Camera:
	context = zmq.Context()
	socket = context.socket(zmq.REQ)
	socket.connect("ipc:///tmp/settleplate_camera")

	def __init__(self, app):
		self.logger = app.logger
