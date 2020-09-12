# -*- coding: utf-8 -*-
# by digiteng...06.2020, 07.2020, 08.2020
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Components.Label import Label
from Components.ActionMap import ActionMap
from Screens.MessageBox import MessageBox
import Tools.Notifications
import os, re, random
from Components.SelectionList import SelectionList, SelectionEntryComponent
from Components.config import config, configfile, ConfigYesNo, ConfigSubsection, getConfigListEntry, ConfigSelection, ConfigText, ConfigInteger, ConfigSelectionNumber, ConfigDirectory
from Components.ConfigList import ConfigListScreen
from enigma import eTimer, eLabel, eServiceCenter, eServiceReference, ePixmap, eSize, ePoint, loadJPG, iServiceInformation, eEPGCache, getBestPlayableServiceReference, getDesktop
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Components.Pixmap import Pixmap
from PIL import Image, ImageDraw, ImageFilter
from Screens.LocationBox import LocationBox
import requests

desktop_size = getDesktop(0).size().width()
epgcache = eEPGCache.getInstance()

config.plugins.xtraEvent = ConfigSubsection()
config.plugins.xtraEvent.loc = ConfigDirectory(default='')
config.plugins.xtraEvent.searchMOD = ConfigSelection(default = "Current Channel", choices = [("Bouquets"), ("Current Channel")])
config.plugins.xtraEvent.searchNUMBER = ConfigSelectionNumber(0, 999, 1, default=0)
config.plugins.xtraEvent.timer = ConfigSelectionNumber(1, 168, 1, default=1)
config.plugins.xtraEvent.searchMANUELnmbr = ConfigSelectionNumber(0, 999, 1, default=1)
config.plugins.xtraEvent.searchMANUELyear = ConfigInteger(default = 0, limits=(0, 9999))
config.plugins.xtraEvent.imgNmbr = ConfigSelectionNumber(0, 999, 1, default=1)

