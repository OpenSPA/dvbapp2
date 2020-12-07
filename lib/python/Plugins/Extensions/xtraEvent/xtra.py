# -*- coding: utf-8 -*-
# by digiteng...06.2020, 11.2020
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Components.Pixmap import Pixmap
from Components.Label import Label
from Components.ActionMap import ActionMap
from Screens.MessageBox import MessageBox
from Screens.Standby import TryQuitMainloop
import Tools.Notifications
import os, re, random, datetime
from Components.SelectionList import SelectionList, SelectionEntryComponent
from Components.config import config, configfile, ConfigYesNo, ConfigSubsection, getConfigListEntry, ConfigSelection, ConfigText, ConfigInteger, ConfigSelectionNumber, ConfigDirectory
from Components.ConfigList import ConfigListScreen
from enigma import eTimer, eLabel, eServiceCenter, eServiceReference, ePixmap, eSize, ePoint, loadJPG, iServiceInformation, eEPGCache, getBestPlayableServiceReference, getDesktop
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Screens.VirtualKeyBoard import VirtualKeyBoard
from PIL import Image, ImageDraw, ImageFilter
from Screens.LocationBox import LocationBox
import socket
import requests
import threading
from Components.ProgressBar import ProgressBar
from Screens.ChoiceBox import ChoiceBox
import shutil

desktop_size = getDesktop(0).size().width()
epgcache = eEPGCache.getInstance()

config.plugins.xtraEvent = ConfigSubsection()
config.plugins.xtraEvent.skinSelect = ConfigSelection(default = "default", choices = [("default"), ("skin_2"), ("skin_3")])
config.plugins.xtraEvent.loc = ConfigDirectory(default='')
config.plugins.xtraEvent.searchMOD = ConfigSelection(default = "Current Channel", choices = [("Bouquets"), ("Current Channel")])
# config.plugins.xtraEvent.searchNUMBER = ConfigSelectionNumber(0, 999, 1, default=0)
imglist = []
for i in range(0, 999):
	if i == 0:
		imglist.append(("all epg"))
	else:
		imglist.append(("%d" % i))
config.plugins.xtraEvent.searchNUMBER = ConfigSelection(default = "all epg", choices = imglist)

config.plugins.xtraEvent.timer = ConfigSelectionNumber(1, 168, 1, default=1)
config.plugins.xtraEvent.searchMANUELnmbr = ConfigSelectionNumber(0, 999, 1, default=1)
config.plugins.xtraEvent.searchMANUELyear = ConfigInteger(default = 0, limits=(0, 9999))
config.plugins.xtraEvent.imgNmbr = ConfigSelectionNumber(0, 999, 1, default=1)

config.plugins.xtraEvent.searchModManuel = ConfigSelection(default = "TV List", choices = [("TV List"), ("Movies List")])
config.plugins.xtraEvent.EMCloc = ConfigDirectory(default='')

config.plugins.xtraEvent.apis = ConfigYesNo(default = False)
config.plugins.xtraEvent.tmdbAPI = ConfigText(default="", visible_width=100, fixed_size=False)
config.plugins.xtraEvent.tvdbAPI = ConfigText(default="", visible_width=100, fixed_size=False)
config.plugins.xtraEvent.omdbAPI = ConfigText(default="", visible_width=100, fixed_size=False)
config.plugins.xtraEvent.fanartAPI = ConfigText(default="", visible_width=100, fixed_size=False)

config.plugins.xtraEvent.searchMANUEL_EMC = ConfigText(default="movies name", visible_width=100, fixed_size=False)
config.plugins.xtraEvent.searchMANUEL = ConfigText(default="event name", visible_width=100, fixed_size=False)
config.plugins.xtraEvent.searchLang = ConfigText(default="en", visible_width=100, fixed_size=False)
config.plugins.xtraEvent.timerMod = ConfigYesNo(default = False)

config.plugins.xtraEvent.tmdb = ConfigYesNo(default = False)
config.plugins.xtraEvent.tvdb = ConfigYesNo(default = False)
config.plugins.xtraEvent.maze = ConfigYesNo(default = False)
config.plugins.xtraEvent.fanart = ConfigYesNo(default = False)
config.plugins.xtraEvent.bing = ConfigYesNo(default = False)
config.plugins.xtraEvent.extra = ConfigYesNo(default = False)
config.plugins.xtraEvent.extra2 = ConfigYesNo(default = False)

config.plugins.xtraEvent.poster = ConfigYesNo(default = False)
config.plugins.xtraEvent.banner = ConfigYesNo(default = False)
config.plugins.xtraEvent.backdrop = ConfigYesNo(default = False)
config.plugins.xtraEvent.info = ConfigYesNo(default = False)

config.plugins.xtraEvent.opt_Images = ConfigYesNo(default = False)
config.plugins.xtraEvent.cnfg = ConfigYesNo(default = False)
config.plugins.xtraEvent.cnfgSel = ConfigSelection(default = "poster", choices = [("poster"), ("banner"), ("backdrop"), ("EMC")])

config.plugins.xtraEvent.TMDBpostersize = ConfigSelection(default="w185", choices = [
	("w92", "92x138"), 
	("w154", "154x231"), 
	("w185", "185x278"), 
	("w342", "342x513"), 
	("w500", "500x750"), 
	("w780", "780x1170"), 
	("original", "ORIGINAL")])
config.plugins.xtraEvent.TVDBpostersize = ConfigSelection(default="thumbnail", choices = [
	("thumbnail", "340x500"), 
	("fileName", "original(680x1000)")])

config.plugins.xtraEvent.TMDBbackdropsize = ConfigSelection(default="w300", choices = [
	("w300", "300x170"), 
	("w780", "780x440"), 
	("w1280", "1280x720"),
	("original", "ORIGINAL")])

config.plugins.xtraEvent.TVDBbackdropsize = ConfigSelection(default="thumbnail", choices = [
	("thumbnail", "640x360"), 
	("fileName", "original(1920x1080)")])

config.plugins.xtraEvent.FANART_Poster_Resize = ConfigSelection(default="10", choices = [
	("10", "100x142"), 
	("5", "200x285"), 
	("3", "333x475"), 
	("2", "500x713"), 
	("1", "1000x1426")])

config.plugins.xtraEvent.FANART_Backdrop_Resize = ConfigSelection(default="10", choices = [
	("2", "original/2"), 
	("1", "original")])

config.plugins.xtraEvent.imdb_Poster_size = ConfigSelection(default="10", choices = [
	("185", "185x278"), 
	("344", "344x510"), 
	("500", "500x750")])

config.plugins.xtraEvent.PB = ConfigSelection(default="posters", choices = [
	("posters", "Poster"), 
	("backdrops", "Backdrop")])

config.plugins.xtraEvent.imgs = ConfigSelection(default="TMDB", choices = [
	('TMDB', 'TMDB'), 
	('TVDB', 'TVDB'), 
	('FANART', 'FANART'), 
	('IMDB(poster)', 'IMDB(poster)'), 
	('Bing', 'Bing'), 
	('Google', 'Google')])

