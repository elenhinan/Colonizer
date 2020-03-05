# NeoPixel library strandtest example
# Author: Tony DiCola (tony@tonydicola.com)
#
# Direct port of the Arduino NeoPixel library strandtest example.  Showcases
# various animations on a strip of NeoPixels.
import time
import threading
from enum import Enum
try:
	from neopixel import *
except ImportError:
	LED_STRIP = None
else:
	# LED strip configuration:
	LED_PIN = 21  # GPIO pin connected to the pixels (must support PWM!).
	LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
	LED_DMA = 10  # DMA channel to use for generating signal (try 10)
	LED_BRIGHTNESS = 255  # Set to 0 for darkest and 255 for brightest
	LED_INVERT = False  # True to invert the signal (when using NPN transistor level shift)
	LED_CHANNEL = 0
	LED_STRIP = ws.SK6812_STRIP_RGBW

LED_LINE = range(0, 7)  # line led 1 to 7
LED_RING = range(7, 30) # ring led 8 to 30

class IlluminationMode(Enum):
	OFF = 0
	IMAGING = 1
	WAIT = 2
	FAIL = 3
	PASS = 4
	DEMO = 5

class Illumination():
	def __init__(self, app):

		self.logger = app.logger
		# Create NeoPixel object with appropriate configuration.
		if LED_STRIP is None:
			self.logger.error("NeoPixel library not found")
			
		self.n_leds = len(LED_LINE)+len(LED_RING)
		self.strip = Adafruit_NeoPixel(self.n_leds, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL,
								  LED_STRIP)
		# Intialize the library (must be called once before other functions).
		self.strip.begin()

		# Mode selection
		self.mode = IlluminationMode.OFF
		self.illuminating = False
		self.function_mapping = {
			IlluminationMode.IMAGING: lambda: self.color_fill(Color(255, 0 , 255, 48)),
			IlluminationMode.WAIT: lambda: self.rainbow(wait_ms=10),
			IlluminationMode.FAIL: lambda: self.color_wipe(Color(255, 0, 0, 0)),
			IlluminationMode.PASS: lambda: self.color_wipe(Color(0, 255, 0, 0)),
			IlluminationMode.DEMO: lambda: self.color_fill(Color(8, 8, 8, 8))
		}

	def Flash(self, onoff):
		if onoff:
			val = 255
		else:
			val = 0
		for i in LED_LINE:
			self.strip.setPixelColor(i, Color(val,val,val,val))
		self.strip.show()

	def Ring(self, onoff):
		if onoff:
			val = 96
		else:
			val = 0
		for i in LED_RING:
			self.strip.setPixelColor(i, Color(val,val,val,val))
		self.strip.show()

	# Define functions which animate LEDs in various ways.
	@staticmethod
	def wheel(pos):
		"""Generate rainbow colors across 0-255 positions."""
		if pos < 85:
			return Color(pos * 3, 255 - pos * 3, 0)
		elif pos < 170:
			pos -= 85
			return Color(255 - pos * 3, 0, pos * 3)
		else:
			pos -= 170
			return Color(0, pos * 3, 255 - pos * 3)

	def color_wipe(self, color, wait_ms=50):
		"""Wipe color across display a pixel at a time."""
		if LED_STRIP is None:
			return
		for i in range(self.strip.numPixels()):
			self.strip.setPixelColor(i, color)
			self.strip.show()
			time.sleep(wait_ms / 1000.0)

	def color_fill(self, color):
		"""Wipe color across display a pixel at a time."""
		if LED_STRIP is None:
			return
		for i in range(self.strip.numPixels()):
			self.strip.setPixelColor(i, color)
		self.strip.show()

	def rainbow(self, wait_ms=20):
		"""Draw rainbow that uniformly distributes itself across all pixels."""
		if LED_STRIP is None:
			return
		while self.illuminating:
			for j in range(256):
				for i in range(self.strip.numPixels()):
					self.strip.setPixelColor(i, self.wheel(((i * 256 // self.strip.numPixels()) + j) & 255))
				self.strip.show()
				time.sleep(wait_ms / 1000.0)

	def close(self):
		self.stop()

	def run(self):
		self.illuminating = False
		self.wait()
		self.logger.debug("Starting mode %s"%self.mode)
		self.illuminating = True
		self.function_mapping[self.mode]()

	def stop(self):
		self.mode = IlluminationMode.OFF
		self.color_fill(Color(0, 0, 0, 0))
		self.wait()
