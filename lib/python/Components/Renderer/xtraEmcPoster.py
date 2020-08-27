# -*- coding: utf-8 -*-
# by digiteng...07.2020 - 08.2020
# <widget source="Service" render="xtraEmcPoster" delayPic="500" position="0,0" size="185,278" zPosition="0"
from Renderer import Renderer
from enigma import ePixmap, loadJPG, eTimer
from Tools.Directories import fileExists
from Components.Sources.ServiceEvent import ServiceEvent
from Components.Sources.CurrentService import CurrentService
from Components.config import config
import re

try:
	from Plugins.Extensions.xtraEvent.xtra import xtra
	pathLoc = config.plugins.xtraEvent.loc.value
except:
	pass

class xtraEmcPoster(Renderer):

	def __init__(self):
		Renderer.__init__(self)
		self.piconsize = (0,0)
		self.delayPicTime = 100

	def applySkin(self, desktop, parent):
		attribs = self.skinAttributes[:]
		for (attrib, value) in self.skinAttributes:
			if attrib == "size":
				self.piconsize = value
			elif attrib == 'delayPic':          # delay time(ms) for emc poster showing...
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
		movieNm = ""
		try:
			service = self.source.getCurrentService()
			if service:
				evnt = service.getPath()
				movieNm = evnt.split('-')[-1].split(".")[0].strip().lower()
				movieNm = re.sub("([\(\[]).*?([\)\]])|(: odc.\d+)|(\d+: odc.\d+)|(\d+ odc.\d+)|(:)|( -(.*?).*)|(,)|!", "", movieNm)
				pstrNm = "{}xtraEvent/EMC/{}-poster.jpg".format(pathLoc, movieNm.strip())
				if fileExists(pstrNm):
					self.instance.setScale(1)
					self.instance.setPixmap(loadJPG(pstrNm))
					self.instance.show()
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
		
		