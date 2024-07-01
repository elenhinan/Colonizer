#!/usr/bin/env python3
import cv2
import numpy as np
from ctypes import *
from hwlayer.base import BaseCamera, BaseSettings
try:
   from pyueye import ueye
   from pyueye.ueye import c_mem_p
except:
   print('uEye python library not found')

class UeyeSettings(BaseSettings):
   pass

class CameraUeye(BaseCamera):
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

      # get config
      self.config = UeyeSettings()

      # use first camera
      self.h_cam = ueye.HIDS(deviceid)

      # init camera
      if not self._check_ueye(ueye.is_InitCamera(self.h_cam, None), 'InitCamera'):
         self.cam_started = False
         return
      else:
         self.cam_started = True

      # enable autoexit
      self._check_ueye(ueye.is_EnableAutoExit(
         self.h_cam, ueye.IS_ENABLE_AUTO_EXIT), 'EnableAutoExit')

      # set DIB mode
      self._check_ueye(ueye.is_SetDisplayMode(
         self.h_cam, ueye.IS_SET_DM_DIB), 'SetDisplayMode')

      #set Freerun mode
      self._check_ueye(ueye.is_SetExternalTrigger(
         self.h_cam, ueye.IS_SET_TRIGGER_OFF), 'SetExternalTrigger')
      #self.check_ueye(ueye.is_SetExternalTrigger(self.h_cam, ueye.IS_SET_TRIGGER_SOFTWARE), 'SetExternalTrigger')

      # find max resolution
      self.cam_sensorinfo = ueye.SENSORINFO()
      self._check_ueye(ueye.is_GetSensorInfo(
         self.h_cam, self.cam_sensorinfo), 'GetSensorInfo')
      self.logger.debug('Found sensor %s' % str(self.cam_sensorinfo.strSensorName))
      self.cam_camerainfo = ueye.CAMINFO()
      self._check_ueye(ueye.is_GetCameraInfo(
         self.h_cam, self.cam_camerainfo), 'GetCameraInfo')

      # allocate memory
      self.img_width = self.cam_sensorinfo.nMaxWidth.value
      self.img_height = self.cam_sensorinfo.nMaxHeight.value
      self.logger.debug('Image size: x%4d y%4d' %
                        (self.img_width, self.img_height))
      img_bpp = c_int(24)
      self.img_pointer = c_mem_p()
      self.img_pid = c_int()
      self._check_ueye(ueye.is_AllocImageMem(self.h_cam, c_int(self.img_width), c_int(
         self.img_height), img_bpp, self.img_pointer, self.img_pid), 'AllocateImageMem')
      self._check_ueye(ueye.is_SetImageMem(
         self.h_cam, self.img_pointer, self.img_pid), 'SetImageMem')

      # allocate matching numpy array for image
      self.image = np.zeros((self.img_height, self.img_width, 3), dtype=np.uint8)

      # set color mode
      self._check_ueye(ueye.is_SetColorMode(
         self.h_cam, ueye.IS_CM_BGR8_PACKED), 'SetColorMode')

      # set pixel clock
      pixel_clock = c_uint(16)
      self._check_ueye(ueye.is_PixelClock(
         self.h_cam, ueye.IS_PIXELCLOCK_CMD_SET, pixel_clock, sizeof(c_uint)), 'PixelClock')
      self.logger.debug('Pixelclock: %d' % pixel_clock.value)

      self.exposure = 48.
      self.set_exposure(self.exposure)

      # set gain
      #ueye.is_SetHardwareGain(self.h_cam, 20, IS_IGNORE_PARAMETER, IS_IGNORE_PARAMETER, IS_IGNORE_PARAMETER)
      self._check_ueye(ueye.is_SetGainBoost(
         self.h_cam, ueye.IS_SET_GAINBOOST_ON), 'Gain Boost on')

      # set auto modes
      enable = c_double(1)
      disable = c_double(0)
      self._check_ueye(ueye.is_SetAutoParameter(
         self.h_cam, ueye.IS_SET_ENABLE_AUTO_SHUTTER, disable, c_double(0)), 'SetAutoParameter Shutter')
      self._check_ueye(ueye.is_SetAutoParameter(
         self.h_cam, ueye.IS_SET_ENABLE_AUTO_GAIN, disable, c_double(0)), 'SetAutoParameter Gain')
      #self.check_ueye(ueye.is_SetAutoParameter(
      #	self.h_cam, ueye.IS_SET_ENABLE_AUTO_FRAMERATE, enable, c_double(0)), 'SetAutoParameter Framerate')
      self._check_ueye(ueye.is_SetAutoParameter(
         self.h_cam, ueye.IS_SET_ENABLE_AUTO_WHITEBALANCE, disable, c_double(0)), 'SetAutoParameter WB')

      # set framerate
      framerate = c_double(5)
      self._check_ueye(ueye.is_SetFrameRate(
         self.h_cam, c_double(15), framerate), 'SetFrameRate')
      self.camera_ready = True  # todo: add more tests

   def _check_ueye(self, retvalue, name):
      if not retvalue == ueye.IS_SUCCESS:
         self.logger.error('uEYE(%s): %s' % (name, retvalue))
         return False
      else:
         return True

   def capture_array(self) -> np.array:
      self._check_ueye(ueye.is_FreezeVideo(self.h_cam, ueye.IS_WAIT), 'FreezeVideo')
      self._check_ueye(ueye.is_CopyImageMem(self.h_cam, self.img_pointer,
                                       self.img_pid, self.image.ctypes.data_as(c_mem_p)), 'CopyImageMem')
      img_processed = cv2.flip(self.image, 1)  # mirror image
      return img_processed

   def capture_jpeg(self) -> bytes:
      img = self.capture_array()
      encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 95]
      return cv2.imencode(".jpg", img, encode_param)

   def update(self) -> None:
      pass

   def isReady(self) -> bool:
      return self.cam_started

   def set_flash(self, flash: str) -> None:
      pass

   def set_exposure(self, exp: int) -> None:
      exposure = c_double(exp/1000.)
      self._check_ueye(ueye.is_Exposure(
         self.h_cam, ueye.IS_EXPOSURE_CMD_SET_EXPOSURE, exposure, sizeof(c_double)), 'Exposure')
      self.logger.debug('Exposure: %d' % exposure.value)

   def set_whitebalance(self, wb_red: float, wb_blue:float) -> None:
      pass

   def set_flip(self, horizontal:bool, vertical:bool) -> None:
      self.config.flip = (horizontal, vertical)

   def close(self):
      self.stop()
      self._check_ueye(ueye.is_ExitCamera(self.h_cam), 'ExitCamera')
