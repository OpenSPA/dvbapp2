# -*- coding: utf-8 -*-
# by digiteng...12-2019
#  <widget source="session.Event_Now" render="Label" position="50,545" size="930,40" font="Regular; 32" halign="left" transparent="1" zPosition="2" backgroundColor="back_color" valign="center">
#   	<convert type="FroidEvent">SESSION_EPISODE,RATING,YEAR,GENRE</convert>
# </widget>
from Components.Converter.Converter import Converter
from Components.Element import cached
from Components.Converter.genre import getGenreStringSub
import re

class FroidEvent(Converter, object):

	def __init__(self, type):
		Converter.__init__(self, type)
		self.tip = str(type).split(",")

	@cached
	def getText(self):
		event = self.source.event
		evnt = []
		try:
			for type in self.tip: 
				type.strip()
 				if type == "SESSION_EPISODE":
					ses_ep = self.sessionEpisode(event)
					if ses_ep != "" and len(ses_ep) > 0:
						evnt.append(ses_ep)

				elif type == "RATING":
					rating = event.getParentalData()
					if rating:
						rtng = rating.getRating()
						if rtng > 0:
							evnt.append("%d+"%rtng)

				elif type == "YEAR":
					year = self.yearPr(event)
					if len(year) > 0:
						evnt.append("%s"%year)

				elif type == "GENRE":
					genre = event.getGenreData()
					if not genre is None:
						gnr = getGenreStringSub(genre.getLevel1(), genre.getLevel2())
						if len(gnr) > 0:
							evnt.append("%s"%gnr)

			return " • ".join(evnt)
		except:
			return ""

	text = property(getText)

	def sessionEpisode(self, event):
		fd = event.getShortDescription() + "\n" + event.getExtendedDescription()
		pattern = ["(\d+). Staffel, Folge (\d+)", "T(\d+) Ep.(\d+)", "'Episodio (\d+)' T(\d+)"]
		for i in pattern:
			seg = re.search(i, fd)
			if seg:
				if re.search("Episodio",i):
					return "S"+seg.group(2).zfill(2)+"E"+seg.group(1).zfill(2)
				else :
					return "S"+seg.group(1).zfill(2)+"E"+seg.group(2).zfill(2)
		return ""

	def yearPr(self, event):
		fd = event.getShortDescription() + "\n" + event.getExtendedDescription()
		open("/tmp/evnt.txt", "w").write(fd)
		pattern = [".*[A-Z][A-Z]*\s(\d+)+", "\([+][0-9]+\)\s((\d+)(\d+)+)"]
		for i in pattern:
			yr = re.search(i, fd)
			if yr:
				jr = yr.group()
				return "%s"%jr
		return ""