config.plugins.xtraEvent.searchModManuel = ConfigSelection(default = "TV List", choices = [("TV List"), ("Movies List")])
config.plugins.xtraEvent.EMCloc = ConfigDirectory(default='')

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
# config.plugins.xtraEvent.omdb = ConfigYesNo(default = False)
config.plugins.xtraEvent.maze = ConfigYesNo(default = False)
config.plugins.xtraEvent.fanart = ConfigYesNo(default = False)
config.plugins.xtraEvent.bing = ConfigYesNo(default = False)
config.plugins.xtraEvent.extra = ConfigYesNo(default = False)

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
	("10", "192x108"), 
	("5", "384x216"), 
	("3", "634x357"), 
	("2", "960x540"), 
	("1", "1920x1080")])

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
	if desktop_size <= 1280:
		skin = """
<screen name="xtra" position="0,0" size="1280,720" title="xtraEvent v1" flags="wfNoBorder" backgroundColor="transparent">
  <ePixmap position="0,0" size="1280,720" zPosition="-1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/xtraEvent/pic/xtra_hd.png" transparent="1" />
  <widget source="Title" render="Label" position="40,35" size="745,40" font="Console; 30" foregroundColor="#c5c5c5" backgroundColor="#23262e" transparent="1" />
  <widget name="config" position="40,95" size="745,510" itemHeight="30" font="Regular;24" foregroundColor="#c5c5c5" scrollbarMode="showOnDemand" transparent="1" backgroundColor="#23262e" backgroundColorSelected="#565d6d" foregroundColorSelected="#ffffff" />
  <widget source="help" position="840,600" size="400,26" render="Label" font="Regular;22" foregroundColor="#f3fc92" backgroundColor="#23262e" halign="left" valign="center" transparent="1" />
  <widget name="status" position="840,300" size="400,30" transparent="1" font="Regular;22" foregroundColor="#92f1fc" backgroundColor="#23262e" />
  <widget name="info" position="840,330" size="400,260" transparent="1" font="Regular;22" foregroundColor="#c5c5c5" backgroundColor="#23262e" halign="left" valign="top" />
  <widget source="key_red" render="Label" font="Regular;22" foregroundColor="#c5c5c5" backgroundColor="#23262e" position="45,640" size="170,30" halign="left" transparent="1" zPosition="1" />
  <widget source="key_green" render="Label" font="Regular;22" foregroundColor="#c5c5c5" backgroundColor="#23262e" position="235,640" size="170,30" halign="left" transparent="1" zPosition="1" />
  <widget source="key_yellow" render="Label" font="Regular;22" foregroundColor="#c5c5c5" backgroundColor="#23262e" position="425,640" size="170,30" halign="left" transparent="1" zPosition="1" />
  <widget source="key_blue" render="Label" font="Regular; 20" foregroundColor="#c5c5c5" backgroundColor="#23262e" position="615,640" size="170,30" halign="left" transparent="1" zPosition="1" />
  <widget source="global.CurrentTime" render="Label" position="839,40" size="400,30" font="Console; 25" valign="center" halign="center" transparent="1" foregroundColor="#c5c5c5" backgroundColor="#23262e" zPosition="2">
    <convert type="ClockToText">Default</convert>
  </widget>
  <eLabel name="" text=" INFO" position="1150,640" size="100,30" transparent="1" halign="center" font="Console; 20" />
</screen>
		"""

	else:
		skin = """
<screen name="xtra" position="0,0" size="1920,1080" title="xtraEvent v1" flags="wfNoBorder" backgroundColor="transparent">
  <ePixmap position="0,0" size="1920,1080" zPosition="-1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/xtraEvent/pic/xtra_fhd.png" transparent="1" />
  <widget source="Title" render="Label" position="60,53" size="1118,60" font="Console; 45" foregroundColor="#c5c5c5" backgroundColor="#23262e" transparent="1" />
  <widget name="config" position="60,143" size="1118,765" itemHeight="45" font="Regular;36" foregroundColor="#c5c5c5" scrollbarMode="showOnDemand" transparent="1" backgroundColor="#23262e" backgroundColorSelected="#565d6d" foregroundColorSelected="#ffffff" />
  <widget source="help" position="1260,900" size="600,45" render="Label" font="Regular;33" foregroundColor="#f3fc92" backgroundColor="#23262e" halign="left" valign="center" transparent="1" />
  <widget name="status" position="1260,460" size="600,55" transparent="1" font="Regular;33" foregroundColor="#92f1fc" backgroundColor="#23262e" />
  <widget name="info" position="1260,495" size="600,390" transparent="1" font="Regular;33" foregroundColor="#c5c5c5" backgroundColor="#23262e" halign="left" valign="top" />
  <widget source="key_red" render="Label" font="Regular;33" foregroundColor="#c5c5c5" backgroundColor="#23262e" position="68,960" size="255,45" halign="left" transparent="1" zPosition="1" />
  <widget source="key_green" render="Label" font="Regular;33" foregroundColor="#c5c5c5" backgroundColor="#23262e" position="353,960" size="255,45" halign="left" transparent="1" zPosition="1" />
  <widget source="key_yellow" render="Label" font="Regular;33" foregroundColor="#c5c5c5" backgroundColor="#23262e" position="638,960" size="255,45" halign="left" transparent="1" zPosition="1" />
  <widget source="key_blue" render="Label" font="Regular; 30" foregroundColor="#c5c5c5" backgroundColor="#23262e" position="923,960" size="255,45" halign="left" transparent="1" zPosition="1" />
  <widget source="global.CurrentTime" render="Label" position="1259,70" size="600,55" font="Console; 30" valign="center" halign="center" transparent="1" foregroundColor="#c5c5c5" backgroundColor="#23262e" zPosition="2">
    <convert type="ClockToText">Default</convert>
  </widget>
  <eLabel name="" text=" INFO" position="1725,960" size="150,55" transparent="1" halign="center" font="Console; 30" />
</screen>
		"""

	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)

		self.epgcache = eEPGCache.getInstance()

		list = []
		ConfigListScreen.__init__(self, list, session=session)

		self['key_red'] = Label(_('Close'))
		self['key_green'] = Label(_('Search'))
		self['key_yellow'] = Label(_('Download'))
		self['key_blue'] = Label(_('Manuel Search'))

		self["actions"] = ActionMap(["OkCancelActions", "SetupActions", "DirectionActions", "ColorActions", "EventViewActions", "VirtualKeyboardAction"],
		{
			"left": self.keyLeft,
			"down": self.keyDown,
			"up": self.keyUp,
			"right": self.keyRight,
			"red": self.exit,
			"green": self.search,
			"yellow": self.dwnldFileld,
			"blue": self.ms,
			"cancel": self.exit,
			"ok": self.keyOK,
			"info": self.strg,
			"menu": self.brokenImageRemove,

			# "info": self.about,
		},-1)
		
		self.setTitle(_("xtraEvent v1"))
		self['status'] = Label()
		self['info'] = Label()
		self["help"] = StaticText()
		
		self.timer = eTimer()
		self.timer.callback.append(self.xtraList)
		self.onLayoutFinish.append(self.xtraList)

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
		return

	def delay(self):
		self.timer.start(100, True)

	def xtraList(self):
		for x in self["config"].list:
			if len(x) > 1:
				x[1].save()
		list = []
		list.append(getConfigListEntry("—"*100))