config.plugins.xtraEvent.searchType = ConfigSelection(default="tv", choices = [
	('tv', 'TV'), 
	('movie', 'MOVIE'), 
	('multi', 'MULTI')])

config.plugins.xtraEvent.FanartSearchType = ConfigSelection(default="tv", choices = [
	('tv', 'TV'),
	('movies', 'MOVIE')])

class xtra(Screen, ConfigListScreen):

	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		skin = None
		if desktop_size <= 1280:
			if config.plugins.xtraEvent.skinSelect.value == "default":
				skin = "/usr/lib/enigma2/python/Plugins/Extensions/xtraEvent/skins/xtra_720_default.xml"
			elif config.plugins.xtraEvent.skinSelect.value == "skin_2":
				skin = "/usr/lib/enigma2/python/Plugins/Extensions/xtraEvent/skins/xtra_720_2.xml"
			elif config.plugins.xtraEvent.skinSelect.value == "skin_3":
				skin = "/usr/lib/enigma2/python/Plugins/Extensions/xtraEvent/skins/xtra_720_3.xml"
		else:
			if config.plugins.xtraEvent.skinSelect.value == "default":
				skin = "/usr/lib/enigma2/python/Plugins/Extensions/xtraEvent/skins/xtra_1080_default.xml"
			elif config.plugins.xtraEvent.skinSelect.value == "skin_2":
				skin = "/usr/lib/enigma2/python/Plugins/Extensions/xtraEvent/skins/xtra_1080_2.xml"
			elif config.plugins.xtraEvent.skinSelect.value == "skin_3":
				skin = "/usr/lib/enigma2/python/Plugins/Extensions/xtraEvent/skins/xtra_1080_3.xml"
		with open(skin, 'r') as f:
			self.skin = f.read()

		list = []
		ConfigListScreen.__init__(self, list, session=session)

		self['key_red'] = Label(_('Close'))
		self['key_green'] = Label(_('Search'))
		self['key_yellow'] = Label(_('Delete files'))
		self['key_blue'] = Label(_('Manual Search'))

		self["actions"] = ActionMap(["OkCancelActions", "SetupActions", "DirectionActions", "ColorActions", "EventViewActions", "VirtualKeyboardAction"],
		{
			"left": self.keyLeft,
			"down": self.keyDown,
			"up": self.keyUp,
			"right": self.keyRight,
			"red": self.exit,
			"green": self.search,
			"yellow": self.erase,
			"blue": self.ms,
			"cancel": self.exit,
			"ok": self.keyOK,
			"info": self.strg,
			"menu": self.menuS
		},-1)
		
		self.setTitle(_("xtraEvent..."))
		self['status'] = Label()
		self['info'] = Label()
		self['int_statu'] = Label()
		self["help"] = StaticText()
		
		self.timer = eTimer()
		self.timer.callback.append(self.xtraList)
		self.onLayoutFinish.append(self.xtraList)
		self.intCheck()
		
	def intCheck(self):
		try:
			socket.setdefaulttimeout(2)
			socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
			self['int_statu'].setText("●")
			# return True
		except:
			return False

	def strg(self):
		try:
			path_poster = pathLoc+ "poster/"
			path_banner = pathLoc+ "banner/"
			path_backdrop = pathLoc+ "backdrop/"
			path_info = pathLoc+ "infos/"
			
			folder_size=sum([sum(map(lambda fname: os.path.getsize(os.path.join(path_poster, fname)), files)) for path_poster, folders, files in os.walk(path_poster)])
			posters_sz = "%0.1f" % (folder_size/(1024*1024.0))
			poster_nmbr = len(os.listdir(path_poster))

			folder_size=sum([sum(map(lambda fname: os.path.getsize(os.path.join(path_banner, fname)), files)) for path_banner, folders, files in os.walk(path_banner)])
			banners_sz = "%0.1f" % (folder_size/(1024*1024.0))
			banner_nmbr = len(os.listdir(path_banner))

			folder_size=sum([sum(map(lambda fname: os.path.getsize(os.path.join(path_backdrop, fname)), files)) for path_backdrop, folders, files in os.walk(path_backdrop)])
			backdrops_sz = "%0.1f" % (folder_size/(1024*1024.0))
			backdrop_nmbr = len(os.listdir(path_backdrop))

			folder_size=sum([sum(map(lambda fname: os.path.getsize(os.path.join(path_info, fname)), files)) for path_info, folders, files in os.walk(path_info)])
			infos_sz = "%0.1f" % (folder_size/(1024*1024.0))
			info_nmbr = len(os.listdir(path_info))
			
			self['status'].setText(_("Storage ;"))
			self['info'].setText(_(
				"Poster : {} poster {} MB".format(poster_nmbr, posters_sz)+ 
				"\nBanner : {} banner {} MB".format(banner_nmbr, banners_sz)+
				"\nBackdrop : {} backdrop {} MB".format(backdrop_nmbr, backdrops_sz)+
				"\nInfo : {} info {} MB".format(info_nmbr, infos_sz)))
		except:
			pass

	def keyOK(self):
		if self['config'].getCurrent()[1] is config.plugins.xtraEvent.loc:
			self.session.openWithCallback(self.pathSelected, LocationBox, text=_('Default Folder'), currDir=config.plugins.xtraEvent.loc.getValue(), minFree=100)

		if self['config'].getCurrent()[1] is config.plugins.xtraEvent.cnfgSel:
			self.compressImg()

	def pathSelected(self, res):
		if res is not None:
			config.plugins.xtraEvent.loc.value = res
			pathLoc = config.plugins.xtraEvent.loc.value + "xtraEvent/"
			if not os.path.isdir(pathLoc):
				os.makedirs(pathLoc + "poster")
				os.makedirs(pathLoc + "banner")
				os.makedirs(pathLoc + "backdrop")
				os.makedirs(pathLoc + "infos")
				os.makedirs(pathLoc + "mSearch")
				os.makedirs(pathLoc + "EMC")
				self.exit()

	def delay(self):
		self.timer.start(100, True)

	def xtraList(self):
		for x in self["config"].list:
			if len(x) > 1:
				x[1].save()
		list = []
		list.append(getConfigListEntry("—"*100))
