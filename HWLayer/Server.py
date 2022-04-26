from os import defpath
import zmq

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("ipc:///tmp/settleplate_hw")

def start():
   while True:
      message = socket.recv()
      print(f"Recieved request: {message}")

      socket.send("test")