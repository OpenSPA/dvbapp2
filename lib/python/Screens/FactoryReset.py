from errno import ENOENT
from os import _exit, listdir, remove
from os.path import isdir, isfile, join as pathjoin
from shutil import rmtree

from Components.config import ConfigSubsection, ConfigYesNo, NoSave, config
from Components.Console import Console
from Components.Sources.StaticText import StaticText
from Screens.MessageBox import MessageBox
from Screens.ParentalControlSetup import ProtectedScreen
from Screens.Setup import Setup
from Tools.Directories import SCOPE_CONFIG, SCOPE_SKINS, copyFile, resolveFilename


class FactoryReset(Setup, ProtectedScreen):
	def __init__(self, session):
		self.configDir = resolveFilename(SCOPE_CONFIG)
		config.factory = ConfigSubsection()
		config.factory.resetFull = NoSave(ConfigYesNo(default=True))
		config.factory.resetNetwork = NoSave(ConfigYesNo(default=True))
		config.factory.resetBouquets = NoSave(ConfigYesNo(default=True))
		config.factory.resetUserInterfaces = NoSave(ConfigYesNo(default=True))
		config.factory.resetMounts = NoSave(ConfigYesNo(default=True))
		config.factory.resetPlugins = NoSave(ConfigYesNo(default=True))
		config.factory.resetResumePoints = NoSave(ConfigYesNo(default=True))
		config.factory.resetSettings = NoSave(ConfigYesNo(default=True))
		config.factory.resetSkins = NoSave(ConfigYesNo(default=True))
		config.factory.resetTimers = NoSave(ConfigYesNo(default=True))
		config.factory.resetOthers = NoSave(ConfigYesNo(default=True))
		Setup.__init__(self, session=session, setup="FactoryReset")
		ProtectedScreen.__init__(self)
		self["key_green"].text = _("Reset")

	def isProtected(self):
		return config.ParentalControl.configured.value and config.ParentalControl.setuppinactive.value and config.ParentalControl.config_sections.manufacturer_reset.value

	def createSetup(self):
		self.analyzeConfig()
		Setup.createSetup(self)

	def keySave(self):
		self.session.openWithCallback(self.keySaveCallback, MessageBox, _("Selecting 'Yes' will delete the currently selected user data. This action can't be undone. You may want to create a backup before continuing.\n\nAre you sure you want to continue with the factory reset?"), default=False, title=_("Factory Reset"))

	def keySaveCallback(self, answer):
		if not answer:
			return
		self.console = Console()
		if config.factory.resetFull.value:
			print("[FactoryReset] Performing a full factory reset.")
			self.resetNetworkConfig()
			self.deleteFiles(self.configDir, None)
			self.installDefaults()
		else:
			if config.factory.resetNetwork.value:
				print("[FactoryReset] Performing a network configuration reset.")
				self.resetNetworkConfig()
			if config.factory.resetBouquets.value and self.bouquets:
				print("[FactoryReset] Performing a bouquets reset.")
				self.deleteFiles(self.configDir, self.bouquets)
			if config.factory.resetUserInterfaces.value and self.userInterfaces:
				print("[FactoryReset] Performing a user interface reset.")
				self.deleteFiles(self.configDir, self.userInterfaces)
			if config.factory.resetMounts.value and self.mounts:
				print("[FactoryReset] Performing a network mount reset.")
				self.deleteFiles(self.configDir, self.mounts)
			if config.factory.resetPlugins.value and self.plugins:
				print("[FactoryReset] Performing a plugins reset.")
				self.deleteFiles(self.configDir, self.plugins)
			if config.factory.resetResumePoints.value and self.resumePoints:
				print("[FactoryReset] Performing a resume points reset.")
				self.deleteFiles(self.configDir, self.resumePoints)
			if config.factory.resetSettings.value and self.settings:
				print("[FactoryReset] Performing a settings reset.")
				self.deleteFiles(self.configDir, self.settings)
			if config.factory.resetSkins.value and self.skins:
				print("[FactoryReset] Performing a skins reset.")
				self.deleteFiles(self.configDir, self.skins)
			if config.factory.resetTimers.value and self.timers:
				print("[FactoryReset] Performing a timers reset.")
				self.deleteFiles(self.configDir, self.timers)
			if config.factory.resetOthers.value and self.others:
				print("[FactoryReset] Performing an other files reset.")
				self.deleteFiles(self.configDir, self.others)
		print("[FactoryReset] Stopping the active service to display the backdrop.")
		self.session.nav.stopService()
		self.console.ePopen(["/usr/bin/showiframe", "/usr/bin/showiframe", "/usr/share/backdrop.mvi"])
		print("[FactoryReset] Stopping and exiting enigma2.")
		_exit(0)
		self.close()  # We should never get to here!

	def closeConfigList(self, closeParameters=()):  # Suppress the save settings pop up on exit.
		self.close(*closeParameters)

	def analyzeConfig(self):
		self.bouquets = []
		self.userInterfaces = []
		self.mounts = []
		self.plugins = []
		self.resumePoints = []
		self.settings = []
		self.skins = []
		self.timers = []
		self.others = []
		for file in sorted(listdir(self.configDir)):
			if isdir(file):
				self.skins.append(file)
			elif file in ("lamedb", "lamedb5"):
				self.bouquets.append(file)
			elif file in ("keymap.xml", "menu.xml", "setup.xml"):
				self.userInterfaces.append(file)
			elif file in ("automounts.xml",):
				self.mounts.append(file)
			elif file in ("resumepoints.pkl",):
				self.resumePoints.append(file)
			elif file in ("settings",):
				self.settings.append(file)
			elif file in ("autotimer.xml", "pm_timers.xml", "timers.xml"):
				self.timers.append(file)
			elif file.startswith("bouquets."):
				self.bouquets.append(file)
			elif file.startswith("userbouquet."):
				self.bouquets.append(file)
			elif file.endswith(".cache"):
				self.mounts.append(file)
			elif not file.startswith("skin_user") and file.endswith(".xml"):
				self.plugins.append(file)
			elif file.startswith("skin_user") and file.endswith(".xml"):
				self.skins.append(file)
			elif file.endswith(".mvi"):
				self.skins.append(file)
			else:
				# print("[FactoryReset] DEBUG: Unclassified file='%s'." % file)
				self.others.append(file)

	def resetNetworkConfig(self):
		configFile = pathjoin(resolveFilename(SCOPE_SKINS), "defaults", "interfaces")
		if isfile(configFile):
			print("[FactoryReset] Default network configuration file found and being installed.")
			if copyFile(configFile, "/etc/network/interfaces") == 0:
				self.console.ePopen(["/bin/sh", "/etc/init.d/networking", "restart"])

	def deleteFiles(self, path, fileList):
		if fileList is None:
			fileList = sorted(listdir(self.configDir))
		for file in fileList:
			target = pathjoin(path, file)
			try:
				if isdir(target):
					print("[FactoryReset] Removing directory '%s' from '%s'." % (target, self.configDir))
					rmtree(target)
				else:
					print("[FactoryReset] Removing file '%s' from '%s'." % (target, self.configDir))
					remove(target)
			except OSError as err:
				if err.errno != ENOENT:
					print("[FactoryReset] Error %d: Unable to delete '%s'!  (%s)" % (err.errno, target, err.strerror))

	def installDefaults(self):
		defaults = pathjoin(resolveFilename(SCOPE_SKINS), "defaults")
		if isdir(defaults):
			defaultFiles = sorted(listdir(defaults))
			if "interfaces" in defaultFiles:  # Network default is done separately.
				defaultFiles.remove("interfaces")
			if defaultFiles:
				print("[FactoryReset] Copying default configuration files from '%s'." % defaults)
				for file in defaultFiles:
					sourceFile = pathjoin(defaults, file)
					if copyFile(sourceFile, self.configDir):
						print("[FactoryReset] Error: Unable to copy file '%s' to '%s'!" % (sourceFile, self.configDir))
					else:
						print("[FactoryReset] File '%s' copied to '%s'." % (sourceFile, self.configDir))
			else:
				print("[FactoryReset] Note: No default configuration files are available!")
		else:
			print("[FactoryReset] Note: No default configuration directory is available!")
