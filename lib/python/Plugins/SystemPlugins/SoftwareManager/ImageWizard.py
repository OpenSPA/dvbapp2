from Screens.Wizard import WizardSummary
from Screens.WizardLanguage import WizardLanguage
from Screens.Wizard import wizardManager
from Screens.Rc import Rc
from Screens.Screen import Screen
from Components.Label import Label
from Components.MenuList import MenuList
from Components.PluginComponent import plugins
from Components.Pixmap import Pixmap
from Plugins.Plugin import PluginDescriptor
from Tools.Directories import fileExists, resolveFilename, SCOPE_PLUGINS
from Components.Pixmap import Pixmap, MovingPixmap, MultiPixmap
from os import popen, path, makedirs, listdir, access, stat, rename, remove, W_OK, R_OK
from enigma import eEnv
from boxbranding import getBoxType, getImageDistro
from BackupRestore import InitConfig as BackupRestore_InitConfig

from Components.config import config, getConfigListEntry, ConfigSubsection, ConfigText, ConfigLocations, ConfigBoolean
from Components.Harddisk import harddiskmanager

boxtype = getBoxType()
distro = getImageDistro()

config.plugins.configurationbackup = BackupRestore_InitConfig()

backupfile = "enigma2settingsbackup.tar.gz"

def checkConfigBackup():
	parts = [ (r.description, r.mountpoint) for r in harddiskmanager.getMountedPartitions(onlyhotplug = False)]
	if boxtype in ('maram9', 'classm', 'axodin', 'axodinc', 'starsatlx', 'genius', 'evo', 'galaxym6'):
		parts.append(('mtd backup','/media/backup'))
	for x in parts:
		if x[1] == '/':
			parts.remove(x)
	if len(parts):
		for x in parts:
			if x[1].endswith('/'):
				fullbackupfile =  x[1] + 'backup_' + distro + '_' +  boxtype + '/' + backupfile
				if fileExists(fullbackupfile):
					config.plugins.configurationbackup.backuplocation.setValue(str(x[1]))
					config.plugins.configurationbackup.backuplocation.save()
					config.plugins.configurationbackup.save()
					return x
				fullbackupfile =  x[1] + 'backup/' + backupfile
				if fileExists(fullbackupfile):
					config.plugins.configurationbackup.backuplocation.setValue(str(x[1]))
					config.plugins.configurationbackup.backuplocation.save()
					config.plugins.configurationbackup.save()
					return x
			else:
				fullbackupfile =  x[1] + '/backup_' + distro + '_' +   boxtype + '/' + backupfile
				if fileExists(fullbackupfile):
					config.plugins.configurationbackup.backuplocation.setValue(str(x[1]))
					config.plugins.configurationbackup.backuplocation.save()
					config.plugins.configurationbackup.save()
					return x
				fullbackupfile =  x[1] + '/backup/' + backupfile
				if fileExists(fullbackupfile):
					config.plugins.configurationbackup.backuplocation.setValue(str(x[1]))
					config.plugins.configurationbackup.backuplocation.save()
					config.plugins.configurationbackup.save()
					return x
		return None

def checkBackupFile():
	backuplocation = config.plugins.configurationbackup.backuplocation.value
	if backuplocation.endswith('/'):
		fullbackupfile =  backuplocation + 'backup_' + distro + '_' + boxtype + '/' + backupfile
		if fileExists(fullbackupfile):
			return True
		else:
			fullbackupfile =  backuplocation + 'backup/' + backupfile
			if fileExists(fullbackupfile):
				return True
			else:
				return False
	else:
		fullbackupfile =  backuplocation + '/backup_' + distro + '_' + boxtype + '/' + backupfile
		if fileExists(fullbackupfile):
			return True
		else:
			fullbackupfile =  backuplocation + '/backup/' + backupfile
			if fileExists(fullbackupfile):
				return True
			else:
				return False

if checkConfigBackup() is None:
	backupAvailable = 0
else:
	backupAvailable = 1

class ImageWizard(WizardLanguage, Rc):
	def __init__(self, session):
		self.xmlfile = resolveFilename(SCOPE_PLUGINS, "SystemPlugins/SoftwareManager/imagewizard.xml")
		WizardLanguage.__init__(self, session, showSteps = False, showStepSlider = False)
		Rc.__init__(self)
		self.session = session
		self["wizard"] = Pixmap()
		self["HelpWindow"] = Pixmap()
		self["HelpWindow"].hide()
		#Screen.setTitle(self, _("Welcome..."))
		Screen.setTitle(self, _("ImageWizard"))
		self.selectedDevice = None

	def markDone(self):
		pass

	def listDevices(self):
		list = [ (r.description, r.mountpoint) for r in harddiskmanager.getMountedPartitions(onlyhotplug = False)]
		for x in list:
			result = access(x[1], W_OK) and access(x[1], R_OK)
			if result is False or x[1] == '/':
				list.remove(x)
		for x in list:
			if x[1].startswith('/autofs/'):
				list.remove(x)
		return list

	def deviceSelectionMade(self, index):
		self.deviceSelect(index)

	def deviceSelectionMoved(self):
		self.deviceSelect(self.selection)

	def deviceSelect(self, device):
		self.selectedDevice = device
		config.plugins.configurationbackup.backuplocation.setValue(self.selectedDevice)
		config.plugins.configurationbackup.backuplocation.save()
		config.plugins.configurationbackup.save()


if config.misc.firstrun.value:
	wizardManager.registerWizard(ImageWizard, backupAvailable, priority = 10)

