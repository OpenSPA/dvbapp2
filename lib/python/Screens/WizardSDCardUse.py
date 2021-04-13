from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen, ConfigList
from Components.ActionMap import ActionMap
from Components.config import config, NoSave, ConfigYesNo, getConfigListEntry, ConfigSubsection
from os import path, system
from enigma import eEPGCache

config.plugins.sdcard = ConfigSubsection()
config.plugins.sdcard.kodi = NoSave(ConfigYesNo(default=True))
config.plugins.sdcard.movie = NoSave(ConfigYesNo(default=True))
config.plugins.sdcard.timeshift = NoSave(ConfigYesNo(default=True))
config.plugins.sdcard.epg = NoSave(ConfigYesNo(default=True))


class WizardSDCardUse(Screen, ConfigListScreen):

	def __init__(self, session, args=None):
		Screen.__init__(self, session)

		self.list = []
		ConfigListScreen.__init__(self, self.list)

		if path.exists("/media/uSDextra/lost+found"):
			self.createconfig()
		else:
			self.close()

	def createconfig(self):
		if not path.exists("/.kodi"):
			self.list.append(getConfigListEntry(_("Use SDCard for %s storage folder") % "kodi", config.plugins.sdcard.kodi))
		self.list.append(getConfigListEntry(_("Use SDCard for movies storage"), config.plugins.sdcard.movie))
		self.list.append(getConfigListEntry(_("Use SDCard for timeshift storage"), config.plugins.sdcard.timeshift))
		self.list.append(getConfigListEntry(_("Use SDCard for epg storage path"), config.plugins.sdcard.epg))
		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def run(self):
		if config.plugins.sdcard.kodi.value:
			if not path.exists("/media/uSDextra/.kodi"):
				system("mkdir -m 777 /media/uSDextra/.kodi")
			if not path.exists("/.kodi"):
				system("ln -s /media/uSDextra/.kodi /.kodi")
			if not path.exists("/home/root/.kodi"):
				system("ln -s /media/uSDextra/.kodi /home/root/.kodi")
		if config.plugins.sdcard.movie:
			if not path.exists("/media/uSDextra/movie"):
				system("mkdir -m 777 /media/uSDextra/movie")
			config.usage.default_path.value = "/media/uSDextra/movie/"
			config.usage.default_path.save()
		if config.plugins.sdcard.timeshift:
			if not path.exists("/media/uSDextra/timeshift"):
				system("mkdir -m 777 /media/uSDextra/timeshift")
			config.usage.timeshift_path.value = "/media/uSDextra/timeshift"
			config.usage.timeshift_path.save()
		if config.plugins.sdcard.epg:
			name = "epg.dat"
			try:
				name = config.misc.epgcache_filename.value.split("/")[-1]
			except:
				pass
			config.misc.epgcache_filename.value = "/media/uSDextra/" + name
			config.misc.epgcache_filename.save()
			eEPGCache.getInstance().setCacheFile(config.misc.epgcache_filename.value)
		self.close()