# CONFIG_________________________________________________________________________________________________________________
		list.append(getConfigListEntry ("CONFIG MENU", config.plugins.xtraEvent.cnfg, _("adjust your settings and close ... your settings are valid ...")))
		list.append(getConfigListEntry("—"*100))
		if config.plugins.xtraEvent.cnfg.value:
			list.append(getConfigListEntry("	LOCALIZACION", config.plugins.xtraEvent.loc, _("'OK' select location downloads...")))
			list.append(getConfigListEntry("	SKIN", config.plugins.xtraEvent.skinSelect, _("* reOpen plugin...")))
			
			list.append(getConfigListEntry("	OPTIMIZA IMAGENES", config.plugins.xtraEvent.opt_Images, _("optimize images...")))
			if config.plugins.xtraEvent.opt_Images.value:
				list.append(getConfigListEntry("\tSELECCIONA IMAGENES A OPTIMIZAR", config.plugins.xtraEvent.cnfgSel, _("'OK' select for optimize images...")))
			list.append(getConfigListEntry("	TUS API'S", config.plugins.xtraEvent.apis, _("...")))
			if config.plugins.xtraEvent.apis.value:
				list.append(getConfigListEntry("	TMDB API", config.plugins.xtraEvent.tmdbAPI, _("enter your own api key...")))
				list.append(getConfigListEntry("	TVDB API", config.plugins.xtraEvent.tvdbAPI, _("enter your own api key...")))
				list.append(getConfigListEntry("	OMDB API", config.plugins.xtraEvent.omdbAPI, _("enter your own api key...")))
				list.append(getConfigListEntry("	FANART API", config.plugins.xtraEvent.fanartAPI, _("enter your own api key...")))
			list.append(getConfigListEntry("—"*100))

			list.append(getConfigListEntry("	MODO BUSQUEDA", config.plugins.xtraEvent.searchMOD, _("select search mode...")))		
			list.append(getConfigListEntry("	BUSCAR SIGUIENTES EVENTOS", config.plugins.xtraEvent.searchNUMBER, _("enter the number of next events...")))

			list.append(getConfigListEntry("	LENGUAJE DE BUSQUEDA", config.plugins.xtraEvent.searchLang, _("select search language...")))
			list.append(getConfigListEntry("	TEMPORIZADOR", config.plugins.xtraEvent.timerMod, _("select timer update for events..")))
			if config.plugins.xtraEvent.timerMod.value == True:
				list.append(getConfigListEntry("\tTEMPORIZADOR(horas)", config.plugins.xtraEvent.timer, _("..."),))
		list.append(getConfigListEntry("—"*100))
		list.append(getConfigListEntry("FUENTES IMAGENES"))
		list.append(getConfigListEntry("—"*100))

# poster__________________________________________________________________________________________________________________
		list.append(getConfigListEntry("POSTER", config.plugins.xtraEvent.poster, _("...")))
		if config.plugins.xtraEvent.poster.value == True:
			list.append(getConfigListEntry("\tTMDB", config.plugins.xtraEvent.tmdb, _(""),))
			if config.plugins.xtraEvent.tmdb.value :
				list.append(getConfigListEntry("\tTMDB TAMAÑO DE POSTER", config.plugins.xtraEvent.TMDBpostersize, _("")))
				list.append(getConfigListEntry("-"*100))
			list.append(getConfigListEntry("\tTVDB", config.plugins.xtraEvent.tvdb, _("source for poster...")))
			if config.plugins.xtraEvent.tvdb.value :
				list.append(getConfigListEntry("\tTVDB TAMAÑO DE POSTER", config.plugins.xtraEvent.TVDBpostersize, _("")))
				list.append(getConfigListEntry("_"*100))
			list.append(getConfigListEntry("\tFANART", config.plugins.xtraEvent.fanart, _("source for poster...")))	
			if config.plugins.xtraEvent.fanart.value:
				list.append(getConfigListEntry("\tFANART TAMAÑO DE POSTER", config.plugins.xtraEvent.FANART_Poster_Resize, _("")))
				list.append(getConfigListEntry("—"*100))
			list.append(getConfigListEntry("\tMAZE(TV SHOWS)", config.plugins.xtraEvent.maze, _("")))
# banner__________________________________________________________________________________________________________________
		list.append(getConfigListEntry("BANNER", config.plugins.xtraEvent.banner, _("")))

# backdrop_______________________________________________________________________________________________________________
		list.append(getConfigListEntry("BACKDROP", config.plugins.xtraEvent.backdrop, _("")))
		if config.plugins.xtraEvent.backdrop.value == True:
			list.append(getConfigListEntry("\tTMDB", config.plugins.xtraEvent.tmdb, _("")))
			if config.plugins.xtraEvent.tmdb.value :
				list.append(getConfigListEntry("\tTMDB TAMAÑO DE BACKDROP", config.plugins.xtraEvent.TMDBbackdropsize, _("")))
				list.append(getConfigListEntry("_"*100))
			list.append(getConfigListEntry("\tTVDB", config.plugins.xtraEvent.tvdb, _("")))
			if config.plugins.xtraEvent.tvdb.value :
				list.append(getConfigListEntry("\tTVDB TAMAÑO DE BACKDROP", config.plugins.xtraEvent.TVDBbackdropsize, _("")))
				list.append(getConfigListEntry("_"*100))
			list.append(getConfigListEntry("\tFANART", config.plugins.xtraEvent.fanart, _("")))
			if config.plugins.xtraEvent.fanart.value:
				list.append(getConfigListEntry("\tFANART TAMAÑO DE BACKDROP", config.plugins.xtraEvent.FANART_Backdrop_Resize, _("")))
				list.append(getConfigListEntry("_"*100))
			list.append(getConfigListEntry("\tEXTRA", config.plugins.xtraEvent.extra, _("source tvmovie.de...")))
			list.append(getConfigListEntry("\tEXTRA-2", config.plugins.xtraEvent.extra2, _("source google search images...")))
			list.append(getConfigListEntry("—"*100))
