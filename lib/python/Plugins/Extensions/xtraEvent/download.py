# -*- coding: utf-8 -*-
# by digiteng...06.2020, 07.2020,08.2020

from Components.AVSwitch import AVSwitch
from enigma import eEPGCache
from Components.config import config
from ServiceReference import ServiceReference
from Screens.MessageBox import MessageBox
import Tools.Notifications
import requests
from requests.utils import quote
import os, re, random
from PIL import Image
import socket
import xtra
from datetime import datetime


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
pathLoc = xtra.pathLocation().location()

def save():
	if config.plugins.xtraEvent.searchMOD.value == "Current Channel":
		currentChEpgs()
	if config.plugins.xtraEvent.searchMOD.value == "Bouquets":
		selBouquets()

def currentChEpgs():
	if os.path.exists(pathLoc + "events"):
		os.remove(pathLoc + "events")
	try:
		events = None
		import NavigationInstance
		ref = NavigationInstance.instance.getCurrentlyPlayingServiceReference().toString()
		try:
			events = epgcache.lookupEvent(['IBDCTSERNX', (ref, 1, -1, -1)])
			n = config.plugins.xtraEvent.searchNUMBER.value

			for i in range(int(n)):
				title = events[i][4]
				evntNm = re.sub("([\(\[]).*?([\)\]])|(: odc.\d+)|(\d+: odc.\d+)|(\d+ odc.\d+)|(:)|( -(.*?).*)|(,)|!", "", title).rstrip().lower()
				open(pathLoc + "events", "a+").write("%s\n" %str(evntNm))

			intCheck()
			download()
		except:
			pass

	except:
		pass

def selBouquets():
	if os.path.exists(pathLoc + "events"):
		os.remove(pathLoc + "events")
		
	if os.path.exists(pathLoc + "bqts"):
		with open(pathLoc + "bqts", "r") as f:
			refs = f.readlines()
		
		nl=len(refs)
		for i in range(nl):
			ref = refs[i]
			try:
				events = epgcache.lookupEvent(['IBDCTSERNX', (ref, 1, -1, -1)])
				n = config.plugins.xtraEvent.searchNUMBER.value
				for i in range(int(n)):
					title = events[i][4]
					evntNm = re.sub("([\(\[]).*?([\)\]])|(: odc.\d+)|(\d+: odc.\d+)|(\d+ odc.\d+)|(:)|( -(.*?).*)|(,)|!", "", title).rstrip().lower()
					open(pathLoc+"events","a+").write("%s\n"% str(evntNm))
			except:
				pass		
		intCheck()
		download()

def intCheck():
	try:
		socket.setdefaulttimeout(0.5)
		socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
		return True
	except:
		return False

def download():
	now = datetime.now()
	dt = now.strftime("%d/%m/%Y %H:%M:%S")
	with open("/tmp/up_report", "a+") as f:
		f.write(str("\nstart : {}\n".format(dt)))
	try:
		if intCheck():
			if config.plugins.xtraEvent.poster.value == True:
				if config.plugins.xtraEvent.tmdb.value == True:
					tmdb_Poster()
				if config.plugins.xtraEvent.tvdb.value == True:
					tvdb_Poster()

				if config.plugins.xtraEvent.maze.value == True:
					maze_Poster()
				if config.plugins.xtraEvent.fanart.value == True:
					fanart_Poster()

			if config.plugins.xtraEvent.banner.value == True:
				Banner()

			if config.plugins.xtraEvent.backdrop.value == True:
				if config.plugins.xtraEvent.tmdb.value == True:
					tmdb_backdrop()
				if config.plugins.xtraEvent.tvdb.value == True:
					tvdb_backdrop()
				if config.plugins.xtraEvent.fanart.value == True:
					fanart_backdrop()
				if config.plugins.xtraEvent.extra.value == True:
					extra_backdrop()

			if config.plugins.xtraEvent.info.value == True:
				infos()
		else:
			Tools.Notifications.AddNotification(MessageBox, _("NO INTERNET CONNECTION !.."), MessageBox.TYPE_INFO, timeout = 10)
			return
	except:
		return
# DOWNLOAD POSTERS ######################################################################################################

