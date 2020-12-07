# -*- coding: utf-8 -*-
# by digiteng...07.2020 - 08.2020
# <widget source="Service" render="xtraEmcBackdrop" delayPic="500" position="0,0" size="1280,720" zPosition="0"
from Renderer import Renderer
from enigma import ePixmap, loadJPG, eTimer
from Components.Sources.ServiceEvent import ServiceEvent
from Components.Sources.CurrentService import CurrentService
from Components.config import config
from Tools.Directories import fileExists
import re

try:
	pathLoc = config.plugins.xtraEvent.loc.value
except:
	pass

class xtraEmcBackdrop(Renderer):

	def __init__(self):
		Renderer.__init__(self)
		self.piconsize = (0,0)
		self.delayPicTime = 100
		self.timer = eTimer()
		self.timer.callback.append(self.showPicture)
		
	def applySkin(self, desktop, parent):
		attribs = self.skinAttributes[:]
		for (attrib, value) in self.skinAttributes:
			if attrib == "size":
				self.piconsize = value
			elif attrib == 'delayPic':          # delay time(ms) for emc background showing...
				self.delayPicTime = int(value)
		self.skinAttributes = attribs
		return Renderer.applySkin(self, desktop, parent)

	GUI_WIDGET = ePixmap
	def changed(self, what):
		if not self.instance:
			return
		else:
			if what[0] != self.CHANGED_CLEAR:
				self.timer.start(self.delayPicTime, True)

	def showPicture(self):
		movieNm = ""
		try:
			service = self.source.getCurrentService()
			if service:
				evnt = service.getPath()
				movieNm = evnt.split('-')[-1].split(".")[0].strip()
				movieNm = re.sub("([\(\[]).*?([\)\]])|(: odc.\d+)|(\d+: odc.\d+)|(\d+ odc.\d+)|(:)|( -(.*?).*)|(,)|!", "", movieNm)
				pstrNm = "{}xtraEvent/EMC/{}-backdrop.jpg".format(pathLoc, movieNm.strip())
				if fileExists(pstrNm):
					self.instance.setScale(2)
					self.instance.setPixmap(loadJPG(pstrNm))
					self.instance.show()
				else:
					self.instance.setScale(2)
					self.instance.setPixmap(loadJPG("/usr/lib/enigma2/python/Plugins/Extensions/xtraEvent/pic/noMovie.jpg"))
					self.instance.show()
			else:
				self.instance.hide()
		except:
			pass