# path location_________________________________________________________________________________________________________________
		list.append(getConfigListEntry("CONFIG MENU", config.plugins.xtraEvent.cnfg, _("general setup...")))
		list.append(getConfigListEntry("—"*100))
		if config.plugins.xtraEvent.cnfg.value:
			list.append(getConfigListEntry("    LOCATION", config.plugins.xtraEvent.loc, _("'OK' select location downloads...")))
			
			list.append(getConfigListEntry("    OPTIMIZE IMAGES", config.plugins.xtraEvent.opt_Images, _("optimize images...")))
			if config.plugins.xtraEvent.opt_Images.value:
				list.append(getConfigListEntry("\tOPTIMIZE IMAGES SELECT", config.plugins.xtraEvent.cnfgSel, _("'OK' select for optimize images...")))
			list.append(getConfigListEntry("    TMDB API", config.plugins.xtraEvent.tmdbAPI, _("enter your own api key...")))
			list.append(getConfigListEntry("    TVDB API", config.plugins.xtraEvent.tvdbAPI, _("enter your own api key...")))
			list.append(getConfigListEntry("    OMDB API", config.plugins.xtraEvent.omdbAPI, _("enter your own api key...")))
			list.append(getConfigListEntry("    FANART API", config.plugins.xtraEvent.fanartAPI, _("enter your own api key...")))
			list.append(getConfigListEntry("—"*100))
# config_________________________________________________________________________________________________________________
			list.append(getConfigListEntry("    SEARCH MODE", config.plugins.xtraEvent.searchMOD, _("select search mode...")))		
			list.append(getConfigListEntry("    SEARCH NEXT EVENTS", config.plugins.xtraEvent.searchNUMBER, _("enter the number of next events...")))
			list.append(getConfigListEntry("    SEARCH LANGUAGE", config.plugins.xtraEvent.searchLang, _("select search language...")))
			list.append(getConfigListEntry("    TIMER", config.plugins.xtraEvent.timerMod, _("select timer update for events..")))
			if config.plugins.xtraEvent.timerMod.value == True:
				list.append(getConfigListEntry("\tTIMER(hours)", config.plugins.xtraEvent.timer, _("..."),))
		list.append(getConfigListEntry("—"*100))
		list.append(getConfigListEntry("IMAGE SOURCES"))
		list.append(getConfigListEntry("—"*100))

# poster__________________________________________________________________________________________________________________
		list.append(getConfigListEntry("POSTER", config.plugins.xtraEvent.poster, _("...")))
		if config.plugins.xtraEvent.poster.value == True:
			list.append(getConfigListEntry("\tTMDB", config.plugins.xtraEvent.tmdb, _("source for poster..."),))
			if config.plugins.xtraEvent.tmdb.value :
				list.append(getConfigListEntry("\tTMDB POSTER SIZE", config.plugins.xtraEvent.TMDBpostersize, _("Choose poster sizes for TMDB")))
				list.append(getConfigListEntry("-"*100))
			list.append(getConfigListEntry("\tTVDB", config.plugins.xtraEvent.tvdb, _("source for poster...")))
			if config.plugins.xtraEvent.tvdb.value :
				list.append(getConfigListEntry("\tTVDB POSTER SIZE", config.plugins.xtraEvent.TVDBpostersize, _("Choose poster sizes for TVDB")))
				list.append(getConfigListEntry("_"*100))
			list.append(getConfigListEntry("\tFANART", config.plugins.xtraEvent.fanart, _("source for poster...")))	
			if config.plugins.xtraEvent.fanart.value:
				list.append(getConfigListEntry("\tFANART POSTER SIZE", config.plugins.xtraEvent.FANART_Poster_Resize, _("Choose poster sizes for FANART")))
				list.append(getConfigListEntry("—"*100))
			list.append(getConfigListEntry("\tMAZE(TV SHOWS)", config.plugins.xtraEvent.maze, _("source for tv shows...")))
