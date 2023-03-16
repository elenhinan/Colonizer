#!/usr/bin/env python3
import cv2
import numpy as np
from ctypes import *
try:
	from pyueye import ueye
	from pyueye.ueye import c_mem_p
except:
	print('uEye python library not found')


class CameraUeye():
	# https://en.ids-imaging.com/manuals/uEye_SDK/EN/uEye_Manual_4.90/index.html

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
		self.h_cam = ueye.HIDS(deviceid)

		# init camera
		if not self.check_ueye(ueye.is_InitCamera(self.h_cam, None), 'InitCamera'):
			return

		# enable autoexit
		self.check_ueye(ueye.is_EnableAutoExit(
			self.h_cam, ueye.IS_ENABLE_AUTO_EXIT), 'EnableAutoExit')

		# set DIB mode
		self.check_ueye(ueye.is_SetDisplayMode(
			self.h_cam, ueye.IS_SET_DM_DIB), 'SetDisplayMode')

		#set Freerun mode
		self.check_ueye(ueye.is_SetExternalTrigger(
			self.h_cam, ueye.IS_SET_TRIGGER_OFF), 'SetExternalTrigger')
		#self.check_ueye(ueye.is_SetExternalTrigger(self.h_cam, ueye.IS_SET_TRIGGER_SOFTWARE), 'SetExternalTrigger')

		# find max resolution
		self.cam_sensorinfo = ueye.SENSORINFO()
		self.check_ueye(ueye.is_GetSensorInfo(
			self.h_cam, self.cam_sensorinfo), 'GetSensorInfo')
		self.logger.debug('Found sensor %s' % str(self.cam_sensorinfo.strSensorName))
		self.cam_camerainfo = ueye.CAMINFO()
		self.check_ueye(ueye.is_GetCameraInfo(
			self.h_cam, self.cam_camerainfo), 'GetCameraInfo')

		# allocate memory
		self.img_width = self.cam_sensorinfo.nMaxWidth.value
		self.img_height = self.cam_sensorinfo.nMaxHeight.value
		self.logger.debug('Image size: x%4d y%4d' %
		                  (self.img_width, self.img_height))
		img_bpp = c_int(24)
		self.img_pointer = c_mem_p()
		self.img_pid = c_int()
		self.check_ueye(ueye.is_AllocImageMem(self.h_cam, c_int(self.img_width), c_int(
			self.img_height), img_bpp, self.img_pointer, self.img_pid), 'AllocateImageMem')
		self.check_ueye(ueye.is_SetImageMem(
			self.h_cam, self.img_pointer, self.img_pid), 'SetImageMem')

		# allocate matching numpy array for image
		self.image = np.zeros((self.img_height, self.img_width, 3), dtype=np.uint8)

		# set color mode
		self.check_ueye(ueye.is_SetColorMode(
			self.h_cam, ueye.IS_CM_BGR8_PACKED), 'SetColorMode')

		# set pixel clock
		pixel_clock = c_uint(16)
		self.check_ueye(ueye.is_PixelClock(
			self.h_cam, ueye.IS_PIXELCLOCK_CMD_SET, pixel_clock, sizeof(c_uint)), 'PixelClock')
		self.logger.debug('Pixelclock: %d' % pixel_clock.value)

		self.exposure = 48.
		self.set_exposure(self.exposure)

		# set gain
		#ueye.is_SetHardwareGain(self.h_cam, 20, IS_IGNORE_PARAMETER, IS_IGNORE_PARAMETER, IS_IGNORE_PARAMETER)
		self.check_ueye(ueye.is_SetGainBoost(
			self.h_cam, ueye.IS_SET_GAINBOOST_ON), 'Gain Boost on')

		# set auto modes
		enable = c_double(1)
		disable = c_double(0)
		self.check_ueye(ueye.is_SetAutoParameter(
			self.h_cam, ueye.IS_SET_ENABLE_AUTO_SHUTTER, disable, c_double(0)), 'SetAutoParameter Shutter')
		self.check_ueye(ueye.is_SetAutoParameter(
			self.h_cam, ueye.IS_SET_ENABLE_AUTO_GAIN, disable, c_double(0)), 'SetAutoParameter Gain')
		#self.check_ueye(ueye.is_SetAutoParameter(
		#	self.h_cam, ueye.IS_SET_ENABLE_AUTO_FRAMERATE, enable, c_double(0)), 'SetAutoParameter Framerate')
		self.check_ueye(ueye.is_SetAutoParameter(
			self.h_cam, ueye.IS_SET_ENABLE_AUTO_WHITEBALANCE, disable, c_double(0)), 'SetAutoParameter WB')

		# set framerate
		framerate = c_double(5)
		self.check_ueye(ueye.is_SetFrameRate(
			self.h_cam, c_double(15), framerate), 'SetFrameRate')
		self.camera_ready = True  # todo: add more tests

	def check_ueye(self, retvalue, name):
		if not retvalue == ueye.IS_SUCCESS:
			self.logger.error('uEYE(%s): %s' % (name, retvalue))
			return False
		else:
			return True

	def set_exposure(self, value):
		exposure = c_double(value)
		self.check_ueye(ueye.is_Exposure(
			self.h_cam, ueye.IS_EXPOSURE_CMD_SET_EXPOSURE, exposure, sizeof(c_double)), 'Exposure')
		self.logger.debug('Exposure: %d' % exposure.value)

	def close(self):
		self.stop()
		self.check_ueye(ueye.is_ExitCamera(self.h_cam), 'ExitCamera')

	def heigh(self):
		return self.img_height

	def width(self):
		return self.img_width

	def capture(self, exp=None):
		# capture image
		if exp != None:
			self.set_exposure(exp)
		else:
			self.set_exposure(self.exposure)

		self.check_ueye(ueye.is_FreezeVideo(self.h_cam, ueye.IS_WAIT), 'FreezeVideo')
		self.check_ueye(ueye.is_CopyImageMem(self.h_cam, self.img_pointer,
                                       self.img_pid, self.image.ctypes.data_as(c_mem_p)), 'CopyImageMem')
		img_processed = cv2.flip(self.image, 1)  # mirror image
		return img_processed

	def capture_hdr(self):
		# capture hdr image series
		exp = [1/64, 1/8, 1]
		img = {}
		for e in exp:
			self.set_exposure(self.exposure*e)
			self.check_ueye(ueye.is_FreezeVideo(self.h_cam, ueye.IS_WAIT), 'FreezeVideo')
			self.check_ueye(ueye.is_CopyImageMem(self.h_cam, self.img_pointer, self.img_pid, self.image.ctypes.data_as(c_mem_p)), 'CopyImageMem')
			img[e] = cv2.flip(self.image, 1)
		return img

	# def capture_autoexp(self):
	# 	# capture image
	# 	rate = 16
	# 	self.set_exposure(self.exposure/rate)
	# 	self.check_ueye(ueye.is_FreezeVideo(self.h_cam, ueye.IS_WAIT), 'FreezeVideo')
	# 	self.check_ueye(ueye.is_CopyImageMem(self.h_cam, self.img_pointer, self.img_pid, self.image.ctypes.data_as(c_mem_p)), 'CopyImageMem')
		
	# 	hist = np.histogram(self.image, bins=256, range=(0,255), density=True)
		
	# 	exposure_clip = 0.98
	# 	for i in range(256):
	# 		exposure_clip = exposure_clip + hist[-i]
	# 		if exposure_clip > 1.0:
	# 			rate/256*(256-i)
	# 			break
		
	# 	img_processed = cv2.flip(self.image, 1)  # mirror image
	# 	return img_processed

	def stop(self):
		self.capturing = False
		self.wait()
