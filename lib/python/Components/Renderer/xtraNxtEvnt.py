# -*- coding: utf-8 -*-
# by digiteng...05.2020, 07.2020,
# for channellist,
# <widget source="ServiceEvent" render="xtraNxtEvnt" nxtEvents="4" snglEvent="" font="Regular; 18" position="840,500" size="400,110" zPosition="5" backgroundColor="background" transparent="1" />
# nxtEvents or snglEvent must be empty...
from Renderer import Renderer
from enigma import eLabel, eEPGCache
from Components.VariableText import VariableText
from time import localtime

class xtraNxtEvnt(Renderer, VariableText):

	def __init__(self):
		Renderer.__init__(self)
		VariableText.__init__(self)
		
		# self.nxEvnt = 0
		self.snglEvnt = 0
		self.epgcache = eEPGCache.getInstance()

	def applySkin(self, desktop, parent):
		attribs = self.skinAttributes[:]
		for attrib, value in self.skinAttributes:
			if attrib == 'nxtEvents':
				self.nxEvnt = value
			if attrib == 'snglEvent':
				self.snglEvnt = value

		self.skinAttributes = attribs
		return Renderer.applySkin(self, desktop, parent)

	GUI_WIDGET = eLabel
	def changed(self, what):
		self.text = ''
		try:
			ref = self.source.service
			nextEvent = self.epgcache.lookupEvent(['IBDCTM', (ref.toString(), 0, 1, -1)])
			if nextEvent and self.snglEvnt == "":
				for i in xrange(int(self.nxEvnt)):
					evnts = nextEvent[i+1][4]
					bt = localtime(nextEvent[i+1][1])
					self.text = self.text + "%02d:%02d - %s\n"%(bt[3], bt[4], evnts)
			if nextEvent and self.snglEvnt != "":
				evnts = nextEvent[int(self.snglEvnt)][4]
				bt = localtime(nextEvent[int(self.snglEvnt)][1])
				self.text = self.text + "%02d:%02d - %s\n"%(bt[3], bt[4], evnts)
			else:
				return ""
		except:
			return ""
