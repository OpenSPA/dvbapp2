# -*- coding: utf-8 -*-
# by digiteng...04.2020 - 08,2020
# <widget source="session.Event_Now" render="xtraBackdrop" delayPic="500" position="0,0" size="300,169" zPosition="1" />
from Renderer import Renderer
from enigma import ePixmap, ePicLoad, eTimer, eEPGCache
from Components.AVSwitch import AVSwitch
from Components.Pixmap import Pixmap
from Components.config import config
from Tools.Directories import fileExists
import re

try:
	from Plugins.Extensions.xtraEvent.xtra import xtra
	pathLoc = config.plugins.xtraEvent.loc.value
except:
	pass

class xtraBackdrop(Renderer):
	def __init__(self):
		Renderer.__init__(self)
		self.delayPicTime = 100

	def applySkin(self, desktop, parent):
		attribs = self.skinAttributes[:]
		for attrib, value in self.skinAttributes:
			if attrib == 'delayPic':          # delay time(ms) for backdrop showing...
				self.delayPicTime = int(value)
			
		self.skinAttributes = attribs
		return Renderer.applySkin(self, desktop, parent)

	GUI_WIDGET = ePixmap
	def changed(self, what):
		if not self.instance:
			return
		else:
			if what[0] != self.CHANGED_CLEAR:
				self.delay()

	def showPicture(self):
		evnt = ''
		pstrNm = ''
		evntNm = ''
		try:
			event = self.source.event
			if event:
				evnt = event.getEventName()
				evntNm = re.sub("([\(\[]).*?([\)\]])|(: odc.\d+)|(\d+: odc.\d+)|(\d+ odc.\d+)|(:)|( -(.*?).*)|(,)|!", "", evnt).rstrip().lower()
				pstrNm = "{}xtraEvent/backdrop/{}.jpg".format(pathLoc, evntNm)
				if fileExists(pstrNm):
					size = self.instance.size()
					self.picload = ePicLoad()
					sc = AVSwitch().getFramebufferScale()
					if self.picload:
						self.picload.setPara((size.width(), size.height(),  sc[0], sc[1], False, 1, '#00000000'))
					result = self.picload.startDecode(pstrNm, 0, 0, False)
					if result == 0:
						ptr = self.picload.getData()
						if ptr != None:
							self.instance.setPixmap(ptr)
							self.instance.show()
					del self.picload
				else:
					self.instance.hide()
			else:
				self.instance.hide()
		except:
			pass


	def delay(self):
		self.timer = eTimer()
		self.timer.callback.append(self.showPicture)
		self.timer.start(self.delayPicTime, True)
		