# info___________________________________________________________________________________________________________________
		list.append(getConfigListEntry("INFO", config.plugins.xtraEvent.info, _("Program information with OMDB...")))
		list.append(getConfigListEntry("—"*100))

		self["config"].list = list
		self["config"].l.setList(list)
		self.help()

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.delay()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.delay()

	def keyDown(self):
		self["config"].instance.moveSelection(self["config"].instance.moveDown)
		self.delay()

	def keyUp(self):
		self["config"].instance.moveSelection(self["config"].instance.moveUp)
		self.delay()

	def pageUp(self):
		self["config"].instance.moveSelection(self["config"].instance.pageDown)
		self.delay()

	def pageDown(self):
		self["config"].instance.moveSelection(self["config"].instance.pageUp)
		self.delay()

	def help(self):
		cur = self["config"].getCurrent()
		if cur:
			self["help"].text = cur[2]

	def currentChEpgs(self):
		if os.path.exists(pathLoc+"events"):
			os.remove(pathLoc+"events")
		try:
			events = None
			ref = self.session.nav.getCurrentlyPlayingServiceReference().toString()
			try:
				events = epgcache.lookupEvent(['IBDCTSERNX', (ref, 1, -1, -1)])
				if config.plugins.xtraEvent.searchNUMBER.value == "all epg":
					n = len(events)
					ttls = []
					for i in range(int(n)):
						title = events[i][4]
						evntNm = re.sub("([\(\[]).*?([\)\]])|(: odc.\d+)|(\d+: odc.\d+)|(\d+ odc.\d+)|(:)|( -(.*?).*)|(,)|!", "", title).rstrip()
						ttls.append(str(evntNm))
					ttls = list(dict.fromkeys(ttls))
					open(pathLoc+"events", "w").write(str(ttls))
					n = len(ttls)
					self['info'].setText(_("Event to be Scanned : {}".format(str(n))))
				else:
					n = config.plugins.xtraEvent.searchNUMBER.value
					ttls = []
					for i in range(int(n)):
						title = events[i][4]
						evntNm = re.sub("([\(\[]).*?([\)\]])|(: odc.\d+)|(\d+: odc.\d+)|(\d+ odc.\d+)|(:)|( -(.*?).*)|(,)|!", "", title).rstrip()
						ttls.append(str(evntNm))
					ttls = list(dict.fromkeys(ttls))
					open(pathLoc+"events", "w").write(str(ttls))
					n = len(ttls)
					self['info'].setText(_("Event to be Scanned : {}".format(str(n))))
			except:
				pass
		except:
			pass

	def menuS(self):
		list = [(_('Broken Images Remove'), self.brokenImageRemove), (_('No(Exit)'), self.exit)]
		self.session.openWithCallback(self.menuCallback, ChoiceBox, title=_('xtraEvent...'), list=list)

	def compressImg(self):
		import sys
		filepath = pathLoc + config.plugins.xtraEvent.cnfgSel.value
		folder_size = sum([sum(map(lambda fname: os.path.getsize(os.path.join(filepath, fname)), files)) for filepath, folders, files in os.walk(filepath)])
		old_size = "%0.1f" % (folder_size/(1024))
		if os.path.exists(filepath):
			lstdr = os.listdir(filepath)
			for j in lstdr:
				try:
					if os.path.isfile(filepath+"/"+j):
						im = Image.open(filepath+"/"+j)
						im.save(filepath+"/"+j, optimize=True, quality=75)
				except:
					pass

			folder_size = sum([sum(map(lambda fname: os.path.getsize(os.path.join(filepath, fname)), files)) for filepath, folders, files in os.walk(filepath)])
			new_size = "%0.1f" % (folder_size/(1024))
			self['info'].setText(_("{} images optimization end...\nGain : {}KB to {}KB".format(len(lstdr), old_size, new_size)))

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
		self['info'].setText(_("Removed Broken Images : {}".format(str(rmvd))))

	def menuCallback(self, ret = None):
		ret and ret[1]()

	def search(self):
		import download
		if config.plugins.xtraEvent.searchMOD.value == "Current Channel":
			self.session.open(download.downloads)
		if config.plugins.xtraEvent.searchMOD.value == "Bouquets":
			self.session.open(selBouquets)

	def ms(self):
		self.session.open(manuelSearch)

	def exit(self):
		for x in self["config"].list:
			if len(x) > 1:
				x[1].save()
		configfile.save()
		self.close()

	def erase(self):
		path = [pathLoc+'poster', pathLoc+'banner', pathLoc+'infos']
		formato = '%d-%m-%y'
		hoy = datetime.datetime.now()
		dia = hoy - datetime.timedelta(days=30)
		print hoy
		print dia
		for folder in path :
			print folder
			llista = os.listdir(folder)
			for file in llista:
				print file
				archivo = folder + os.sep + file
				estado = os.stat(archivo)
				modificado = datetime.datetime.fromtimestamp(estado.st_mtime)
				print modificado
				if modificado < dia :
					os.remove(archivo)