def tmdb_Poster():
	url = ""
	dwnldFile = ""
	try:
		if os.path.exists(pathLoc+"events"):
			with open(pathLoc+"events", "r") as f:
				titles = f.readlines()
			titles = list(dict.fromkeys(titles))
			n = len(titles)
			downloaded = 0
			for i in range(n):
				title = titles[i]
				title = title.strip()
				dwnldFile = pathLoc + "poster/{}.jpg".format(title)
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
							w = open(dwnldFile, 'wb').write(requests.get(url, stream=True, allow_redirects=True).content)
							downloaded += 1
							w.close()
							
					except:
						pass
			now = datetime.now()
			dt = now.strftime("%d/%m/%Y %H:%M:%S")
			with open("/tmp/up_report", "a+") as f:
				f.write("tmdb_poster end : {} (downloaded : {})\n".format(dt, str(downloaded)))
			brokenImageRemove()
		
	except:
		pass

def tvdb_Poster():
	url = ""
	dwnldFile = ""
	downloaded = None
	try:
		if os.path.exists(pathLoc+"events"):
			with open(pathLoc+"events", "r") as f:
				titles = f.readlines()

			titles = list(dict.fromkeys(titles))
			n = len(titles)
			downloaded = 0
			for i in range(n):
				title = titles[i]
				title = title.strip()
				dwnldFile = pathLoc + "poster/{}.jpg".format(title)
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

							w = open(dwnldFile, 'wb').write(requests.get(url, stream=True, allow_redirects=True).content)
							downloaded += 1
							w.close()
								
					except:
						pass
			now = datetime.now()
			dt = now.strftime("%d/%m/%Y %H:%M:%S")
			with open("/tmp/up_report", "a+") as f:
				f.write("tvdb_poster end : {} (downloaded : {})\n".format(dt, str(downloaded)))
			brokenImageRemove()
	except:
		pass

