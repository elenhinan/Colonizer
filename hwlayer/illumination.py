# NeoPixel library strandtest example
# Author: Tony DiCola (tony@tonydicola.com)
#
# Direct port of the Arduino NeoPixel library strandtest example.  Showcases
# various animations on a strip of NeoPixels.
import time
from threading import Thread, Event, Timer
from enum import Enum
import board
from neopixel_spi import NeoPixel_SPI
#from neopixel import NeoPixel

# LED strip configuration:
LED_ORDER = "GRB"
LED_RING = 24
LED_TOP = 45
LED_OFF = [0,0,0]

class Illumination():
	def __init__(self, app=None):

		if app:
			self.logger = app.logger
		else:
			self.logger = None
		# Create NeoPixel object with appropriate configuration.
			
		self.n_leds = LED_RING + LED_TOP
		self.strip = NeoPixel_SPI(board.SPI(), self.n_leds, auto_write=False, bpp=len(LED_ORDER), pixel_order=LED_ORDER)
		#self.strip = NeoPixel(board.D10, self.n_leds, auto_write=False, bpp=len(LED_ORDER), pixel_order=LED_ORDER)
		self.segment = {
			'ring' : range(0,LED_RING),
			'top'  : range(LED_RING,LED_RING+LED_TOP)
		}

		self._thread = None
		self._thread_stop = Event()
		self._busy = False
		self._timer = Timer(0, self.stop)

	def top(self, color, duration:float=0):
		self.stop()
		for i in range(self.n_leds):
			if i in self.segment['top']:
				self.strip[i] = color
			else:
				self.strip[i] = LED_OFF
		self.strip.show()
		if duration > 0:
			self._timer.interval = duration
			self._timer.start()

	def ring(self, color, duration:float=0):
		self.stop()
		for i in range(self.n_leds):
			if i in self.segment['ring']:
				self.strip[i] = color
			else:
				self.strip[i] = LED_OFF
		self.strip.show()
		if duration > 0:
			self._timer.interval = duration
			self._timer.start()

	# Define functions which animate LEDs in various ways.
	@staticmethod
	def wheel(pos):
		"""Generate rainbow colors across 0-255 positions."""
		if pos < 85:
			return [pos * 3, 255 - pos * 3, 0]
		elif pos < 170:
			pos -= 85
			return [255 - pos * 3, 0, pos * 3]
		else:
			pos -= 170
			return [0, pos * 3, 255 - pos * 3]

	def color_wipe(self, color, wait_ms=100):
		self.stop()
		self._thread = Thread(target=self._color_wipe, args=[color,wait_ms])
		self._thread.start()

	def _color_wipe(self, color, wait_ms):
		"""Wipe color across display a pixel at a time."""
		for i in range(LED_RING):
			if self._thread_stop.is_set():
				return
			self.strip[i] = color
			self.strip.show()
			time.sleep(wait_ms / 1000.0)

	def rainbow(self, wait_ms=10, duration=0):
		self.stop()
		self._thread = Thread(target=self._rainbow, args=[wait_ms])
		self._thread.start()

	def _rainbow(self, wait_ms):
		"""Draw rainbow that uniformly distributes itself across all pixels."""
		while True:
			for j in range(256):
				for i in range(LED_RING):
					self.strip[i] = self.wheel(((i * 256 // LED_RING) + j) & 255)
				self.strip.show()
				time.sleep(wait_ms / 1000.0)
				if self._thread_stop.is_set():
					print('stopping rainbow')
					return

	def stop(self):
		if self._timer.is_alive:
			self._timer.cancel()
		if type(self._thread) is Thread:
			if self._thread.is_alive():
				self._thread_stop.set()
				self._thread.join()
			self._thread = None
			self._thread_stop.clear()
		self.strip.fill([0,0,0])
		
illumination = Illumination()

if __name__ == "__main__":
	led = Illumination()
	#led.ring([255,196,92])
	print('test rainbow')
	led.rainbow(10);
	time.sleep(10)
	print('test wipe')
	led.color_wipe([92,0,12])
	time.sleep(5)
	print('test ring')
	led.ring([92,92,92])
	print('test stop')
	led.stop()
	