class manuelSearch(Screen, ConfigListScreen):

	def __init__(self, session):
		Screen.__init__(self, session)

		skin = None
		if desktop_size <= 1280:
			if config.plugins.xtraEvent.skinSelect.value == "default":
				skin = "/usr/lib/enigma2/python/Plugins/Extensions/xtraEvent/skins/manuelSearch_720_default.xml"
			elif config.plugins.xtraEvent.skinSelect.value == "skin_2":
				skin = "/usr/lib/enigma2/python/Plugins/Extensions/xtraEvent/skins/manuelSearch_720_2.xml"
			elif config.plugins.xtraEvent.skinSelect.value == "skin_3":
				skin = "/usr/lib/enigma2/python/Plugins/Extensions/xtraEvent/skins/manuelSearch_720_3.xml"
		else:
			if config.plugins.xtraEvent.skinSelect.value == "default":
				skin = "/usr/lib/enigma2/python/Plugins/Extensions/xtraEvent/skins/manuelSearch_1080_default.xml"
			elif config.plugins.xtraEvent.skinSelect.value == "skin_2":
				skin = "/usr/lib/enigma2/python/Plugins/Extensions/xtraEvent/skins/manuelSearch_1080_2.xml"
			elif config.plugins.xtraEvent.skinSelect.value == "skin_3":
				skin = "/usr/lib/enigma2/python/Plugins/Extensions/xtraEvent/skins/manuelSearch_1080_3.xml"
		with open(skin, 'r') as f:
			self.skin = f.read()

		self.title = ""
		self.year = ""
		self.evnt = ""

		list = []
		ConfigListScreen.__init__(self, list, session=session)

		self.setTitle(_("Manuel Search Events..."))
		self["key_red"] = StaticText(_("Exit"))
		self["key_green"] = StaticText(_("Search"))
		self["key_yellow"] = StaticText(_("Append"))
		self["key_blue"] = StaticText(_("Keyboard"))
		self["actions"] = ActionMap(["SetupActions", "ColorActions", "DirectionActions", "VirtualKeyboardAction"],
			{
				"left": self.keyLeft,

				"right": self.keyRight,
				"cancel": self.close,
				"red": self.close,
				"ok": self.keyOK,
				"green": self.mnlSrch,
				"yellow": self.append,
				"blue": self.vk
			}, -2)
		
		self['status'] = Label()
		self['info'] = Label()
		self["Picture"] = Pixmap()
		self['progress'] = ProgressBar()
		self['progress'].setRange((0, 100))
		self['progress'].setValue(0)		

		self.timer = eTimer()
		self.timer.callback.append(self.msList)
		self.timer.callback.append(self.pc)
		self.onLayoutFinish.append(self.msList)


	def keyOK(self):
		if self['config'].getCurrent()[1] is config.plugins.xtraEvent.EMCloc:
			self.session.openWithCallback(self.pathSelected, LocationBox, text=_('Default Folder'), currDir=config.plugins.xtraEvent.EMCloc.getValue(), minFree=100)

	def pathSelected(self, res):
		if res is not None:
			config.plugins.xtraEvent.EMCloc.value = res
			pathLoc = config.plugins.xtraEvent.EMCloc.value
			# self['status'].setText(_(pathLoc))
		return

	def intCheck(self):
		try:
			socket.setdefaulttimeout(5)
			socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
			return True
		except:
			return False

	def delay(self):
		self.timer.start(100, True)

	def msList(self):
		for x in self["config"].list:
			if len(x) > 1:
				x[1].save()
	
		list = []
		list.append(getConfigListEntry(_("CH / EMC-MoviePlayer"), config.plugins.xtraEvent.searchModManuel))
		list.append(getConfigListEntry(_("Events Next"), config.plugins.xtraEvent.searchMANUELnmbr))

		if config.plugins.xtraEvent.searchModManuel.value == "Movies List":
			list.append(getConfigListEntry(_("Movies List Location -OK Select-"), config.plugins.xtraEvent.EMCloc))

		list.append(getConfigListEntry(_("Year"), config.plugins.xtraEvent.searchMANUELyear))
		list.append(getConfigListEntry(_("Search Language"), config.plugins.xtraEvent.searchLang))
		list.append(getConfigListEntry(_("Search Image"), config.plugins.xtraEvent.PB))

		list.append(getConfigListEntry(_("Search Source"), config.plugins.xtraEvent.imgs))
		if config.plugins.xtraEvent.imgs.value == "TMDB":
			list.append(getConfigListEntry(_("\tSearch Type"), config.plugins.xtraEvent.searchType))
			if config.plugins.xtraEvent.PB.value == "posters":
				list.append(getConfigListEntry(_("\tSize"), config.plugins.xtraEvent.TMDBpostersize))
			else:
				list.append(getConfigListEntry(_("\tSize"), config.plugins.xtraEvent.TMDBbackdropsize))
				
		if config.plugins.xtraEvent.imgs.value == "TVDB":
			if config.plugins.xtraEvent.PB.value == "posters":
				list.append(getConfigListEntry(_("\tSize"), config.plugins.xtraEvent.TVDBpostersize))
			else:
				list.append(getConfigListEntry(_("\tSize"), config.plugins.xtraEvent.TVDBbackdropsize))
		
		if config.plugins.xtraEvent.imgs.value == "FANART":
			list.append(getConfigListEntry(_("\tSearch Type"), config.plugins.xtraEvent.FanartSearchType))
			if config.plugins.xtraEvent.PB.value == "posters":
				list.append(getConfigListEntry(_("\tSize"), config.plugins.xtraEvent.FANART_Poster_Resize))
			else:
				list.append(getConfigListEntry(_("\tSize"), config.plugins.xtraEvent.FANART_Backdrop_Resize))
		
		if config.plugins.xtraEvent.imgs.value == "IMDB(poster)":
			list.append(getConfigListEntry(_("\tSize"), config.plugins.xtraEvent.imdb_Poster_size))

		list.append(getConfigListEntry("—"*50))
		list.append(getConfigListEntry(_("Show Images"), config.plugins.xtraEvent.imgNmbr))
		list.append(getConfigListEntry("—"*50))
		
		self["config"].list = list
		self["config"].l.setList(list)

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		if self['config'].getCurrent()[0] == 'Events Next':
			self.curEpg()
		self.delay()
		
	def keyRight(self):
		ConfigListScreen.keyRight(self)
		if self['config'].getCurrent()[0] == 'Events Next':
			self.curEpg()
		self.delay()

	def curEpg(self):
		if config.plugins.xtraEvent.searchModManuel.value == "TV List":
			try:
				events = ""
				ref = self.session.nav.getCurrentlyPlayingServiceReference().toString()
				events = epgcache.lookupEvent(['IBDCTSERNX', (ref, 1, -1, -1)])
				if events:
					n = config.plugins.xtraEvent.searchMANUELnmbr.value
					self.evnt = events[int(n)][4]
					self.vkEdit("")
			except:
				pass
		if config.plugins.xtraEvent.searchModManuel.value == "Movies List":
			self.movieList()

	def movieList(self):
		pathLoc = config.plugins.xtraEvent.EMCloc.value
		try:
			mlst = os.listdir(pathLoc)
			if mlst:
				movieList = [x for x in mlst if x.endswith(".mvi") or x.endswith(".ts") or x.endswith(".mp4") or x.endswith(".avi") or x.endswith(".mkv") or x.endswith(".divx")]
				if movieList:
					n = config.plugins.xtraEvent.searchMANUELnmbr.value
					self.evnt = movieList[int(n)]
					self.vkEdit("")
		except:
			pass

	def vk(self):
		self.session.openWithCallback(self.vkEdit, VirtualKeyBoard, title="edit event name...", text = self.evnt)

	def vkEdit(self, text=None):
		if text:
			config.plugins.xtraEvent.searchMANUEL = ConfigText(default="{}".format(text), visible_width=100, fixed_size=False)
			config.plugins.xtraEvent.searchMANUEL_EMC = ConfigText(default="{}".format(text), visible_width=100, fixed_size=False)
			if config.plugins.xtraEvent.searchModManuel.value == "TV List":
				self.title = config.plugins.xtraEvent.searchMANUEL.value
			if config.plugins.xtraEvent.searchModManuel.value == "Movies List":
				self.title = config.plugins.xtraEvent.searchMANUEL_EMC.value
				self.title = self.title.split('-')[-1].split(".")[0].strip()
			self['status'].setText(_("Search : {}".format(str(self.title))))
		else:
			config.plugins.xtraEvent.searchMANUEL = ConfigText(default="{}".format(self.evnt), visible_width=100, fixed_size=False)
			config.plugins.xtraEvent.searchMANUEL_EMC = ConfigText(default="{}".format(self.evnt), visible_width=100, fixed_size=False)
			if config.plugins.xtraEvent.searchModManuel.value == "TV List":
				self.title = config.plugins.xtraEvent.searchMANUEL.value
			if config.plugins.xtraEvent.searchModManuel.value == "Movies List":
				self.title = config.plugins.xtraEvent.searchMANUEL_EMC.value
				self.title = self.title.split('-')[-1].split(".")[0].strip()
			self['status'].setText(_("Search : {}".format(str(self.title))))

	def mnlSrch(self):
		try:
			fs = os.listdir(pathLoc + "mSearch/")
			for f in fs:
				os.remove(pathLoc + "mSearch/" + f)
		except:
			return
		if config.plugins.xtraEvent.PB.value == "posters":
			if config.plugins.xtraEvent.imgs.value == "TMDB":
				threading.Thread(target=self.tmdb).start()
			if config.plugins.xtraEvent.imgs.value == "TVDB":
				threading.Thread(target=self.tvdb).start()
			if config.plugins.xtraEvent.imgs.value == "FANART":
				threading.Thread(target=self.fanart).start()
			if config.plugins.xtraEvent.imgs.value == "IMDB(poster)":
				threading.Thread(target=self.imdb).start()
			if config.plugins.xtraEvent.imgs.value == "Bing":
				threading.Thread(target=self.bing).start()
			if config.plugins.xtraEvent.imgs.value == "Google":
				threading.Thread(target=self.google).start()

		if config.plugins.xtraEvent.PB.value == "backdrops":
			if config.plugins.xtraEvent.imgs.value == "TMDB":
				threading.Thread(target=self.tmdb).start()
			if config.plugins.xtraEvent.imgs.value == "TVDB":
				threading.Thread(target=self.tvdb).start()
			if config.plugins.xtraEvent.imgs.value == "FANART":
				threading.Thread(target=self.fanart).start()
			if config.plugins.xtraEvent.imgs.value == "Bing":
				threading.Thread(target=self.bing).start()
			if config.plugins.xtraEvent.imgs.value == "Google":
				threading.Thread(target=self.google).start()

	def pc(self):
		try:
			self.iNmbr = config.plugins.xtraEvent.imgNmbr.value
			self.pb = config.plugins.xtraEvent.PB.value
			self.path = pathLoc + "mSearch/{}-{}-{}.jpg".format(self.title, self.pb, self.iNmbr)
			if config.plugins.xtraEvent.imgs.value == "IMDB(poster)":
				self.path = pathLoc + "mSearch/{}-poster-1.jpg".format(self.title)
			self["Picture"].instance.setPixmap(loadJPG(self.path))
			if desktop_size <= 1280:
				if self.pb == "posters":
					self["Picture"].instance.setScale(1)
					self["Picture"].instance.resize(eSize(185,278))
					self["Picture"].instance.move(ePoint(930,325))
				else:
					self["Picture"].instance.setScale(1)
					self["Picture"].instance.resize(eSize(300,170))
					self["Picture"].instance.move(ePoint(890,375))
			else:
				if self.pb == "posters":
					self["Picture"].instance.setScale(1)
					self["Picture"].instance.resize(eSize(185,278))
					self["Picture"].instance.move(ePoint(1450,550))
				else:
					self["Picture"].instance.setScale(1)
					self["Picture"].instance.resize(eSize(300,170))
					self["Picture"].instance.move(ePoint(1400,600))				

			self['Picture'].show()
			self.inf()
		except:
			return

	def inf(self):
		pb_path = ""
		pb_sz = ""
		tot = ""
		cur = ""
		try:
			msLoc = pathLoc + "mSearch/"
			n = 0
			for file in os.listdir(msLoc):
				if file.startswith("{}-{}".format(self.title, self.pb)) == True:
					e = os.path.join(msLoc, file)
					n += 1
			tot = n
			cur = config.plugins.xtraEvent.imgNmbr.value
			
			pb_path = pathLoc + "mSearch/{}-{}-{}.jpg".format(self.title, self.pb, self.iNmbr)
			pb_sz = "{} KB".format(os.path.getsize(pb_path)/1024)

			im = Image.open(pb_path)
			pb_res = im.size

			self['info'].setText(_("{}/{}    {}    {}".format(cur,tot,pb_sz,pb_res)))
		except:
			return

	def append(self):
		try:
			self.title = self.title
			if config.plugins.xtraEvent.PB.value == "posters":
				if config.plugins.xtraEvent.imgs.value == "bing":
					target = pathLoc + "poster/{}.jpg".format(self.title)
				if config.plugins.xtraEvent.searchModManuel.value == "TV List":
					target = pathLoc + "poster/{}.jpg".format(self.title)
				else:
					target = pathLoc + "EMC/{}-poster.jpg".format(self.title)
			else:
				if config.plugins.xtraEvent.searchModManuel.value == "TV List":
					target = pathLoc + "backdrop/{}.jpg".format(self.title)
					if config.plugins.xtraEvent.imgs.value == "bing":
						evntNm = re.sub("([\(\[]).*?([\)\]])|(: odc.\d+)|(\d+: odc.\d+)|(\d+ odc.\d+)|(:)|( -(.*?).*)|(,)|!", "", self.title).rstrip()
						target = pathLoc + "backdrop/{}.jpg".format(evntNm)
				else:
					target = pathLoc + "EMC/{}-backdrop.jpg".format(self.title)
			
			import shutil
			if os.path.exists(self.path):
				shutil.copyfile(self.path, target)
				
				if os.path.exists(target):
					if config.plugins.xtraEvent.PB.value == "backdrops":
						if not config.plugins.xtraEvent.searchModManuel.value == "TV List":
							im1 = Image.open(target) 
							im1 = im1.resize((1280,720))
							im1 = im1.save(target)
							if os.path.exists(target):
								im1 = Image.open(target)
								im2 = Image.open("/usr/lib/enigma2/python/Plugins/Extensions/xtraEvent/pic/emc_background.jpg")
								mask = Image.new("L", im1.size, 80)
								im = Image.composite(im1, im2, mask)
								im.save(target)
		except:
			return

	def tmdb(self):
		self['progress'].setValue(0)
		try:
			self.srch = config.plugins.xtraEvent.searchType.value
			self.year = config.plugins.xtraEvent.searchMANUELyear.value
			from requests.utils import quote
			url = "https://api.themoviedb.org/3/search/{}?api_key={}&query={}".format(self.srch, tmdb_api, quote(self.title))
			if self.year != "0":
				if config.plugins.xtraEvent.searchType.value == "tv":
					url += "&first_air_date_year={}".format(self.year)
				elif config.plugins.xtraEvent.searchType.value == "movie":
					url += "&year={}".format(self.year)

			id = requests.get(url).json()['results'][0]['id']
			url = "https://api.themoviedb.org/3/{}/{}?api_key={}&append_to_response=images".format(self.srch, int(id), tmdb_api)
			if config.plugins.xtraEvent.searchLang.value != "":
				url += "&language={}".format(config.plugins.xtraEvent.searchLang.value)
			if config.plugins.xtraEvent.PB.value == "posters":
				sz = config.plugins.xtraEvent.TMDBpostersize.value
			else:
				sz = config.plugins.xtraEvent.TMDBbackdropsize.value
			p1 = requests.get(url).json()
			pb_no = p1['images']['{}'.format(self.pb)]
			n = len(pb_no)
			if n > 0:
				downloaded = 0
				for i in range(int(n)):

					poster = p1['images']['{}'.format(self.pb)][i]['file_path']
					if poster:
						url_poster = "https://image.tmdb.org/t/p/{}{}".format(sz, poster)
						dwnldFile = pathLoc + "mSearch/{}-{}-{}.jpg".format(self.title, self.pb, i+1)
						open(dwnldFile, 'wb').write(requests.get(url_poster, stream=True, allow_redirects=True).content)
						
						downloaded += 1
						self.prgrs(downloaded, n)
			else:
				self['status'].setText(_("Download : 0"))
			config.plugins.xtraEvent.imgNmbr.value = 0

		except:
			return

	def tvdb(self):
		self['progress'].setValue(0)
		try:
			self.srch = config.plugins.xtraEvent.searchType.value
			self.year = config.plugins.xtraEvent.searchMANUELyear.value
			from requests.utils import quote
			url = "https://thetvdb.com/api/GetSeries.php?seriesname={}".format(quote(self.title))
			if self.year != 0:
				url += "%20{}".format(self.year)
			
			url_read = requests.get(url).text
			series_id = re.findall('<seriesid>(.*?)</seriesid>', url_read)[0]
			if config.plugins.xtraEvent.PB.value == "posters":
				keyType = "poster"
			else:
				keyType = "fanart"
			url = 'https://api.thetvdb.com/series/{}/images/query?keyType={}'.format(series_id, keyType)
			u = requests.get(url, headers={"Accept-Language":"{}".format(config.plugins.xtraEvent.searchLang.value)})
			try:
				pb_no = u.json()["data"]
				n = len(pb_no)
			except:
				self['status'].setText(_("Download : No"))
				return
			if n > 0:
				downloaded = 0
				for i in range(int(n)):
					if config.plugins.xtraEvent.PB.value == "posters":
						img_pb = u.json()["data"][i]['{}'.format(config.plugins.xtraEvent.TVDBpostersize.value)]
					else:
						img_pb = u.json()["data"][i]['{}'.format(config.plugins.xtraEvent.TVDBbackdropsize.value)]
					url = "https://artworks.thetvdb.com/banners/{}".format(img_pb)

					dwnldFile = pathLoc + "mSearch/{}-{}-{}.jpg".format(self.title, self.pb, i+1)
					open(dwnldFile, 'wb').write(requests.get(url, stream=True, allow_redirects=True).content)
					downloaded += 1
					self.prgrs(downloaded, n)
			else:
				self['status'].setText(_("Download : No"))
			config.plugins.xtraEvent.imgNmbr.value = 0
		except:
			return

	def fanart(self):
		id = "-"
		from requests.utils import quote
		try:
			if config.plugins.xtraEvent.FanartSearchType.value == "tv":
				try:
					url_maze = "http://api.tvmaze.com/singlesearch/shows?q={}".format(quote(self.title))
					mj = requests.get(url_maze).json()
					id = (mj['externals']['thetvdb'])
				except:
					pass
			else:
				try:
					self.year = config.plugins.xtraEvent.searchMANUELyear.value
					url = "https://api.themoviedb.org/3/search/movie?api_key={}&query={}".format(tmdb_api, quote(self.title))
					if self.year != 0:
						url += "&primary_release_year={}&year={}".format(self.year, self.year)
					id = requests.get(url).json()['results'][0]['id']
				except:
					pass

			try:
				m_type = config.plugins.xtraEvent.FanartSearchType.value
				url_fanart = "https://webservice.fanart.tv/v3/{}/{}?api_key={}".format(m_type, id, fanart_api)
				fjs = requests.get(url_fanart).json()
				if config.plugins.xtraEvent.PB.value == "posters":
					if config.plugins.xtraEvent.FanartSearchType.value == "tv":
						pb_no = fjs['tvposter']
						n = len(pb_no)
					else:
						pb_no = fjs['movieposter']
						n = len(pb_no)
				if config.plugins.xtraEvent.PB.value == "backdrops":
					if config.plugins.xtraEvent.FanartSearchType.value == "tv":
						pb_no = fjs['showbackground']
						n = len(pb_no)
					else:
						pb_no = fjs['moviebackground']
						n = len(pb_no)
				if n > 0:
					downloaded = 0				
					for i in range(int(n)):
						if config.plugins.xtraEvent.PB.value == "posters":
							if config.plugins.xtraEvent.FanartSearchType.value == "tv":
								url = (fjs['tvposter'][i]['url'])
							else:
								url = (fjs['movieposter'][i]['url'])
						
						if config.plugins.xtraEvent.PB.value == "backdrops":
							if config.plugins.xtraEvent.FanartSearchType.value == "tv":
								url = (fjs['showbackground'][i]['url'])
							else:
								url = (fjs['moviebackground'][i]['url'])
								
						if url:
							dwnldFile = pathLoc + "mSearch/{}-{}-{}.jpg".format(self.title, self.pb, i+1)
							open(dwnldFile, 'wb').write(requests.get(url, stream=True, allow_redirects=True).content)
							downloaded += 1
							self.prgrs(downloaded, n)
							
							scl = 1
							im = Image.open(dwnldFile)
							if config.plugins.xtraEvent.PB.value == "posters":
								scl = config.plugins.xtraEvent.FANART_Poster_Resize.value
							if config.plugins.xtraEvent.PB.value == "backdrops":
								scl = config.plugins.xtraEvent.FANART_Backdrop_Resize.value
							im1 = im.resize((im.size[0] // int(scl), im.size[1] // int(scl)), Image.ANTIALIAS)
							im1.save(dwnldFile)

				else:
					self['status'].setText(_("Download : No"))
				config.plugins.xtraEvent.imgNmbr.value = 0
			except:
				pass
	
		except:
			pass

	def imdb(self):
		downloaded = 0
		try:
			from requests.utils import quote
			url_find = 'https://m.imdb.com/find?q={}'.format(quote(self.title))
			ff = requests.get(url_find).text
			p = 'src=\"https://(.*?)._V1_UX75_CR0,0,75,109_AL_.jpg'
			pstr = re.findall(p,ff)[0]
			if config.plugins.xtraEvent.PB.value == "posters":
				url = "https://{}._V1_UX{}_AL_.jpg".format(pstr, config.plugins.xtraEvent.imdb_Poster_size.value)
				if url:
					dwnldFile = pathLoc + "mSearch/{}-poster-1.jpg".format(self.title)
					open(dwnldFile, 'wb').write(requests.get(url, stream=True, allow_redirects=True).content)
					downloaded += 1
					n = 1
					self.prgrs(downloaded, n)
				else:
					self['status'].setText(_("Download : No"))
				config.plugins.xtraEvent.imgNmbr.value = 0
		except:
			pass

	def bing(self):
		self['status'].setText(_("Download : No"))
		pass
		# try:
			# url="https://www.bing.com/search?q={}+poster+jpg".format(self.title.replace(" ", "+"))
			# headers = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"}
			# ff = requests.get(url, stream=True, headers=headers).text
			# p = re.findall('ihk=\"\/th\?id=(.*?)&', ff)
			# n = len(p)
			# downloaded = 0
			# if n > 0:
				# for i in range(n):
					# url = "https://www.bing.com/th?id={}".format(p[i])
					# dwnldFile = pathLoc + "mSearch/{}-{}-{}.jpg".format(self.title, self.pb, i+1)
					# open(dwnldFile, 'wb').write(requests.get(url, stream=True, allow_redirects=True).content)

					# downloaded += 1
					# self.prgrs(downloaded, n)
			# else:
				# self['status'].setText(_("Download : No"))
			# config.plugins.xtraEvent.imgNmbr.value = 0
		# except:
			# pass

	def google(self):
		try:
			url = "https://www.google.com/search?q={}&tbm=isch&tbs=sbd:0".format(self.title.replace(" ", "+"))
			headers = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"}
			ff = requests.get(url, stream=True, headers=headers).text
			p = re.findall('"https://(.*?).jpg",(\d*),(\d*)', ff)
			n = 9
			downloaded = 0
			for i in range(n):
				url = "https://" + p[i+1][0] + ".jpg"
				dwnldFile = pathLoc + "mSearch/{}-{}-{}.jpg".format(self.title, self.pb, i+1)
				open(dwnldFile, 'wb').write(requests.get(url, stream=True, allow_redirects=True).content)
				downloaded += 1
				self.prgrs(downloaded, n)
			config.plugins.xtraEvent.imgNmbr.value = 0
		except:
			self['status'].setText(_("Download : No"))
			return

	def prgrs(self, downloaded, n):
		self['status'].setText("Download : {} / {}".format(downloaded, n))
		self['progress'].setValue(int(100*downloaded/n))

def bqtList():
	bouquets = []
	serviceHandler = eServiceCenter.getInstance()
	list = serviceHandler.list(eServiceReference('1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "bouquets.tv" ORDER BY bouquet'))
	if list:
		while True:
			bqt = list.getNext()
			if not bqt.valid(): break
			info = serviceHandler.info(bqt)
			if info:
				bouquets.append((info.getName(bqt), bqt))
		return bouquets
	return 

def chList(bqtNm):
	channels = []
	serviceHandler = eServiceCenter.getInstance()
	chlist = serviceHandler.list(eServiceReference('1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "bouquets.tv" ORDER BY bouquet'))
	if chlist :
		while True:
			chh = chlist.getNext()
			if not chh.valid(): break
			info = serviceHandler.info(chh)
			if chh.flags & eServiceReference.isDirectory:
				info = serviceHandler.info(chh)
			if info.getName(chh) in bqtNm:
				chlist = serviceHandler.list(chh)
				while True:
					chhh = chlist.getNext()
					if not chhh.valid(): break
					channels.append((chhh.toString()))
		return channels
	return

class selBouquets(Screen):
	
	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)

		skin = None
		if desktop_size <= 1280:
			if config.plugins.xtraEvent.skinSelect.value == "default":
				skin = "/usr/lib/enigma2/python/Plugins/Extensions/xtraEvent/skins/selBouquets_720_default.xml"
			elif config.plugins.xtraEvent.skinSelect.value == "skin_2":
				skin = "/usr/lib/enigma2/python/Plugins/Extensions/xtraEvent/skins/selBouquets_720_2.xml"
			elif config.plugins.xtraEvent.skinSelect.value == "skin_3":
				skin = "/usr/lib/enigma2/python/Plugins/Extensions/xtraEvent/skins/selBouquets_720_3.xml"
		else:
			if config.plugins.xtraEvent.skinSelect.value == "default":
				skin = "/usr/lib/enigma2/python/Plugins/Extensions/xtraEvent/skins/selBouquets_1080_default.xml"
			elif config.plugins.xtraEvent.skinSelect.value == "skin_2":
				skin = "/usr/lib/enigma2/python/Plugins/Extensions/xtraEvent/skins/selBouquets_1080_2.xml"
			elif config.plugins.xtraEvent.skinSelect.value == "skin_3":
				skin = "/usr/lib/enigma2/python/Plugins/Extensions/xtraEvent/skins/selBouquets_1080_3.xml"
		with open(skin, 'r') as f:
			self.skin = f.read()

		self.bouquets = bqtList()
		# self.epgcache = eEPGCache.getInstance()
		self.setTitle(_("Bouquet Selection"))
		self.sources = [SelectionEntryComponent(s[0], s[1], 0, (s[0] in ["sources"])) for s in self.bouquets]
		self["list"] = SelectionList(self.sources)

		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
			{
				"cancel": self.cancel,
				"red": self.cancel,
				"green": self.bouquetEpgs,
				"yellow": self["list"].toggleSelection,
				"blue": self["list"].toggleAllSelection,

				"ok": self["list"].toggleSelection
			}, -2)

		self["key_red"] = Label(_("Cancel"))
		self["key_green"] = Label(_("Save"))
		self["key_yellow"] = Label(_("Select(OK)"))
		self["key_blue"] = Label(_("All Select"))
		
		self['status'] = Label()
		self['info'] = Label()

	def bouquetEpgs(self):
		if os.path.exists(pathLoc+"bqts"):
			os.remove(pathLoc+"bqts")
		if os.path.exists(pathLoc+"events"):
			os.remove(pathLoc+"events")
		try:
			self.sources = []
			for idx,item in enumerate(self["list"].list):
				item = self["list"].list[idx][0]
				if item[3]:
					self.sources.append(item[0])

			for p in self.sources:
				serviceHandler = eServiceCenter.getInstance()
				refs = chList(p)

				eventlist=[]
				for ref in refs:
					open(pathLoc + "bqts", "a+").write("%s\n"% str(ref))
					# try:
						# events = epgcache.lookupEvent(['IBDCTSERNX', (ref, 1, -1, -1)])
						# n = config.plugins.xtraEvent.searchNUMBER.value
						# for i in range(int(n)):
							# title = events[i][4]
							# evntNm = re.sub("([\(\[]).*?([\)\]])|(: odc.\d+)|(\d+: odc.\d+)|(\d+ odc.\d+)|(:)|( -(.*?).*)|(,)|!", "", title).rstrip()
							# eventlist.append(evntNm)
						# open(pathLoc+"events","w").write(str(eventlist))

					# except:
						# pass

			else:
				list = [(_('With Plugin Download'), self.withPluginDownload), (_('With Timer Download'), self.withTimerDownload), (_('No(Exit)'), self.cancel)]
				self.session.openWithCallback(self.menuCallback, ChoiceBox, title=_('Download ?'), list=list)

		except:
			pass

	def withPluginDownload(self):
		import download
		self.session.open(download.downloads)

	def withTimerDownload(self):
		if config.plugins.xtraEvent.timerMod.value == False:
			self.session.open(MessageBox, _("PLEASE TURN ON AND SET THE TIMER! ..."), MessageBox.TYPE_INFO, timeout = 10)
		else:
			self.session.openWithCallback(self.restart, MessageBox, _("NOW AND RESTART TO SEARCH AND DOWNLOAD IN BACKGROUND WITH TIMER?"), MessageBox.TYPE_YESNO, timeout = 20)

	def menuCallback(self, ret = None):
		ret and ret[1]()

	def restart(self, answer):
		if answer is True:
			configfile.save()
			self.session.open(TryQuitMainloop, 3)
		else:
			self.close()

	def cancel(self):
		self.close(self.session, False)

