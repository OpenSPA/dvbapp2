# by digiteng
# v1 07.2020

# <ePixmap pixmap="xtra/star_b.png" position="560,367" size="200,20" alphatest="blend" zPosition="2" transparent="1" />
# <widget render="xtraStar" source="session.Event_Now" pixmap="xtra/star.png" position="560,367" size="200,20" alphatest="blend" transparent="1" zPosition="3" />

from Components.VariableValue import VariableValue
from Renderer import Renderer
from enigma import eSlider
from Components.config import config
from Tools.Directories import fileExists
import re
import json

try:
	from Plugins.Extensions.xtraEvent.xtra import xtra
	pathLoc = config.plugins.xtraEvent.loc.value
except:
	pass

class xtraStar(VariableValue, Renderer):
	def __init__(self):
		Renderer.__init__(self)
		VariableValue.__init__(self)
		self.__start = 0
		self.__end = 100

	GUI_WIDGET = eSlider
	def changed(self, what):
		rtng = None
		if what[0] == self.CHANGED_CLEAR:
			(self.range, self.value) = ((0, 1), 0)
			return
		try:
			event = ""
			evntNm = ""
			evnt = ""
			event = self.source.event
			if event:
				evnt = event.getEventName()
				evntNm = re.sub("([\(\[]).*?([\)\]])|(: odc.\d+)|(\d+: odc.\d+)|(\d+ odc.\d+)|(:)|( -(.*?).*)|(,)|!", "", evnt).rstrip().lower()
				rating_json = "{}xtraEvent/infos/{}.json".format(pathLoc, evntNm)
				if rating_json:
					with open(rating_json) as f:
						rating = json.load(f)['imdbRating']
					if rating:
						rtng = int(10*(float(rating)))
					else:
						rtng = 0
				else:
					rtng = 0			
			else:
				rtng = 0
		except:
			pass
		range = 100
		value = rtng

		(self.range, self.value) = ((0, range), value)

	def postWidgetCreate(self, instance):
		instance.setRange(self.__start, self.__end)

	def setRange(self, range):
		(self.__start, self.__end) = range
		if self.instance is not None:
			self.instance.setRange(self.__start, self.__end)

	def getRange(self):
		return self.__start, self.__end

	range = property(getRange, setRange)