# banner__________________________________________________________________________________________________________________
		list.append(getConfigListEntry("BANNER", config.plugins.xtraEvent.banner, _("tvdb and fanart for BANNER...")))

# backdrop_______________________________________________________________________________________________________________
		list.append(getConfigListEntry("BACKDROP", config.plugins.xtraEvent.backdrop, _("source for backdrop...")))
		if config.plugins.xtraEvent.backdrop.value == True:
			list.append(getConfigListEntry("\tTMDB", config.plugins.xtraEvent.tmdb, _("source for backdrop...")))
			if config.plugins.xtraEvent.tmdb.value :
				list.append(getConfigListEntry("\tTMDB BACKDROP SIZE", config.plugins.xtraEvent.TMDBbackdropsize, _("Choose backdrop sizes for TMDB")))
				list.append(getConfigListEntry("_"*100))
			list.append(getConfigListEntry("\tTVDB", config.plugins.xtraEvent.tvdb, _("source for backdrop...")))
			if config.plugins.xtraEvent.tvdb.value :
				list.append(getConfigListEntry("\tTVDB BACKDROP SIZE", config.plugins.xtraEvent.TVDBbackdropsize, _("Choose backdrop sizes for TVDB")))
				list.append(getConfigListEntry("_"*100))
			list.append(getConfigListEntry("\tFANART", config.plugins.xtraEvent.fanart, _("source for backdrop...")))
			if config.plugins.xtraEvent.fanart.value:
				list.append(getConfigListEntry("\tFANART BACKDROP SIZE", config.plugins.xtraEvent.FANART_Backdrop_Resize, _("Choose backdrop sizes for FANART")))
				list.append(getConfigListEntry("_"*100))
			list.append(getConfigListEntry("\tEXTRA", config.plugins.xtraEvent.extra, _("tvmovie.de, bing, google search images...")))
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

	def search(self):
		if config.plugins.xtraEvent.searchMOD.value == "Current Channel":
			self.currentChEpgs() 
		elif config.plugins.xtraEvent.searchMOD.value == "Bouquets":
			self.session.open(selBouquets)

	def currentChEpgs(self):
		if os.path.exists(pathLoc+"events"):
			os.remove(pathLoc+"events")
		try:
			events = None
			ref = self.session.nav.getCurrentlyPlayingServiceReference().toString()
			try:
				events = self.epgcache.lookupEvent(['IBDCTSERNX', (ref, 1, -1, -1)])
				n = config.plugins.xtraEvent.searchNUMBER.value
				for i in range(int(n)):
					title = events[i][4]
					evntNm = re.sub("([\(\[]).*?([\)\]])|(: odc.\d+)|(\d+: odc.\d+)|(\d+ odc.\d+)|(:)|( -(.*?).*)|(,)|!", "", title).rstrip().lower()
					
					open(pathLoc+"events","a+").write("%s\n" % str(evntNm))
				
				if os.path.exists(pathLoc+"events"):
					with open(pathLoc+"events", "r") as f:
						titles = f.readlines()
					titles = list(dict.fromkeys(titles))
					n = len(titles)
					self['info'].setText(_("Event to be Scanned : {}".format(str(n))))
				self.dwnldFileld()
			except:
				pass
		except:
			pass

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

	def ms(self):
		self.session.open(manuelSearch)

	def dwnldFileld(self):
		from download import download
		download()

	def exit(self):
		for x in self["config"].list:
			if len(x) > 1:
				x[1].save()
		configfile.save()
		self.close()

