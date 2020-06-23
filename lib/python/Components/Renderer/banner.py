# -*- coding: utf-8 -*-
# by digiteng...03.2020
#v2...03.2020
# <widget source="session.Event_Now" render="banner" position="0,0" size="758,140" zPosition="1" />
from Renderer import Renderer
from enigma import ePixmap, ePicLoad, eTimer
from Components.AVSwitch import AVSwitch
from Components.Pixmap import Pixmap
from Components.config import config
import json
import re
import os
import urllib2

try:
	if config.plugins.blackpanel.apitmdb.value != "":
		tmdb_api = config.plugins.blackpanel.apitmdb.value
	else:
		tmdb_api = "8fedefb08d7138abbb6d19ff66c9170c"
except:
	tmdb_api = "8fedefb08d7138abbb6d19ff66c9170c"

if os.path.isdir("/media/usb"):
	path_folder = "/media/usb/banner/"
else:
	path_folder = "/media/hdd/banner/"

try:
	folder_size=sum([sum(map(lambda fname: os.path.getsize(os.path.join(path_folder, fname)), files)) for path_folder, folders, files in os.walk(path_folder)])
	banners_sz = ".format0.f".format (folder_size/(1024*1024.0))
	if banners_sz >= "10":    # folder remove size(10MB)...
		import shutil
		shutil.rmtree(path_folder)
except:
	pass

class banner(Renderer):

	def __init__(self):
		Renderer.__init__(self)
		self.bannerName = ''
		self.event = ''

	GUI_WIDGET = ePixmap
	def changed(self, what):
		try:
			if not self.instance:
				return
			self.event = self.source.event
			if what[0] == self.CHANGED_CLEAR:
				self.instance.hide()
			if what[0] != self.CHANGED_CLEAR:
				if self.event:
					evnt = self.event.getEventName()
					try:
						filterNm = re.sub("([\(\[]).*?([\)\]])|(: odc.\d+)", " ", evnt)
						evntNm = filterNm
					except:
						evntNm = evnt
					self.dwn_banner = path_folder + "{}_banner.jpg".format(evntNm)
					bannerName = path_folder + evntNm + "_banner.jpg"
					self.evntNm = urllib2.quote(evntNm)
					if os.path.exists(bannerName):
						try:
							size = self.instance.size()
							self.picload = ePicLoad()
							sc = AVSwitch().getFramebufferScale()
							if self.picload:
								self.picload.setPara((size.width(),
								size.height(),
								sc[0],
								sc[1],
								False,
								1,
								'#00000000'))
							result = self.picload.startDecode(bannerName, 0, 0, False)
							if result == 0:
								ptr = self.picload.getData()
								if ptr != None:
									self.instance.setPixmap(ptr)
									self.instance.show()
						except:
							self.instance.hide()
					else:
						self.delay()
						self.instance.hide()
				else:
					self.instance.hide()
					return
		except:
			return

	def downloadBanner(self):
		year = self.year()
		try:
			url_tvdb = "https://thetvdb.com/api/GetSeries.php?seriesname={}".format(self.evntNm)
			if year:
				url_tvdb += "&primary_release_year={}&year={}".format(year, year)
			url_read = urllib2.urlopen(url_tvdb).read()
			series_id = re.findall('<seriesid>(.*?)</seriesid>', url_read, re.I)[0]
			if series_id:
				try:
					self.url_banner = "https://artworks.thetvdb.com/banners/graphical/{}-g.jpg".format(series_id)
					if self.url_banner:
						self.saveBanner()
				except:
					try:
						url_tvdb = "https://thetvdb.com/api/a99d487bb3426e5f3a60dea6d3d3c7ef/series/{}/bnnr.xml".format(series_id)
						url_read = urlopen(url_tvdb).read()
						banner = re.findall('<banner>(.*?)</banner>', url_read)[0]
						self.url_banner = "https://artworks.thetvdb.com/banners/{}".format(banner)
						self.saveBanner()
					except:
						try:
							url_tmdb = "https://api.themoviedb.org/3/search/multi?api_key={}&query={}".format( tmdb_api, quote(self.evntNm))
							if len(year) > 0:
								url_tmdb += "&primary_release_year={}&year={}".format(year, year)
							jp = json.load(urllib2.urlopen(url_tmdb))
							tmdb_id = (jp['results'][0]['id'])
							if tmdb_id:
								m_type = (jp['results'][0]['media_type'])
								if m_type == "movie":
									m_type = (jp['results'][0]['media_type']) + "s"
								else:
									mm_type = m_type
								url_fanart = "https://webservice.fanart.tv/v3/{}/{}?api_key=6d231536dea4318a88cb2520ce89473b".format(m_type, tmdb_id)
								fjs = json.load(urllib2.urlopen(url_fanart))
								if fjs:
									if m_type == "movies":
										mm_type = (jp['results'][0]['media_type'])
									self.url_banner = (fjs[mm_type+'banner'][0]['url'])
									if self.url_banner:
										self.saveBanner()
						except:
							try:
								url_maze = "http://api.tvmaze.com/singlesearch/shows?q={}".format(self.evntNm)
								mj = json.load(urllib2.urlopen(url_maze))
								poster = (mj['externals']['thetvdb'])
								if poster:
									url_tvdb = "https://thetvdb.com/api/GetSeries.php?seriesname={}".format(poster)
									url_read = urllib2.urlopen(url_tvdb).read()
									series_id = re.findall('<seriesid>(.*?)</seriesid>', url_read, re.I)[0]
									banner_img = re.findall('<banner>(.*?)</banner>', url_read, re.I)[0]
									if banner_img:
										self.url_banner = "https://artworks.thetvdb.com{}".format(banner_img)
										self.saveBanner()
									if series_id:
										try:
											url_fanart = "https://webservice.fanart.tv/v3/{}/{}?api_key=6d231536dea4318a88cb2520ce89473b".format(m_type, series_id)
											fjs = json.load(urllib2.urlopen(url_fanart))
											if fjs:
												if m_type == "movies":
													mm_type = (jp['results'][0]['media_type'])
												else:
													mm_type = m_type
												self.url_banner = (fjs[mm_type+'banner'][0]['url'])
												if self.url_banner:
													self.saveBanner()
										except:
											return
							except:
								return
		except:
			return

	def year(self):
		try:
			sd = self.event.getShortDescription() + "\n" + self.event.getExtendedDescription()
			pattern = ["(19[0-9][0-9])","(20[0-9][0-9])"]
			for i in pattern:
				yr = re.search(i, sd)
				if yr:
					jr = yr.group(1)
					return "{}".format(jr)
			return ""
		except:
			return

	def delay(self):
		self.timer = eTimer()
		self.timer.callback.append(self.downloadBanner)
		self.timer.start(60, True)

	def saveBanner(self):
		if not os.path.isdir(path_folder):
			os.makedirs(path_folder)
		with open(self.dwn_banner,'wb') as f:
			f.write(urllib2.urlopen(self.url_banner).read())
			f.close()
