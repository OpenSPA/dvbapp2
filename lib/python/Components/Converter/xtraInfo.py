# -*- coding: utf-8 -*-
# by digiteng...07.2020

# <widget source="session.Event_Now" render="Label" position="50,545" size="930,400" font="Regular; 32" halign="left" transparent="1" zPosition="2" backgroundColor="back_color" valign="center">
  	# <convert type="xtraInfo">Title,Year,Description</convert>
# </widget>

from Components.Converter.Converter import Converter
from Components.Element import cached
from Components.config import config
from Tools.Directories import fileExists
import re
import json


try:
	from Plugins.Extensions.xtraEvent.xtra import xtra
	pathLoc = config.plugins.xtraEvent.loc.value
except:
	pathLoc = "/media/hdd/"


class xtraInfo(Converter, object):

	Title = "Title"
	Year = "Year"
	Rated = "Rated"
	Released = "Released"
	Runtime = "Runtime"
	Genre = "Genre"
	Director = "Director"
	Writer = "Writer"
	Actors = "Actors"
	Plot = "Description"
	Language = "Language"
	Country = "Country"
	Awards = "Awards"
	imdbRating = "imdbRating"
	imdbVotes = "imdbVotes"
	Type = "Type"
	totalSeasons = "totalSeasons"


	def __init__(self, type):
		Converter.__init__(self, type)
		self.types = str(type).split(",")

	@cached
	def getText(self):
		event = self.source.event
		if event:
			if self.types:
				evnt = event.getEventName()
				evntNm = re.sub("([\(\[]).*?([\)\]])|(: odc.\d+)|(\d+: odc.\d+)|(\d+ odc.\d+)|(:)|( -(.*?).*)|(,)|!", "", evnt).rstrip().lower()
				rating_json = "{}xtraEvent/infos/{}.json".format(pathLoc, evntNm)
				if fileExists(rating_json):
					with open(rating_json) as f:
						read_json = json.load(f)
					evnt = []
					try:
						for type in self.types:
							type.strip()
							if read_json["Response"] == "True":
								
								if type == self.Title:
									title = read_json['Title']
									if title:
										evnt.append("Title : {}".format(title))
								elif type == self.Year:
									year = read_json["Year"]
									if year:
										evnt.append("Year : {}".format(year))
								elif type == self.Rated:
									Rated = read_json["Rated"]
									if Rated:
										evnt.append("Rated : {}".format(Rated))
								elif type == self.Released:
									Released = read_json["Released"]
									if Released:
										evnt.append("Released : {}".format(Released))
								elif type == self.Runtime:
									Runtime = read_json["Runtime"]
									if Runtime:
										evnt.append("Runtime : {}".format(Runtime))
								elif type == self.Genre:
									Genre = read_json["Genre"]
									if Genre:
										evnt.append("Genre : {}".format(Genre))
								elif type == self.Director:
									Director = read_json["Director"]
									if Director:
										evnt.append("Director : {}".format(Director))
								elif type == self.Writer:
									Writer = read_json["Writer"]
									if Writer:
										evnt.append("Writer : {}".format(Writer))
								elif type == self.Actors:
									Actors = read_json["Actors"]
									if Actors:
										evnt.append("Actors : {}".format(Actors))
								elif type == self.Plot:
									Plot = read_json["Plot"]
									if Plot:
										evnt.append("Description : {}".format(Plot))
								elif type == self.Language:
									Language = read_json["Language"]
									if Language:
										evnt.append("Language : {}".format(Language))
								elif type == self.Country:
									Country = read_json["Country"]
									if Country:
										evnt.append("Country : {}".format(Country))
								elif type == self.Awards:
									Awards = read_json["Awards"]
									if Awards:
										evnt.append("Awards : {}".format(Awards))
								elif type == self.imdbRating:
									imdbRating = read_json["imdbRating"]
									if imdbRating:
										evnt.append("imdb : {}".format(imdbRating))
								elif type == self.imdbVotes:
									imdbVotes = read_json["imdbVotes"]
									if imdbVotes:
										evnt.append("imdbVotes : {}".format(imdbVotes))
								elif type == self.Type:
									Type = read_json["Type"]
									if Type:
										evnt.append("Type : {}".format(Type))
								elif type == self.totalSeasons:
									totalSeasons = read_json["totalSeasons"]
									if totalSeasons:
										evnt.append("totalSeasons : {}".format(totalSeasons))

								else:
									return ""

						return "\n".join(evnt)
					except:
						return ""
		else:
			return ""
	text = property(getText)
