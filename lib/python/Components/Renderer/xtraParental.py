# -*- coding: utf-8 -*-
# by digiteng...
# v1 07.2020
# <widget render="xtraParental" source="session.Event_Now" position="0,0" size="60,60" alphatest="blend" zPosition="2" transparent="1" />
from Renderer import Renderer
from enigma import ePixmap, loadPNG
from Tools.Directories import resolveFilename, SCOPE_CURRENT_SKIN, fileExists
from Components.config import config
import re
import json

try:
	from Plugins.Extensions.xtraEvent.xtra import xtra
	pathLoc = config.plugins.xtraEvent.loc.value
except:
	pass

pratePath = resolveFilename(SCOPE_CURRENT_SKIN, 'parental')

class xtraParental(Renderer):

	def __init__(self):
		Renderer.__init__(self)
		self.rateNm = ''

	GUI_WIDGET = ePixmap
	def changed(self, what):
		if not self.instance:
			return
		else:
			event = self.source.event
			if event:
				fd = event.getShortDescription() + "\n" + event.getExtendedDescription()
				try:
					ppr = ["[aA]b ((\d+))", "[+]((\d+))", "Od lat: ((\d+))"]
					for i in ppr:
						prr = re.search(i, fd)
						if prr:
							parentName = prr.group(1)
							parentName = parentName.replace("7", "6")
							break
					else:
						evnt = event.getEventName()
						evntNm = re.sub("([\(\[]).*?([\)\]])|(: odc.\d+)|(\d+: odc.\d+)|(\d+ odc.\d+)|(:)|( -(.*?).*)|(,)|!", "", evnt).rstrip().lower()
						rating_json = "{}xtraEvent/infos/{}.json".format(pathLoc, evntNm)

						if fileExists(rating_json):
							with open(rating_json) as f:
								prate = json.load(f)['Rated']

							if prate == "TV-Y7":
								rate = "6"
							elif prate == "TV-14":
								rate = "12"
							elif prate == "TV-PG":
								rate = "16"
							elif prate == "TV-G":
								rate = "0"
							elif prate == "TV-MA":
								rate = "18"
							elif prate == "PG-13":
								rate = "16"
							elif prate == "R":
								rate = "18"
							elif prate == "G":
								rate = "0"
							else:
								pass
							if rate:	
								parentName = str(rate)

					if parentName:
						rateNm = pratePath + "FSK_{}.png".format(parentName)
						self.instance.setPixmap(loadPNG(rateNm))
						self.instance.show()
					else:
						self.instance.hide()
				except:
					self.instance.hide()
			return			
					