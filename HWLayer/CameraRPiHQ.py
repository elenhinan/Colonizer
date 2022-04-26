#!/usr/bin/env python3
import cv2
import numpy as np
from time import sleep, time
from picamera import PiCamera
from fractions import Fraction

class CameraRPiHQ():

	def __init__(self, app):
		# get logger
		self.logger = app.logger

		self.camera = PiCamera(resolution=(4056,3040))
		self.camera.iso = 100
		sleep(2)
		self.camera.shutter_speed = self.camera.exposure_speed
		self.camera.exposure_mode = 'off'
		g = self.camera.awb_gains
		self.camera.awb_mode = 'off'
		self.camera.awb_gains = g

	def set_exposure(self, value):
		self.logger.debug('Exposure: %d' % value)

	def close(self):
		self.stop()

	def height(self):
		return self.camera.resolution.height

	def width(self):
		return self.camera.resolution.width

	def capture(self, exp=None):
		# capture image
		start = time()
		rx,ry = self.camera.resolution.pad()
		buffer = np.empty(rx*ry*3, dtype=np.uint8)
		self.camera.capture(buffer, 'bgr')
		image = buffer.reshape((ry,rx,3))
		end = time()
		self.logger.info("Image taken (%s)"%(end-start))
		return image

	def capture_hdr(self):
		# capture hdr image series
		exp = [1/64, 1/8, 1]
		img = {}
		for e in exp:
			#self.set_exposure(self.exposure*e)
			img[e] = None
		return img

	def stop(self):
		self.capturing = False
		self.wait()
