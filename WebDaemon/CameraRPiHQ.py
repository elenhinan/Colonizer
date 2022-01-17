#!/usr/bin/env python3
import cv2
import numpy as np

class Camera():

	def __init__(self, app, deviceid=0):
		# get logger
		self.logger = app.logger

		# pyueye camera driver
		self.capturing = False
		self.h_cam = None
		self.cam_info = None
		self.image = None
		self.camera_ready = False

		# use first camera

		# init camera

		# find max resolution

		# allocate matching numpy array for image

		# set color mode

		# set gain

		# set auto modes

	def check_ueye(self, retvalue, name):
		return False

	def set_exposure(self, value):
		self.logger.debug('Exposure: %d' % value)

	def close(self):
		self.stop()

	def heigh(self):
		return self.img_height

	def width(self):
		return self.img_width

	def capture(self, exp=None):
		# capture image
		return np.zeros([256,256,3],dtype=np.uint8)

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