class manuelSearch(Screen, ConfigListScreen):
	if desktop_size <= 1280:
		skin = """
  <screen name="manuelSearch" position="center,center" size="1280,720" title="Manuel Search..." backgroundColor="#ffffff" flags="wfNoBorder">
	<ePixmap position="0,0" size="1280,720" zPosition="-1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/xtraEvent/pic/xtra_hd.png" transparent="1" />
    <widget source="Title" render="Label" position="40,40" size="745,40" font="Console; 30" foregroundColor="#c5c5c5" backgroundColor="#23262e" transparent="1" />
	<widget source="session.CurrentService" render="Label" position="40,80" size="638,40" zPosition="2" font="Console; 30" transparent="1" backgroundColor="#23262e" valign="center">
		<convert type="ServiceName">Name</convert>
	</widget>
	<widget name="config" position="40,150" size="745,550" itemHeight="30" font="Regular;24" foregroundColor="#c5c5c5" scrollbarMode="showOnDemand" transparent="1" backgroundColor="#23262e" backgroundColorSelected="#565d6d" foregroundColorSelected="#ffffff" />
    <widget name="status" position="40,560" size="745,60" transparent="1" font="Regular;24" foregroundColor="#92f1fc" backgroundColor="#23262e" />
    <widget name="info" position="840,640" size="400,30" transparent="1" font="Regular;22" halign="center" foregroundColor="#c5c5c5" backgroundColor="#23262e" />
    <widget name="Picture" position="840,320" size="185,278" zPosition="5" transparent="1" />
	
	<widget source="key_red" render="Label" font="Regular;22" foregroundColor="#c5c5c5" backgroundColor="#23262e" position="40,640" size="170,30" halign="left" transparent="1" zPosition="1" />
    <widget source="key_green" render="Label" font="Regular;22" foregroundColor="#c5c5c5" backgroundColor="#23262e" position="230,640" size="170,30" halign="left" transparent="1" zPosition="1" />
    <widget source="key_yellow" render="Label" font="Regular;22" foregroundColor="#c5c5c5" backgroundColor="#23262e" position="420,640" size="170,30" halign="left" transparent="1" zPosition="1" />
    <widget source="key_blue" render="Label" font="Regular;22" foregroundColor="#c5c5c5" backgroundColor="#23262e" position="610,640" size="170,30" halign="left" transparent="1" zPosition="1" />
    <eLabel name="" position="40,120" size="745, 1" backgroundColor="#898989" />

  </screen>
		"""
	else:
		skin = """
  <screen name="manuelSearch" position="center,center" size="1920,1080" title="Manuel Search..." backgroundColor="#ffffff" flags="wfNoBorder">
	<ePixmap position="0,0" size="1920,1080" zPosition="-1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/xtraEvent/pic/xtra_fhd.png" transparent="1" />
    <widget source="Title" render="Label" position="60,60" size="1118,60" font="Console; 45" foregroundColor="#c5c5c5" backgroundColor="#23262e" transparent="1" />
	<widget source="session.CurrentService" render="Label" position="60,120" size="957,60" zPosition="2" font="Console; 45" transparent="1" backgroundColor="#23262e" valign="center">
		<convert type="ServiceName">Name</convert>
	</widget>
	<widget name="config" position="60,225" size="1118,825" itemHeight="45" font="Regular;36" foregroundColor="#c5c5c5" scrollbarMode="showOnDemand" transparent="1" backgroundColor="#23262e" backgroundColorSelected="#565d6d" foregroundColorSelected="#ffffff" />
    <widget name="status" position="60,840" size="1118,90" transparent="1" font="Regular;36" foregroundColor="#92f1fc" backgroundColor="#23262e" />
    <widget name="info" position="1260,960" size="600,45" transparent="1" font="Regular;33" halign="center" foregroundColor="#c5c5c5" backgroundColor="#23262e" />
    <widget name="Picture" position="1260,480" size="278,417" zPosition="5" transparent="1" />
	<widget source="key_red" render="Label" font="Regular;33" foregroundColor="#c5c5c5" backgroundColor="#23262e" position="60,960" size="255,45" halign="left" transparent="1" zPosition="1" />
    <widget source="key_green" render="Label" font="Regular;33" foregroundColor="#c5c5c5" backgroundColor="#23262e" position="345,960" size="255,45" halign="left" transparent="1" zPosition="1" />
    <widget source="key_yellow" render="Label" font="Regular;33" foregroundColor="#c5c5c5" backgroundColor="#23262e" position="630,960" size="255,45" halign="left" transparent="1" zPosition="1" />
    <widget source="key_blue" render="Label" font="Regular;33" foregroundColor="#c5c5c5" backgroundColor="#23262e" position="915,960" size="255,45" halign="left" transparent="1" zPosition="1" />
    <eLabel name="" position="60,180" size="1118, 2" backgroundColor="#898989" />

  </screen>			
		"""

	def __init__(self, session):
		Screen.__init__(self, session)

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
		list.append(getConfigListEntry(_("Next Images"), config.plugins.xtraEvent.imgNmbr))
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
		self['status'].setText(_("Download : "))
		from download import intCheck
		if intCheck():
			if config.plugins.xtraEvent.PB.value == "posters":
				if config.plugins.xtraEvent.imgs.value == "TMDB":
					self.tmdb()
				if config.plugins.xtraEvent.imgs.value == "TVDB":
					self.tvdb()
				if config.plugins.xtraEvent.imgs.value == "FANART":
					self.fanart()
				if config.plugins.xtraEvent.imgs.value == "IMDB(poster)":
					self.imdb()
				if config.plugins.xtraEvent.imgs.value == "Bing":
					self.bing()
				if config.plugins.xtraEvent.imgs.value == "Google":
					self.google()

			if config.plugins.xtraEvent.PB.value == "backdrops":
				if config.plugins.xtraEvent.imgs.value == "TMDB":
					self.tmdb()
				if config.plugins.xtraEvent.imgs.value == "TVDB":
					self.tvdb()
				if config.plugins.xtraEvent.imgs.value == "FANART":
					self.fanart()
				if config.plugins.xtraEvent.imgs.value == "Bing":
					self.bing()
				if config.plugins.xtraEvent.imgs.value == "Google":
					self.google()

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

			self['info'].setText(_("{}/{}    {}    {} ".format(cur,tot,pb_sz,pb_res)))
		except:
			return

	def append(self):
		try:
			self.title = self.title.lower()
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
						evntNm = re.sub("([\(\[]).*?([\)\]])|(: odc.\d+)|(\d+: odc.\d+)|(\d+ odc.\d+)|(:)|( -(.*?).*)|(,)|!", "", self.title).rstrip().lower()
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
		try:
			self.srch = config.plugins.xtraEvent.searchType.value
			self.year = config.plugins.xtraEvent.searchMANUELyear.value
			from requests.utils import quote
			url_tmdb = "https://api.themoviedb.org/3/search/{}?api_key={}&query={}".format(self.srch, tmdb_api, quote(self.title))
			if self.year != 0:
				url_tmdb += "&primary_release_year={}&year={}".format(self.year, self.year)
			
			id = requests.get(url_tmdb).json()['results'][0]['id']
			url = "https://api.themoviedb.org/3/{}/{}?api_key={}&append_to_response=images".format(self.srch, int(id), tmdb_api)
			if config.plugins.xtraEvent.searchLang.value != "":
				url += "&language={}".format(config.plugins.xtraEvent.searchLang.value)
			if config.plugins.xtraEvent.PB.value == "posters":
				sz = config.plugins.xtraEvent.TMDBpostersize.value
			else:
				sz = config.plugins.xtraEvent.TMDBbackdropsize.value
			for i in range(99):
				poster = requests.get(url).json()
				poster = poster['images']['{}'.format(self.pb)][i]['file_path']
				if poster:
					url_poster = "https://image.tmdb.org/t/p/{}{}".format(sz, poster)
					dwnldFile = pathLoc + "mSearch/{}-{}-{}.jpg".format(self.title, self.pb, i+1)
					open(dwnldFile, 'wb').write(requests.get(url_poster, stream=True, allow_redirects=True).content)
					dwnldFile_tot = i+1
					self['status'].setText(_("Download : {}".format(str(dwnldFile_tot))))
					
		except:
			return

	def tvdb(self):
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

			for i in range(99):
				if config.plugins.xtraEvent.PB.value == "posters":
					img_pb = u.json()["data"][i]['{}'.format(config.plugins.xtraEvent.TVDBpostersize.value)]
				else:
					img_pb = u.json()["data"][i]['{}'.format(config.plugins.xtraEvent.TVDBbackdropsize.value)]
				url = "https://artworks.thetvdb.com/banners/{}".format(img_pb)

				dwnldFile = pathLoc + "mSearch/{}-{}-{}.jpg".format(self.title, self.pb, i+1)
				open(dwnldFile, 'wb').write(requests.get(url, stream=True, allow_redirects=True).content)
				dwnldFile_tot = i+1
				self['status'].setText(_("Download : {}".format(str(dwnldFile_tot))))

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
					url_tmdb = "https://api.themoviedb.org/3/search/movie?api_key={}&query={}".format(tmdb_api, quote(self.title))
					if self.year != 0:
						url_tmdb += "&primary_release_year={}&year={}".format(self.year, self.year)
					id = requests.get(url_tmdb).json()['results'][0]['id']
				except:
					pass

			try:
				m_type = config.plugins.xtraEvent.FanartSearchType.value
				url_fanart = "https://webservice.fanart.tv/v3/{}/{}?api_key={}".format(m_type, id, fanart_api)
				fjs = requests.get(url_fanart).json()

				for i in range(99):
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
							
						scl = 1
						im = Image.open(dwnldFile)
						if config.plugins.xtraEvent.PB.value == "posters":
							scl = config.plugins.xtraEvent.FANART_Poster_Resize.value
						if config.plugins.xtraEvent.PB.value == "backdrops":
							scl = config.plugins.xtraEvent.FANART_Backdrop_Resize.value
						im1 = im.resize((im.size[0] // int(scl), im.size[1] // int(scl)), Image.ANTIALIAS)
						im1.save(dwnldFile)
						dwnldFile_tot = i+1
						self['status'].setText(_("Download : {}".format(str(dwnldFile_tot))))
			except:
				pass
	
		except:
			pass

	def imdb(self):
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
					w = open(dwnldFile, 'wb').write(requests.get(url, stream=True, allow_redirects=True).content)
					self['status'].setText(_("Download : 1"))
					w.close()
		except:
			pass

	def bing(self):
		try:
			url="https://www.bing.com/search?q={}+poster+jpg".format(self.title.replace(" ", "+"))
			headers = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"}
			ff = requests.get(url, stream=True, headers=headers).text
			p = re.findall('ihk=\"\/th\?id=(.*?)&', ff)
			n = len(p)
			for i in range(n):
				url = "https://www.bing.com/th?id={}".format(p[i])
				dwnldFile = pathLoc + "mSearch/{}-{}-{}.jpg".format(self.title, self.pb, i+1)
				open(dwnldFile, 'wb').write(requests.get(url, stream=True, allow_redirects=True).content)
				dwnldFile_tot = i+1
				self['status'].setText(_("Download : {}".format(str(dwnldFile_tot))))
		except:
			pass

	def google(self):
		try:
			url = "https://www.google.com/search?q={}&tbm=isch&tbs=sbd:0".format(self.title.replace(" ", "+"))
			headers = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"}
			ff = requests.get(url, stream=True, headers=headers).text
			p = re.findall('"https://(.*?).jpg",(\d*),(\d*)', ff)
			for i in range(9):
				url = "https://" + p[i+1][0] + ".jpg"
				dwnldFile = pathLoc + "mSearch/{}-{}-{}.jpg".format(self.title, self.pb, i+1)
				open(dwnldFile, 'wb').write(requests.get(url, stream=True, allow_redirects=True).content)
				dwnldFile_tot = i+1
				self['status'].setText(_("Download : {}".format(str(dwnldFile_tot))))
		except:
			pass

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
	if desktop_size <= 1280:
		skin = """
  <screen name="selBouquets" position="center,center" size="1280,720" title="xtraEvent v1" backgroundColor="#ffffff">
    <ePixmap position="0,0" size="1280,720" zPosition="-1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/xtraEvent/pic/xtra_hd.png" transparent="1" />
    <widget source="Title" render="Label" position="40,35" size="745,40" font="Console; 30" foregroundColor="#c5c5c5" backgroundColor="#23262e" transparent="1" />
    <widget name="list" position="40,95" size="745,510" itemHeight="30" font="Regular;24" foregroundColor="#c5c5c5" scrollbarMode="showOnDemand" transparent="1" backgroundColor="#23262e" backgroundColorSelected="#565d6d" foregroundColorSelected="#ffffff" />

    <widget name="status" position="840,300" size="400,30" transparent="1" font="Regular;22" foregroundColor="#92f1fc" backgroundColor="#23262e" />
    <widget name="info" position="840,330" size="400,270" transparent="1" font="Regular;10" foregroundColor="#c5c5c5" backgroundColor="#23262e" halign="left" valign="top" />
    <widget source="key_red" render="Label" font="Regular;22" foregroundColor="#c5c5c5" backgroundColor="#23262e" position="40,640" size="170,30" halign="left" transparent="1" zPosition="1" />
    <widget source="key_green" render="Label" font="Regular;22" foregroundColor="#c5c5c5" backgroundColor="#23262e" position="230,640" size="170,30" halign="left" transparent="1" zPosition="1" />
    <widget source="key_yellow" render="Label" font="Regular;22" foregroundColor="#c5c5c5" backgroundColor="#23262e" position="420,640" size="170,30" halign="left" transparent="1" zPosition="1" />
    <widget source="key_blue" render="Label" font="Regular;22" foregroundColor="#c5c5c5" backgroundColor="#23262e" position="610,640" size="170,30" halign="left" transparent="1" zPosition="1" />

    <eLabel name="" text="v1" position="840, 35" size="400, 40" transparent="1" halign="center" font="Console; 30" backgroundColor="#0023262e" />
  </screen>
		"""
	else:
		skin = """
  <screen name="selBouquets" position="center,center" size="1920,1080" title="xtraEvent v1" backgroundColor="#ffffff">
    <ePixmap position="0,0" size="1920,1080" zPosition="-1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/xtraEvent/pic/xtra_fhd.png" transparent="1" />
    <widget source="Title" render="Label" position="60,53" size="1118,60" font="Console; 45" foregroundColor="#c5c5c5" backgroundColor="#23262e" transparent="1" />
    <widget name="list" position="60,143" size="1118,765" itemHeight="45" font="Regular;36" foregroundColor="#c5c5c5" scrollbarMode="showOnDemand" transparent="1" backgroundColor="#23262e" backgroundColorSelected="#565d6d" foregroundColorSelected="#ffffff" />
    <widget name="status" position="1260,450" size="600,45" transparent="1" font="Regular;33" foregroundColor="#92f1fc" backgroundColor="#23262e" />
    <widget name="info" position="1260,495" size="600,405" transparent="1" font="Regular;15" foregroundColor="#c5c5c5" backgroundColor="#23262e" halign="left" valign="top" />
    <widget source="key_red" render="Label" font="Regular;33" foregroundColor="#c5c5c5" backgroundColor="#23262e" position="60,960" size="255,45" halign="left" transparent="1" zPosition="1" />
    <widget source="key_green" render="Label" font="Regular;33" foregroundColor="#c5c5c5" backgroundColor="#23262e" position="345,960" size="255,45" halign="left" transparent="1" zPosition="1" />
    <widget source="key_yellow" render="Label" font="Regular;33" foregroundColor="#c5c5c5" backgroundColor="#23262e" position="630,960" size="255,45" halign="left" transparent="1" zPosition="1" />
    <widget source="key_blue" render="Label" font="Regular;33" foregroundColor="#c5c5c5" backgroundColor="#23262e" position="915,960" size="255,45" halign="left" transparent="1" zPosition="1" />
    <eLabel name="" text="v1" position="1260, 53" size="600, 60" transparent="1" halign="center" font="Console; 45" backgroundColor="#0023262e" />
  </screen>
		"""		

	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		
		self.bouquets = bqtList()
		self.epgcache = eEPGCache.getInstance()
		self.setTitle(_("Bouquet Selection"))
		self.sources = [SelectionEntryComponent(s[0], s[1], 0, (s[0] in ["sources"])) for s in self.bouquets]
		self["list"] = SelectionList(self.sources)

		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
			{
				"cancel": self.cancel,
				"red": self.cancel,
				"green": self.bouquetEpgs,
				"yellow": self["list"].toggleSelection,
				"blue": self["list"].toggleAllSelection,

				"ok": self["list"].toggleSelection,
			}, -2)

		self["key_red"] = Label(_("Cancel"))
		self["key_green"] = Label(_("Save"))
		self["key_yellow"] = Label(_("Select"))
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
				channels = chList(p)
				for ref in channels:
					open(pathLoc + "bqts", "a+").write("%s\n"% str(ref))
					try:
						events = self.epgcache.lookupEvent(['IBDCTSERNX', (ref, 1, -1, -1)])
						n = config.plugins.xtraEvent.searchNUMBER.value
						for i in range(int(n)):
							title = events[i][4]
							evntNm = re.sub("([\(\[]).*?([\)\]])|(: odc.\d+)|(\d+: odc.\d+)|(\d+ odc.\d+)|(:)|( -(.*?).*)|(,)|!", "", title).rstrip().lower()
							
							open(pathLoc+"events","a+").write("%s\n"% str(evntNm))
					except:
						pass
			self.close()
		except:
			pass

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
