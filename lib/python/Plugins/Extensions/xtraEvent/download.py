# -*- coding: utf-8 -*-
# by digiteng...06.2020, 11.2020
from Components.AVSwitch import AVSwitch
from Screens.Screen import Screen
from Components.Pixmap import Pixmap
from Components.Label import Label
from Components.ActionMap import ActionMap
from enigma import eEPGCache, eTimer, getDesktop, ePixmap
from Components.config import config
from ServiceReference import ServiceReference
from Screens.MessageBox import MessageBox
import Tools.Notifications
import requests
from requests.utils import quote
import os, re, random, json
from PIL import Image
# import socket
import xtra
from datetime import datetime
import threading
from Components.ProgressBar import ProgressBar

if config.plugins.xtraEvent.tmdbAPI.value != "":
	tmdb_api = config.plugins.xtraEvent.tmdbAPI.value
else:
	tmdb_api = "3c3efcf47c3577558812bb9d64019d65"
if config.plugins.xtraEvent.tvdbAPI.value != "":
	tvdb_api = config.plugins.xtraEvent.tvdbAPI.value
else:
	tvdb_api = "a99d487bb3426e5f3a60dea6d3d3c7ef"
if config.plugins.xtraEvent.fanartAPI.value != "":
	fanart_api = config.plugins.xtraEvent.fanartAPI.value
else:
	fanart_api = "6d231536dea4318a88cb2520ce89473b"
if config.plugins.xtraEvent.omdbAPI.value != "":
	omdb_api = config.plugins.xtraEvent.omdbAPI.value
else:
	omdb_apis = ["6a4c9432", "a8834925", "550a7c40", "8ec53e6b"]
	omdb_api = random.choice(omdb_apis)
	
epgcache = eEPGCache.getInstance()
pathLoc = config.plugins.xtraEvent.loc.value + "xtraEvent/"
desktop_size = getDesktop(0).size().width()

