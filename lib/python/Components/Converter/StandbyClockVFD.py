from Converter import Converter
from Components.Element import cached
from time import localtime, strftime
from Components.config import config


class StandbyClockVFD(Converter, object):
	def __init__(self, type):
		Converter.__init__(self, type)
		self.seg = 0
		self.type = 1

	@cached
	def getText(self):
		time = self.source.time
		if time is None:
			return ""
		t = localtime(time)

		try:
			dformat = str(config.usage.lcd_dateformat.value)
			if not dformat:
				dformat = "%H:%M"
		except:
			dformat = "%H:%M"

		if dformat == "OFF":
			text = " "
		elif dformat[0] == "A":
			f = dformat.find(" ")
			format1 = dformat[1:f]
			format2 = dformat[f + 1:] 

			self.seg += 1
			if self.seg == 15:
				self.type += 1
				self.seg = 0
			if self.type == 3:
				self.type = 1

			if self.type == 2:
				text = strftime(_(format2), t)
			if self.type == 1:
				text = strftime(_(format1), t)
		else:
			text = strftime(_(dformat), t)
		return text

	text = property(getText)
