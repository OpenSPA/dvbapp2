# -*- coding: utf-8 -*-
# by digiteng...11.2020

# <widget source="session.Event_Now" render="Label" position="50,545" size="930,400" font="Regular; 32" halign="left" transparent="1" zPosition="2" backgroundColor="back_color" valign="center">
  	# <convert type="xtraInfo2">id,Network,Description</convert>
# </widget>

from Components.Converter.Converter import Converter
from Components.Element import cached
from Components.config import config
from Tools.Directories import fileExists
import re

try:
	pathLoc = config.plugins.xtraEvent.loc.value
except:
	pass

class xtraInfo2(Converter, object):

	id = "id"
	Network = "Network"
	Airs_DayOfWeek = "Airs_DayOfWeek"
	Airs_Time = "Airs_Time"
	ContentRating = "ContentRating" # parental rating
	Genre = "Genre"
	FirstAired = "FirstAired"
	IMDB_ID = "IMDB_ID"
	Network = "Network"
	Overview = "Description"
	Rating = "Rating"
	SeriesID = "SeriesID"
	Status = "Status"
	SeriesName = "SeriesName"
	banner = "banner"
	fanart = "fanart"
	poster = "poster"

	def __init__(self, type):
		Converter.__init__(self, type)
		self.types = str(type).split(",")

	@cached
	def getText(self):
		event = self.source.event
		if event:
			if self.types:
				evnt = event.getEventName()
				evntNm = re.sub("([\(\[]).*?([\)\]])|(: odc.\d+)|(\d+: odc.\d+)|(\d+ odc.\d+)|(:)|( -(.*?).*)|(,)|!", "", evnt).rstrip()
				info_xml = "{}xtraEvent/infos/{}.xml".format(pathLoc, evntNm)
				if fileExists(info_xml):
					with open(info_xml) as f:
						r = f.read()
					evnt = []
					try:
						for type in self.types:
							type.strip()

							if type == self.id:
								id = re.findall('<id>(.*?)</id>', r)[0]
								if id:
									evnt.append("id : {}".format(id))
							elif type == self.Network:
								ntwrk = re.findall('<Network>(.*?)</Network>', r)[0]
								if ntwrk:
									evnt.append("Network : {}".format(ntwrk))
							elif type == self.Airs_DayOfWeek:
								Airs_DayOfWeek = re.findall('<Airs_DayOfWeek>(.*?)</Airs_DayOfWeek>', r)[0]
								if Airs_DayOfWeek:
									evnt.append("Airs_Day : {}".format(Airs_DayOfWeek))
							elif type == self.Airs_Time:
								Airs_Time = re.findall('<Airs_Time>(.*?)</Airs_Time>', r)[0]
								if Airs_Time:
									evnt.append("Airs_Time : {}".format(Airs_Time))
							elif type == self.ContentRating:
								ContentRating = re.findall('<ContentRating>(.*?)</ContentRating>', r)[0]
								if ContentRating:
									evnt.append("Rated : {}".format(ContentRating))
							elif type == self.Genre:
								Genre = re.findall('<Genre>(.*?)</Genre>', r)[0]
								if Genre:
									evnt.append("Genre : {}".format(Genre))
							elif type == self.FirstAired:
								FirstAired = re.findall('<FirstAired>(.*?)</FirstAired>', r)[0]
								if FirstAired:
									evnt.append("FirstAired : {}".format(FirstAired))
							elif type == self.IMDB_ID:
								IMDB_ID = re.findall('<IMDB_ID>(.*?)</IMDB_ID>', r)[0]
								if IMDB_ID:
									evnt.append("IMDB_ID : {}".format(IMDB_ID))
							elif type == self.Overview:
								Overview = re.findall('<Overview>(.*?)</Overview>', r)[0]
								if Overview:
									evnt.append("Description : {}".format(Overview))
							elif type == self.Rating:
								Rating = re.findall('<Rating>(.*?)</Rating>', r)[0]
								if Rating:
									evnt.append("Rating : {}".format(Rating))
							elif type == self.SeriesID:
								SeriesID = re.findall('<SeriesID>(.*?)</SeriesID>', r)[0]
								if SeriesID:
									evnt.append("SeriesID : {}".format(SeriesID))
							elif type == self.Status:
								Status = re.findall('<Status>(.*?)</Status>', r)[0]
								if Status:
									evnt.append("Status : {}".format(Status))
							elif type == self.SeriesName:
								SeriesName = re.findall('<SeriesName>(.*?)</SeriesName>', r)[0]
								if SeriesName:
									evnt.append("Name : {}".format(SeriesName))
							elif type == self.banner:
								banner = re.findall('<banner>(.*?)</banner>', r)[0]
								if banner:
									evnt.append("banner : {}".format(banner))
							elif type == self.fanart:
								fanart = re.findall('<fanart>(.*?)</fanart>', r)[0]
								if fanart:
									evnt.append("fanart : {}".format(fanart))
							elif type == self.poster:
								poster = re.findall('<poster>(.*?)</poster>', r)[0]
								if poster:
									evnt.append("poster : {}".format(poster))
							else:
								return ""

						return "\n".join(evnt)
					except:
						pass
		else:
			return ""
	text = property(getText)