class pathLocation():
	def __init__(self):
		self.location()

	def location(self):
		pathLoc = ""
		if not os.path.isdir(config.plugins.xtraEvent.loc.value):
			pathLoc = "/tmp/xtraEvent/"
			try:
				if not os.path.isdir(pathLoc):
					os.makedirs(pathLoc + "poster")
					os.makedirs(pathLoc + "banner")
					os.makedirs(pathLoc + "backdrop")
					os.makedirs(pathLoc + "infos")
					os.makedirs(pathLoc + "mSearch")
					os.makedirs(pathLoc + "EMC")
			except:
				pass
		else:	
			pathLoc = config.plugins.xtraEvent.loc.value + "xtraEvent/"
			try:
				if not os.path.isdir(pathLoc):
					os.makedirs(pathLoc + "poster")
					os.makedirs(pathLoc + "banner")
					os.makedirs(pathLoc + "backdrop")
					os.makedirs(pathLoc + "infos")
					os.makedirs(pathLoc + "mSearch")
					os.makedirs(pathLoc + "EMC")
			except:
				pass

		return pathLoc
pathLoc = pathLocation().location()

if config.plugins.xtraEvent.tmdbAPI.value != "":
	tmdb_api = config.plugins.xtraEvent.tmdbAPI.value
else:
	tmdb_api = "3c3efcf47c3577558812bb9d64019d65"

if config.plugins.xtraEvent.fanartAPI.value != "":
	fanart_api = config.plugins.xtraEvent.fanartAPI.value
else:
	fanart_api = "6d231536dea4318a88cb2520ce89473b"