class downloads(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		skin = None
		if desktop_size <= 1280:
			if config.plugins.xtraEvent.skinSelect.value == "default":
				skin = "/usr/lib/enigma2/python/Plugins/Extensions/xtraEvent/skins/downloads_720_default.xml"
			elif config.plugins.xtraEvent.skinSelect.value == "skin_2":
				skin = "/usr/lib/enigma2/python/Plugins/Extensions/xtraEvent/skins/downloads_720_2.xml"
			elif config.plugins.xtraEvent.skinSelect.value == "skin_3":
				skin = "/usr/lib/enigma2/python/Plugins/Extensions/xtraEvent/skins/downloads_720_3.xml"
		else:
			if config.plugins.xtraEvent.skinSelect.value == "default":
				skin = "/usr/lib/enigma2/python/Plugins/Extensions/xtraEvent/skins/downloads_1080_default.xml"
			elif config.plugins.xtraEvent.skinSelect.value == "skin_2":
				skin = "/usr/lib/enigma2/python/Plugins/Extensions/xtraEvent/skins/downloads_1080_2.xml"
			elif config.plugins.xtraEvent.skinSelect.value == "skin_3":
				skin = "/usr/lib/enigma2/python/Plugins/Extensions/xtraEvent/skins/downloads_1080_3.xml"
		with open(skin, 'r') as f:
			self.skin = f.read()
		self.titles = ""
		self['status'] = Label()
		self['info'] = Label()
		self['info2'] = Label()
		self['key_red'] = Label(_('Close'))
		self['key_green'] = Label(_('Download'))
		# self['key_yellow'] = Label(_('Download'))
		# self['key_blue'] = Label(_('Manuel Search'))
		self['actions'] = ActionMap(['SetupActions', 'ColorActions'], {'cancel': self.close, 'red': self.close, 'ok':self.save,'green':self.save}, -2)
		
		self['progress'] = ProgressBar()
		self['progress'].setRange((0, 100))
		self['progress'].setValue(0)

	def save(self):
		if config.plugins.xtraEvent.searchMOD.value == "Current Channel":
			self.currentChEpgs()
		if config.plugins.xtraEvent.searchMOD.value == "Bouquets":
			self.selBouquets()
			
	def currentChEpgs(self):
		events = None
		import NavigationInstance
		ref = NavigationInstance.instance.getCurrentlyPlayingServiceReference().toString()
		try:
			events = epgcache.lookupEvent(['IBDCTSERNX', (ref, 1, -1, -1)])
			if config.plugins.xtraEvent.searchNUMBER.value == "all epg":
				n = len(events)
				titles = []
				for i in range(int(n)):
					title = events[i][4]
					evntNm = re.sub("([\(\[]).*?([\)\]])|(: odc.\d+)|(\d+: odc.\d+)|(\d+ odc.\d+)|(:)|( -(.*?).*)|(,)|!", "", title).rstrip()
					titles.append(str(evntNm))
				self.titles = list(dict.fromkeys(titles))
				self.download()
			else:
				n = config.plugins.xtraEvent.searchNUMBER.value
				titles = []
				for i in range(int(n)):
					title = events[i][4]
					evntNm = re.sub("([\(\[]).*?([\)\]])|(: odc.\d+)|(\d+: odc.\d+)|(\d+ odc.\d+)|(:)|( -(.*?).*)|(,)|!", "", title).rstrip()
					titles.append(str(evntNm))
				self.titles = list(dict.fromkeys(titles))
				# threading.Thread(target=self.down, daemon=True).start()
				self.download()
		except:
			pass

	def selBouquets(self):
		if os.path.exists(pathLoc + "bqts"):
			with open(pathLoc + "bqts", "r") as f:
				refs = f.readlines()
			nl = len(refs)
			eventlist=[]
			for i in range(nl):
				ref = refs[i]
				try:
					events = epgcache.lookupEvent(['IBDCTSERNX', (ref, 1, -1, -1)])
					n = config.plugins.xtraEvent.searchNUMBER.value
					for i in range(int(n)):
						title = events[i][4]
						evntNm = re.sub("([\(\[]).*?([\)\]])|(: odc.\d+)|(\d+: odc.\d+)|(\d+ odc.\d+)|(:)|( -(.*?).*)|(,)|!", "", title).rstrip()
						eventlist.append(evntNm)
				except:
					pass
			self.titles = list(dict.fromkeys(eventlist))
			self.download()
			
	def intCheck(self):
		try:
			socket.setdefaulttimeout(5)
			socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
			return True
		except:
			return False
			
	def download(self):
		threading.Thread(target=self.down).start()

####################################################
	def down(self):
		self['progress'].setValue(0)
		now = datetime.now()
		dt = now.strftime("%d/%m/%Y %H:%M:%S")
		with open("/tmp/up_report", "a+") as f:
			f.write(str("\n\nstart : {}\n".format(dt)))
		try:
			tmdb_poster_downloaded = 0
			tvdb_poster_downloaded = 0
			maze_poster_downloaded = 0
			fanart_poster_downloaded = 0
			tmdb_backdrop_downloaded = 0
			tvdb_backdrop_downloaded = 0
			fanart_backdrop_downloaded = 0
			banner_downloaded = 0
			extra_downloaded = 0
			extra2_downloaded = 0
			info_downloaded = 0
			title = ""
			n = len(self.titles)
			for i in range(n):
				title = self.titles[i]
				title = title.strip()

				if config.plugins.xtraEvent.poster.value == True:
					dwnldFile = pathLoc + "poster/{}.jpg".format(title)
# tmdb_Poster() #################################################################
					if config.plugins.xtraEvent.tmdb.value == True:
						if not os.path.exists(dwnldFile):
							srch = "multi"
							lang = config.plugins.xtraEvent.searchLang.value
							url_tmdb = "https://api.themoviedb.org/3/search/{}?api_key={}&query={}&language={}".format(srch, tmdb_api, quote(title), lang)
							try:
								poster = ""
								poster = requests.get(url_tmdb).json()['results'][0]['poster_path']
								p_size = config.plugins.xtraEvent.TMDBpostersize.value
								url = "https://image.tmdb.org/t/p/{}{}".format(p_size, poster)
								if poster != "":
									open(dwnldFile, 'wb').write(requests.get(url, stream=True, allow_redirects=True).content)
									tmdb_poster_downloaded += 1
									downloaded = tmdb_poster_downloaded
									self.prgrs(downloaded, n)
									self['info'].setText(_("{} poster downloaded from TMDB...".format(title.upper())))
									self.brokenImageRemove()
							except:
								pass
# tvdb_Poster() #################################################################								
					if config.plugins.xtraEvent.tvdb.value == True:
						if not os.path.exists(dwnldFile):
							try:
								url_tvdb = "https://thetvdb.com/api/GetSeries.php?seriesname={}".format(quote(title))
								url_read = requests.get(url_tvdb).text
								series_id = re.findall('<seriesid>(.*?)</seriesid>', url_read)[0]
								if series_id:
									url_tvdb = "https://thetvdb.com/api/{}/series/{}/en".format(tvdb_api, series_id)
									url_read = requests.get(url_tvdb).text
									poster = re.findall('<poster>(.*?)</poster>', url_read)[0]
									url = "https://artworks.thetvdb.com/banners/{}".format(poster)
									if config.plugins.xtraEvent.TVDBpostersize.value == "thumbnail":
										url = url.replace(".jpg", "_t.jpg")
									open(dwnldFile, 'wb').write(requests.get(url, stream=True, allow_redirects=True).content)
									tvdb_poster_downloaded += 1
									downloaded = tvdb_poster_downloaded
									self.prgrs(downloaded, n)
									self['info'].setText(_("{} poster downloaded from TVDB...".format(title.upper())))
									self.brokenImageRemove()
							except:
								pass
# maze_Poster() #################################################################								
					if config.plugins.xtraEvent.maze.value == True:
						if not os.path.exists(dwnldFile):		
							url_maze = "http://api.tvmaze.com/search/shows?q={}".format(quote(title))
							try:
								url = requests.get(url_maze).json()[0]['show']['image']['medium']
								open(dwnldFile, 'wb').write(requests.get(url, stream=True, allow_redirects=True).content)
								maze_poster_downloaded += 1
								downloaded = maze_poster_downloaded
								self.prgrs(downloaded, n)
								self['info'].setText(_("{} poster downloaded from MAZE...".format(title.upper())))
								self.brokenImageRemove()
							except:
								pass
# fanart_Poster() #################################################################								
					if config.plugins.xtraEvent.fanart.value == True:
						if not os.path.exists(dwnldFile):				
							try:
								srch = "multi"
								url_tmdb = "https://api.themoviedb.org/3/search/{}?api_key={}&query={}".format(srch, tmdb_api, quote(title))
								bnnr = requests.get(url_tmdb).json()
								tmdb_id = (bnnr['results'][0]['id'])
								if tmdb_id:
									m_type = (bnnr['results'][0]['media_type'])
									if m_type == "movie":
										m_type = (bnnr['results'][0]['media_type']) + "s"
									else:
										mm_type = m_type
									url_maze = "http://api.tvmaze.com/singlesearch/shows?q={}".formatquote(title)
									mj = requests.get(url_maze).json()
									tvdb_id = (mj['externals']['thetvdb'])
									if tvdb_id:
										try:
											url_fanart = "https://webservice.fanart.tv/v3/{}/{}?api_key={}".format(m_type, tvdb_id, tvdb_api)
											fjs = requests.get(url_fanart).json()
											if fjs:
												if m_type == "movies":
													mm_type = (bnnr['results'][0]['media_type'])
												else:
													mm_type = m_type
												url = (fjs['tvposter'][0]['url'])
												if url:
													w = open(dwnldFile, 'wb').write(requests.get(url, stream=True, allow_redirects=True).content)
													fanart_poster_downloaded += 1
													downloaded = fanart_poster_downloaded
													self.prgrs(downloaded, n)
													self['info'].setText(_("{} poster downloaded from FANART...".format(title.upper())))
													self.brokenImageRemove()
													
													scl = 1
													im = Image.open(dwnldFile)
													scl = config.plugins.xtraEvent.FANARTresize.value
													im1 = im.resize((im.size[0] // int(scl), im.size[1] // int(scl)), Image.ANTIALIAS)
													im1.save(dwnldFile)
										except:
											pass
							except:
								pass
# banner() #################################################################	
				if config.plugins.xtraEvent.banner.value == True:
					dwnldFile = pathLoc + "banner/{}.jpg".format(title)
					if not os.path.exists(dwnldFile):
						try:
							url = "https://api.themoviedb.org/3/search/multi?api_key={}&query={}".format(tmdb_api, quote(title))
							jp = requests.get(url).json()
							tmdb_id = (jp['results'][0]['id'])
							if tmdb_id:
								m_type = (jp['results'][0]['media_type'])
								if m_type == "movie":
									m_type = (jp['results'][0]['media_type']) + "s"
								else:
									mm_type = m_type
								print m_type
								if m_type == "movies":
									url = "https://webservice.fanart.tv/v3/{}/{}?api_key={}".format(m_type, tvdb_id, fanart_api)
									
									fjs = requests.get(url).json()
									url = fjs["moviebanner"][0]["url"]
									if url:
										open(dwnldFile, 'wb').write(requests.get(url, stream=True, allow_redirects=True).content)
										banner_downloaded += 1
										downloaded = banner_downloaded
										self.prgrs(downloaded, n)
										self['info'].setText(_("{}, banner downloaded from FANART...".format(title.upper())))
										self.brokenImageRemove()
								else:
									try:
										url_maze = "http://api.tvmaze.com/singlesearch/shows?q={}".format(quote(title))
										mj = requests.get(url_maze).json()
										tvdb_id = (mj['externals']['thetvdb'])
										if tvdb_id:
											url = "https://webservice.fanart.tv/v3/{}/{}?api_key={}".format(m_type, tvdb_id, fanart_api)
											fjs = requests.get(url).json()
											url = fjs["tvbanner"][0]["url"]
											if url:
												open(dwnldFile, 'wb').write(requests.get(url, stream=True, allow_redirects=True).content)
												banner_downloaded += 1
												downloaded = banner_downloaded
												self.prgrs(downloaded, n)
												self['info'].setText(_("{}, banner downloaded from FANART...".format(title.upper())))
												self.brokenImageRemove()
									except:
										pass
						except:
							pass
# backdrop() #################################################################

				if config.plugins.xtraEvent.backdrop.value == True:
					if config.plugins.xtraEvent.extra.value == True:
						dwnldFile = "{}backdrop/{}.jpg".format(pathLoc, title)
						if not os.path.exists(dwnldFile):
							url = "http://capi.tvmovie.de/v1/broadcasts/search?q={}&page=1&rows=1".format(title.replace(" ", "+"))
							try:
								url = requests.get(url).json()['results'][0]['images'][0]['filepath']['android-image-320-180']
							except:
								pass
							open(dwnldFile, 'wb').write(requests.get(url, stream=True, allow_redirects=True).content)
							extra_downloaded += 1
							downloaded = extra_downloaded
							self.prgrs(downloaded, n)
							self['info'].setText(_("{}, backdrop downloaded from EXTRA...".format(title.upper())))
							self.brokenImageRemove()
					if config.plugins.xtraEvent.tmdb.value == True:
						dwnldFile = pathLoc + "backdrop/{}.jpg".format(title)
						if not os.path.exists(dwnldFile):				
							srch = "multi"
							lang = config.plugins.xtraEvent.searchLang.value
							url_tmdb = "https://api.themoviedb.org/3/search/{}?api_key={}&query={}&language={}".format(srch, tmdb_api, quote(title), lang)
							try:
								backdrop = requests.get(url_tmdb).json()['results'][0]['backdrop_path']
								if backdrop:
									backdrop_size = config.plugins.xtraEvent.TMDBbackdropsize.value
									url = "https://image.tmdb.org/t/p/{}{}".format(backdrop_size, backdrop)
									open(dwnldFile, 'wb').write(requests.get(url, stream=True, allow_redirects=True).content)
									tmdb_backdrop_downloaded += 1
									downloaded = tmdb_backdrop_downloaded
									self.prgrs(downloaded, n)
									self['info'].setText(_("{}, backdrop downloaded from TMDB...".format(title.upper())))
									self.brokenImageRemove()
								else:
									self['info'].setText(str("TMDB backdrop : exists "+title))
							except:
								pass

					if config.plugins.xtraEvent.tvdb.value == True:
						dwnldFile = pathLoc + "backdrop/{}.jpg".format(title)
						if not os.path.exists(dwnldFile):
							try:
								url_tvdb = "https://thetvdb.com/api/GetSeries.php?seriesname={}".format(quote(title))
								url_read = requests.get(url_tvdb).text
								series_id = re.findall('<seriesid>(.*?)</seriesid>', url_read)[0]
								if series_id:
									lang = config.plugins.xtraEvent.searchLang.value
									url_tvdb = "https://thetvdb.com/api/{}/series/{}/{}.xml".format(tvdb_api, series_id, lang)
									url_read = requests.get(url_tvdb).text
									backdrop = re.findall('<fanart>(.*?)</fanart>', url_read)[0]
									if backdrop:
										url = "https://artworks.thetvdb.com/banners/{}".format(backdrop)
										if config.plugins.xtraEvent.TVDBbackdropsize.value == "thumbnail":
											url = url.replace(".jpg", "_t.jpg")
										open(dwnldFile, 'wb').write(requests.get(url, stream=True, allow_redirects=True).content)
										tvdb_backdrop_downloaded += 1
										downloaded = tvdb_backdrop_downloaded
										self.prgrs(downloaded, n)
										self['info'].setText(_("{}, backdrop downloaded from TVDB...".format(title.upper())))
										self.brokenImageRemove()
							except:
								pass
					if config.plugins.xtraEvent.fanart.value == True:
						dwnldFile = pathLoc + "backdrop/{}.jpg".format(title)
						if not os.path.exists(dwnldFile):				
							try:
								srch = "multi"
								url = "https://api.themoviedb.org/3/search/{}?api_key={}&query={}".format(srch, tmdb_api, quote(title))
								bckdrp = requests.get(url).json()
								tmdb_id = (bckdrp['results'][0]['id'])
								if tmdb_id:
									m_type = (bckdrp['results'][0]['media_type'])
									if m_type == "movie":
										m_type = (bckdrp['results'][0]['media_type']) + "s"
									else:
										mm_type = m_type
									url = "http://api.tvmaze.com/singlesearch/shows?q={}".format(quote(title))
									bckdrp = requests.get(url).json()
									tvdb_id = (bckdrp['externals']['thetvdb'])
									if tvdb_id:
										try:
											url = "https://webservice.fanart.tv/v3/{}/{}?api_key={}".format(m_type, tvdb_id, fanart_api)
											bckdrp = requests.get(url).json()
											if bckdrp:
												if m_type == "movie":
													url = (bckdrp['moviethumb'][0]['url'])
												else:
													url = (bckdrp['tvthumb'][0]['url'])
												if url:
													open(dwnldFile, 'wb').write(requests.get(url, stream=True, allow_redirects=True).content)
													fanart_backdrop_downloaded += 1
													downloaded = fanart_backdrop_downloaded
													self.prgrs(downloaded, n)
													self['info'].setText(_("{}, backdrop downloaded from FANART...".format(title.upper())))
													self.brokenImageRemove()
													
													scl = config.plugins.xtraEvent.FANART_Backdrop_Resize.value
													im = Image.open(dwnldFile)
													scl = config.plugins.xtraEvent.FANART_Backdrop_Resize.value
													im1 = im.resize((im.size[0] // int(scl), im.size[1] // int(scl)), Image.ANTIALIAS)
													im1.save(dwnldFile)
										except:
											pass
							except:
								pass

					if config.plugins.xtraEvent.extra2.value == True:
						dwnldFile = "{}backdrop/{}.jpg".format(pathLoc, title)
						if not os.path.exists(dwnldFile):
							# try:
								# url="https://www.bing.com/search?q={}+poster+jpg".format(title.replace(" ", "+"))
								# headers = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"}
								# ff = requests.get(url, stream=True, headers=headers).text
								# p='ihk=\"\/th\?id=(.*?)&'
								# f= re.findall(p, ff)
								# url = "https://www.bing.com/th?id="+f[0]
							# except:
								# pass
							try:
								url = "https://www.google.com/search?q={}&tbm=isch&tbs=sbd:0".format(title.replace(" ", "+"))
								headers = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"}
								ff = requests.get(url, stream=True, headers=headers).text
								p = re.findall('"https://(.*?).jpg",(\d*),(\d*)', ff)
								url = "https://" + p[i+1][0] + ".jpg"
							except:
								pass
							open(dwnldFile, 'wb').write(requests.get(url, stream=True, allow_redirects=True).content)
							extra2_downloaded += 1
							downloaded = extra2_downloaded
							self.prgrs(downloaded, n)
							self['info'].setText(_("{}, backdrop downloaded from EXTRA2...".format(title.upper())))
							self.brokenImageRemove()

# infos #################################################################
				if config.plugins.xtraEvent.info.value == True:
					info_files = pathLoc + "infos/{}.json".format(title)
					if not os.path.exists(info_files):
						try:
							url = "http://www.omdbapi.com/?apikey={}&t={}".format(omdb_api, title)
							info_omdb = requests.get(url).json()
							open(info_files,"wb").write(json.dumps(info_omdb))
							info_downloaded += 1
							downloaded = info_downloaded
							self.prgrs(downloaded, n)
							self['info'].setText(_("{}, downloaded from INFO(OMDB)...".format(title.upper())))
						except:
							pass
					else:
						continue
			now = datetime.now()
			dt = now.strftime("%d/%m/%Y %H:%M:%S")
			report = "end : {}\
				\ndownloaded ;\
				\nposter; tmdb :{}, tvdb :{}, maze :{}, fanart :{}\
				\nbackdrop; tmdb :{}, tvdb :{}, fanart :{}, extra :{}, extra2 :{}\
				\nbanner :{}\
				\ninfos :{}".format(dt, str(tmdb_poster_downloaded), str(tvdb_poster_downloaded), str(maze_poster_downloaded), str(fanart_poster_downloaded), 
				str(tmdb_backdrop_downloaded), str(tvdb_backdrop_downloaded), str(fanart_backdrop_downloaded), 
				str(extra_downloaded), str(extra2_downloaded),
				str(banner_downloaded), 
				str(info_downloaded))
			self['info'].setText("downloads finished...")
			self['info2'].setText(report)
			
			with open("/tmp/up_report", "a+") as f:
				f.write(report)
			return
		# else:
			# self.session.open(MessageBox, _("NO INTERNET CONNECTION !.."), MessageBox.TYPE_INFO, timeout = 10)
			# self.close()
		except:
			pass
			
####################################################################################################################################

	def prgrs(self, downloaded, n):
		self['status'].setText("Download : {} / {}".format(downloaded, n))
		self['progress'].setValue(int(100*downloaded/n))
		
	def brokenImageRemove(self):
		b = os.listdir(pathLoc)
		rmvd = 0
		try:
			for i in b:
				bb = pathLoc + "{}/".format(i)
				fc = os.path.isdir(bb)
				if fc != False:	
					for f in os.listdir(bb):
						if f.endswith('.jpg'):
							try:
								img = Image.open(bb+f)
								img.verify()
							except:
								try:
									os.remove(bb+f)
									rmvd += 1
								except:
									pass
		except:
			pass
			