def fanart_Poster():
	# pass
	url = ""
	dwnldFile = ""
	try:
		if os.path.exists(pathLoc+"events"):
			with open(pathLoc+"events", "r") as f:
				titles = f.readlines()

			titles = list(dict.fromkeys(titles))
			n = len(titles)
			downloaded = 0
			for i in range(n):
				title = titles[i]
				title = title.strip()
				
				dwnldFile = pathLoc + "poster/{}.jpg".format(title)
				
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
							
							url_maze = "http://api.tvmaze.com/singlesearch/shows?q={}".format(quote(title))
							mj = requests.get(url_maze).json()
							tvdb_id = (mj['externals']['thetvdb'])
							if tvdb_id:
								try:
									url = "https://webservice.fanart.tv/v3/{}/{}?api_key={}".format(m_type, tvdb_id, fanart_api)
									fjs = requests.get(url).json()
									if fjs:
										if m_type == "movies":
											mm_type = (bnnr['results'][0]['media_type'])
										else:
											mm_type = m_type
										url = (fjs['tvposter'][0]['url'])
										if url:
											# print url
											w = open(dwnldFile, 'wb').write(requests.get(url, stream=True, allow_redirects=True).content)
											downloaded += 1

											scl = 1
											im = Image.open(dwnldFile)
											scl = config.plugins.xtraEvent.FANART_Poster_Resize.value
											im1 = im.resize((im.size[0] // int(scl), im.size[1] // int(scl)), Image.ANTIALIAS)
											im1.save(dwnldFile)
											w.close()

								except:
									pass
				
					except:
						pass
			now = datetime.now()
			dt = now.strftime("%d/%m/%Y %H:%M:%S")
			with open("/tmp/up_report", "a+") as f:
				f.write("fanart_poster end : {} (downloaded : {})\n".format(dt, str(downloaded)))
			brokenImageRemove()
	except:
		pass

def maze_Poster():

	if os.path.exists(pathLoc+"events"):
		with open(pathLoc+"events", "r") as f:
			titles = f.readlines()

		titles = list(dict.fromkeys(titles))
		n = len(titles)
		downloaded = 0
		for i in range(n):
			title = titles[i]
			title = title.strip()
			dwnldFile = pathLoc + "poster/{}.jpg".format(title)
			if not os.path.exists(dwnldFile):
				url = "http://api.tvmaze.com/search/shows?q={}".format(quote(title))
				try:
					url = requests.get(url).json()
					url = url[0]['show']['image']['medium']
					if url:
						w = open(dwnldFile, 'wb').write(requests.get(url, stream=True, allow_redirects=True).content)
						downloaded += 1
						w.close()
				except:
					pass

		now = datetime.now()
		dt = now.strftime("%d/%m/%Y %H:%M:%S")
		with open("/tmp/up_report", "a+") as f:
			f.write("maze_poster end : {} (downloaded : {})\n".format(dt, str(downloaded)))
		brokenImageRemove()

# DOWNLOAD BANNERS ######################################################################################################

def Banner():
	url = ""
	dwnldFile = ""
	if os.path.exists(pathLoc+"events"):
		with open(pathLoc+"events", "r") as f:
			titles = f.readlines()

		titles = list(dict.fromkeys(titles))
		n = len(titles)
		downloaded = 0
		for i in range(n):
			title = titles[i]
			title = title.strip()
			dwnldFile = pathLoc + "banner/{}.jpg".format(title)
			if not os.path.exists(dwnldFile):			
				try:
					url_tvdb = "https://thetvdb.com/api/GetSeries.php?seriesname=%s" %quote(title)
					url_read = requests.get(url_tvdb).text			
					series_id = re.findall('<seriesid>(.*?)</seriesid>', url_read, re.I)[0]
					if series_id:
						url = "https://artworks.thetvdb.com/banners/graphical/%s-g_t.jpg" %(series_id)
						if url:
							w = open(dwnldFile, 'wb').write(requests.get(url, stream=True, allow_redirects=True).content)
							downloaded += 1
							w.close()


				except:
					try:
						dwnldFile = pathLoc + "banner/{}.jpg".format(title)
						if not os.path.exists(dwnldFile):
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
								url_fanart = "https://webservice.fanart.tv/v3/{}/{}?api_key={}".format(m_type, tmdb_id, fanart_api)
								fjs = requests.get(url_fanart).json()
								if fjs:
									if m_type == "movies":
										mm_type = (bnnr['results'][0]['media_type'])
									url = (fjs[mm_type+'banner'][0]['url'])
									if url:
										w = open(dwnldFile, 'wb').write(requests.get(url, stream=True, allow_redirects=True).content)
										downloaded += 1
										w.close()


					except:
						try:
							dwnldFile = pathLoc + "banner/{}.jpg".format(title)
							if not os.path.exists(dwnldFile):
								url_maze = "http://api.tvmaze.com/singlesearch/shows?q=%s" %(title)
								mj = requests.get(url_maze).json()
								poster = (mj['externals']['thetvdb'])
								if poster:
									url_tvdb = "https://thetvdb.com/api/GetSeries.php?seriesname=%s" %quote(title)
									url_read = requests.get(url_tvdb).text
									series_id = re.findall('<seriesid>(.*?)</seriesid>', url_read, re.I)[0]
									banner_img = re.findall('<banner>(.*?)</banner>', url_read, re.I)[0]
									if banner_img:
										url = "https://artworks.thetvdb.com%s" %(banner_img)

										w = open(dwnldFile, 'wb').write(requests.get(url, stream=True, allow_redirects=True).content)
										w.close()

									if series_id:
										try:
											url_fanart = "https://webservice.fanart.tv/v3/{}/{}?api_key={}".format(m_type, series_id, fanart_api)
											fjs = requests.get(url_fanart).json()
											if fjs:
												if m_type == "movies":
													mm_type = (bnnr['results'][0]['media_type'])
												else:
													mm_type = m_type
												url = (fjs[mm_type+'banner'][0]['url'])

												if url:

													w = open(dwnldFile, 'wb').write(requests.get(url, stream=True, allow_redirects=True).content)
													downloaded += 1
													w.close()

										except:
											pass
						except:
							pass
		now = datetime.now()
		dt = now.strftime("%d/%m/%Y %H:%M:%S")
		with open("/tmp/up_report", "a+") as f:
			f.write("banner end : {} (downloaded : {})\n".format(dt, str(downloaded)))
		brokenImageRemove()
# DOWNLOAD BACKDROP ######################################################################################################

def tmdb_backdrop():
	url = ""
	dwnldFile = ""
	try:
		if os.path.exists(pathLoc+"events"):
			with open(pathLoc+"events", "r") as f:
				titles = f.readlines()

			titles = list(dict.fromkeys(titles))
			n = len(titles)
			downloaded = 0
			for i in range(n):
				title = titles[i]
				title = title.strip()
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
						
							w = open(dwnldFile, 'wb').write(requests.get(url, stream=True, allow_redirects=True).content)
							downloaded += 1
							w.close()
					except:
						pass
			now = datetime.now()
			dt = now.strftime("%d/%m/%Y %H:%M:%S")
			with open("/tmp/up_report", "a+") as f:
				f.write("tmdb_backdrop end : {} (downloaded : {})\n".format(dt, str(downloaded)))
			brokenImageRemove()
	except:
		pass

def tvdb_backdrop():
	url = ""
	dwnldFile = ""
	try:
		if os.path.exists(pathLoc+"events"):
			with open(pathLoc+"events", "r") as f:
				titles = f.readlines()

			titles = list(dict.fromkeys(titles))
			n = len(titles)
			downloaded = 0
			for i in range(n):
				title = titles[i]
				title = title.strip()
				dwnldFile = pathLoc + "backdrop/{}.jpg".format(title)
				if not os.path.exists(dwnldFile):
					try:
						url_tvdb = "https://thetvdb.com/api/GetSeries.php?seriesname={}".format(quote(title))
						url_read = requests.get(url_tvdb).text
						series_id = re.findall('<seriesid>(.*?)</seriesid>', url_read)[0]
						if series_id:
							url_tvdb = "https://thetvdb.com/api/{}/series/{}/en".format(tvdb_api, series_id)
							url_read = requests.get(url_tvdb).text
							backdrop = re.findall('<fanart>(.*?)</fanart>', url_read)[0]
							if backdrop:
								url = "https://artworks.thetvdb.com/banners/{}".format(backdrop)
								if config.plugins.xtraEvent.TVDBbackdropsize.value == "thumbnail":
									url = url.replace(".jpg", "_t.jpg")


								w = open(dwnldFile, 'wb').write(requests.get(url, stream=True, allow_redirects=True).content)
								downloaded += 1
								w.close()

					except:
						pass
			now = datetime.now()
			dt = now.strftime("%d/%m/%Y %H:%M:%S")
			with open("/tmp/up_report", "a+") as f:
				f.write("tvdb_backdrop end : {} (downloaded : {})\n".format(dt, str(downloaded)))
			brokenImageRemove()
	except:
		pass

def fanart_backdrop():
	url = ""
	dwnldFile = ""
	try:
		if os.path.exists(pathLoc+"events"):
			with open(pathLoc+"events", "r") as f:
				titles = f.readlines()

			titles = list(dict.fromkeys(titles))
			n = len(titles)
			downloaded = 0
			for i in range(n):
				title = titles[i]
				title = title.strip()
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

							url = "http://api.tvmaze.com/singlesearch/shows?q=%s" %quote(title)
							bckdrp = requests.get(url).json()
							tvdb_id = (bckdrp['externals']['thetvdb'])
							if tvdb_id:
								try:
									
									url = "https://webservice.fanart.tv/v3/{}/{}?api_key={}" %(m_type, tvdb_id, fanart_api)
									bckdrp = requests.get(url).json()
									
									if bckdrp:
										if m_type == "movies":
											mm_type = (bckdrp['results'][0]['media_type'])
										else:
											mm_type = m_type
										url = (bckdrp['tvthumb'][0]['url'])
										if url:
											w = open(dwnldFile, 'wb').write(requests.get(url, stream=True, allow_redirects=True).content)
											downloaded += 1
											w.close()
											
											scl = 1
											im = Image.open(dwnldFile)
											scl = config.plugins.xtraEvent.FANART_Backdrop_Resize.value
											im1 = im.resize((im.size[0] // int(scl), im.size[1] // int(scl)), Image.ANTIALIAS)
											im1.save(dwnldFile)

								except:
									pass
					except:
						pass
			now = datetime.now()
			dt = now.strftime("%d/%m/%Y %H:%M:%S")
			with open("/tmp/up_report", "a+") as f:
				f.write("fanart_backdrop end : {} (downloaded : {})\n".format(dt, str(downloaded)))
			brokenImageRemove()
	except:
		pass

def extra_backdrop():
	if os.path.exists(pathLoc+"events"):
		with open(pathLoc+"events", "r") as f:
			titles = f.readlines()

		titles = list(dict.fromkeys(titles))
		n = len(titles)
		downloaded = 0
		for i in range(n):
			title = titles[i]
			title = title.strip()

			dwnldFile = "{}backdrop/{}.jpg".format(pathLoc, title)
			if not os.path.exists(dwnldFile):
				url = "http://capi.tvmovie.de/v1/broadcasts/search?q={}&page=1&rows=1".format(title.replace(" ", "+"))
				try:
					url = requests.get(url).json()['results'][0]['images'][0]['filepath']['android-image-320-180']
				except:
					# pass
					try:
						url="https://www.bing.com/search?q={}+poster+jpg".format(title.replace(" ", "+"))
						headers = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"}
						ff = requests.get(url, stream=True, headers=headers).text
						p='ihk=\"\/th\?id=(.*?)&'
						f= re.findall(p, ff)
						url = "https://www.bing.com/th?id="+f[0]
					except:
						pass
				try:
					w = open(dwnldFile, 'wb').write(requests.get(url, stream=True, allow_redirects=True).content)
					downloaded += 1
					w.close()
				except:
					pass

		now = datetime.now()
		dt = now.strftime("%d/%m/%Y %H:%M:%S")
		with open("/tmp/up_report", "a+") as f:
			f.write("extra_backdrop(tvmovie+bing) end : {} (downloaded : {})\n".format(dt, str(downloaded)))
		brokenImageRemove()
		downloaded = 0
		for i in range(n):
			title = titles[i]
			title = title.strip()

			dwnldFile = "{}backdrop/{}.jpg".format(pathLoc, title)
			if not os.path.exists(dwnldFile):
				try:
					url = "https://www.google.com/search?q={}&tbm=isch&tbs=sbd:0".format(title.replace(" ", "+"))

					headers = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"}
					ff = requests.get(url, stream=True, headers=headers).text
					p = re.findall('"https://(.*?).jpg",(\d*),(\d*)', ff)
					url = "https://" + p[i+1][0] + ".jpg"

					w = open(dwnldFile, 'wb').write(requests.get(url, stream=True, allow_redirects=True).content)
					downloaded += 1
					w.close()
				except:
					pass

		now = datetime.now()
		dt = now.strftime("%d/%m/%Y %H:%M:%S")
		with open("/tmp/up_report", "a+") as f:
			f.write("extra_backdrop(google) end : {} (downloaded : {})\n".format(dt, str(downloaded)))
		brokenImageRemove()

# DOWNLOAD INFOS ######################################################################################################

def infos():
	import json
	if os.path.exists(pathLoc+"events"):
		with open(pathLoc+"events", "r") as f:
			titles = f.readlines()

		titles = list(dict.fromkeys(titles))
		n = len(titles)
		downloaded = 0
		for i in range(n):
			title = titles[i]
			title = title.strip()
			info_files = pathLoc + "infos/{}.json".format(title)
			if not os.path.exists(info_files):
				try:
					url = 'https://www.bing.com/search?q={}+imdb'.format(title)
					headers = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"}
					ff = requests.get(url, stream=True, headers=headers).text
					rc = re.compile('https://www.imdb.com/title/tt(\d*)', re.DOTALL)
					imdb_id = "tt" + rc.search(ff).group(1)
					if imdb_id:
						url_omdb = 'https://www.omdbapi.com/?apikey={}&i={}'.format(str(omdb_api), str(imdb_id))
						info_json = requests.get(url_omdb).json()

						w = open(info_files,"wb").write(json.dumps(info_json))
						downloaded += 1
						w.close()

				except:
					pass
		now = datetime.now()
		dt = now.strftime("%d/%m/%Y %H:%M:%S")
		with open("/tmp/up_report", "a+") as f:
			f.write("infos end : {} (downloaded : {})\n\n".format(dt, str(downloaded)))

def brokenImageRemove():
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

		