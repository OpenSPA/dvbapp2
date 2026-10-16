from enigma import eLabel, eTimer

from Components.config import config
from Components.SystemInfo import BoxInfo
from Components.VariableText import VariableText
from Components.Renderer.Renderer import Renderer


class RollerCharLCD(VariableText, Renderer):
	GUI_WIDGET = eLabel

	def __init__(self):
		Renderer.__init__(self)
		VariableText.__init__(self)
		self.moveTimerText = eTimer()
		self.moveTimerText.callback.append(self.moveTimerTextRun)
		self.delayTimer = eTimer()
		self.delayTimer.callback.append(self.delayTimergo)
		self.stringlength = 16 if BoxInfo.getItem("machinebuild") in ("vuduo", "sf4008", "beyonwizu4") else 12

	def connect(self, source):
		Renderer.connect(self, source)
		self.changed((self.CHANGED_DEFAULT,))

	def changed(self, what):
		self.moveTimerText.stop()
		self.delayTimer.stop()
		if what[0] == self.CHANGED_CLEAR:
			self.text = ""
		else:
			self.text = self.source.text
		if len(self.text) > self.stringlength:
			self.text = self.source.text + " " * self.stringlength + self.source.text[:self.stringlength + 1]
			self.x = len(self.text) - self.stringlength
			self.idx = 0
			self.backtext = self.text
			self.moveTimerText.start(2000)
		else:
			self.text = self.source.text
			self.x = len(self.text)
			self.idx = 0
			self.backtext = self.text

	def moveTimerTextRun(self):
		self.moveTimerText.stop()
		if self.x > 0:
			txttmp = self.backtext[self.idx:]
			self.text = txttmp[:self.stringlength]
			str_length = 1
			accents = self.text[:2]
			if accents in ("\xc3\xbc", "\xc3\xa4", "\xc3\xb6", "\xc3\x84", "\xc3\x9c", "\xc3\x96", "\xc3\x9f", "\xc3\xa1", "\xc3\xa9", "\xc3\xad", "\xc3\xb3", "\xc3\xba", "\xc3\xb1", "\xc3\x81", "\xc3\x89", "\xc3\x8d", "\xc3\x93", "\xc3\x9a", "\xc3\x91"):
				str_length = 2
			self.idx = self.idx + str_length
			self.x = self.x - str_length
		if self.x == 0:
			self.text = self.backtext
			if config.lcd.scrollDelay.value:
				self.delayTimer.start(config.lcd.scrollDelay.value * 1000, True)
		else:
			self.moveTimerText.start(config.lcd.scrollSpeed.value)

	def delayTimergo(self):
		self.delayTimer.stop()
		self.changed((self.CHANGED_DEFAULT,))
