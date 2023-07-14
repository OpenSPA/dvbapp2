from os import stat, statvfs, makedirs
from os.path import join, isdir
from shlex import split

from Components.config import ConfigBoolean, config, configfile
from Components.Console import Console
from Components.Harddisk import harddiskmanager
from Components.SystemInfo import BoxInfo
from Components.Pixmap import Pixmap
from Screens.FlashExpander import EXPANDER_MOUNT, MOUNT_DEVICE, MOUNT_MOUNTPOINT, MOUNT_FILESYSTEM
from Screens.HelpMenu import ShowRemoteControl
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.VideoWizard import VideoWizard
from Screens.Wizard import wizardManager
from Screens.WizardLanguage import WizardLanguage
from Tools.Directories import fileReadLines, fileWriteLines
from Screens.LocaleSelection import LocaleWizard

MODULE_NAME = __name__.split(".")[-1]

config.misc.firstrun = ConfigBoolean(default=True)
config.misc.languageselected = ConfigBoolean(default = True)  # OPENSPA [morser] For Language Selection in Wizard
config.misc.videowizardenabled = ConfigBoolean(default=True)


class StartWizard(WizardLanguage, ShowRemoteControl):
	def __init__(self, session, silent=True, showSteps=False, neededTag=None):
		self.xmlfile = ["startwizard.xml"]
		WizardLanguage.__init__(self, session, showSteps=False)
		ShowRemoteControl.__init__(self)
		self.deviceData = {}
		self.mountData = None
		self.swapDevice = None
		self.swapDeviceIndex = -1
		self.console = Console()
		flashSize = statvfs('/')
		flashSize = (flashSize.f_frsize * flashSize.f_blocks) // 2 ** 20
		self.smallFlashSize = BoxInfo.getItem("SmallFlash") and flashSize < 130
		self["wizard"] = Pixmap()
		self["HelpWindow"] = Pixmap()
		self["HelpWindow"].hide()
		self.setTitle(_("Start Wizard"))

	def markDone(self):
		# Setup remote control, all STBs have same settings except dm8000 which uses a different setting.
		config.misc.rcused.value = 0 if BoxInfo.getItem("machinebuild") == 'dm8000' else 1
		config.misc.rcused.save()
		config.misc.firstrun.value = False
		config.misc.firstrun.save()
		configfile.save()

	def createSwapFileFlashExpander(self, callback):
		def creataSwapFileCallback(result=None, retVal=None, extraArgs=None):
			fstab = fileReadLines("/etc/fstab", default=[], source=MODULE_NAME)
			print("[FlashExpander] fstabUpdate DEBUG: Begin fstab:\n%s" % "\n".join(fstab))
			fstabNew = [line for line in fstab if "swap" not in line]
			fstabNew.append("%s swap swap defaults 0 0" % fileName)
			fstabNew.append("")
			fileWriteLines("/etc/fstab", "\n".join(fstabNew), source=MODULE_NAME)
			print("[FlashExpander] fstabUpdate DEBUG: Ending fstab:\n%s" % "\n".join(fstabNew))
			messageBox.close()
			if callback:
				callback()

		print("[StartWizard] DEBUG createSwapFileFlashExpander")
		messageBox = self.session.open(MessageBox, _("Please wait, swap is is being created. This could take a few minutes to complete."), MessageBox.TYPE_INFO, enable_input=False, windowTitle=_("Create swap"))
		fileName = join("/.FlashExpander", "swapfile")
		commands = []
		commands.append("/bin/dd if=/dev/zero of='%s' bs=1024 count=131072 2>/dev/null" % fileName)  # Use 128 MB because creation of bigger swap is very slow.
		commands.append("/bin/chmod 600 '%s'" % fileName)
		commands.append("/sbin/mkswap '%s'" % fileName)
		commands.append("/sbin/swapon '%s'" % fileName)
		self.console.eBatch(commands, creataSwapFileCallback, debug=True)

	def createSwapFile(self, callback):
		def getPathMountData(path):
			mounts = fileReadLines("/proc/mounts", [], source=MODULE_NAME)
			print("[StartWizard] getPathMountData DEBUG: path=%s." % path)
			for mount in mounts:
				data = mount.split()
				if data[MOUNT_DEVICE] == path:
					status = stat(data[MOUNT_MOUNTPOINT])
					return (data[MOUNT_MOUNTPOINT], status, data)
			return None

		def creataSwapFileCallback(result=None, retVal=None, extraArgs=None):
			if callback:
				callback()

		print("[StartWizard] DEBUG createSwapFile: %s" % self.swapDevice)
		fileName = "/.swap/swapfile"
		path = self.deviceData[self.swapDevice][0]
		self.mountData = getPathMountData(path)
		fstab = fileReadLines("/etc/fstab", default=[], source=MODULE_NAME)
		print("[StartWizard] fstabUpdate DEBUG: Starting fstab:\n%s" % "\n".join(fstab))
		fstabNew = [line for line in fstab if "swap" not in line]
		mountData = self.mountData[2]
		line = " ".join(("UUID=%s" % self.swapDevice, "/.swap", mountData[MOUNT_FILESYSTEM], "defaults", "0", "0"))
		fstabNew.append(line)
		fstabNew.append("%s swap swap defaults 0 0" % fileName)
		fstabNew.append("")
		fileWriteLines("/etc/fstab", "\n".join(fstabNew), source=MODULE_NAME)
		print("[StartWizard] fstabUpdate DEBUG: Ending fstab:\n%s" % "\n".join(fstabNew))
		makedirs("/.swap", mode=0o755, exist_ok=True)
		commands = []
		commands.append("/bin/mount -a")
		commands.append("/bin/dd if=/dev/zero of='%s' bs=1024 count=131072 2>/dev/null" % fileName)  # Use 128 MB because creation of bigger swap is very slow.
		commands.append("/bin/chmod 600 '%s'" % fileName)
		commands.append("/sbin/mkswap '%s'" % fileName)
		commands.append("/sbin/swapon '%s'" % fileName)
		self.console.eBatch(commands, creataSwapFileCallback, debug=True)

	def swapDeviceList(self):  # Called by startwizard.xml.
		choiceList = []
		for deviceID, deviceData in self.deviceData.items():
			choiceList.append(("%s (%s)" % (deviceData[1], deviceData[0]), deviceID))
		# DEBUG
		print("[StartWizard] DEBUG swapDeviceList: %s" % str(choiceList))

		if len(choiceList) == 0:
			choiceList.append((_("No valid device detected - Press OK"), "."))
		return choiceList

	def swapDeviceSelectionMade(self, index):  # Called by startwizard.xml.
		print("[StartWizard] swapDeviceSelectionMade DEBUG: index='%s'." % index)
		self.swapDeviceIndex = index

	def swapDeviceSelectionMoved(self):  # Called by startwizard.xml.
		print("[StartWizard] DEBUG swapDeviceSelectionMoved: %s" % self.selection)
		self.swapDevice = self.selection

	def readSwapDevices(self, callback=None):
		def readSwapDevicesCallback(output=None, retVal=None, extraArgs=None):
			def getDeviceID(deviceInfo):
				mode = "%s=" % "UUID"
				for token in deviceInfo:
					if token.startswith(mode):
						return token[len(mode):]
				return None

			lines = output.splitlines()
			mountTypemode = " %s=" % "UUID"
			lines = [line for line in lines if mountTypemode in line and ("/dev/sd" in line or "/dev/cf" in line) and ("TYPE=\"ext" in line or "TYPE=\"vfat" in line)]
			self.deviceData = {}
			for (name, hdd) in harddiskmanager.HDDList():
				for line in lines:
					data = split(line.strip())
					if data and data[0][:-1].startswith(hdd.dev_path):
						deviceID = getDeviceID(data)
						if deviceID:
							self.deviceData[deviceID] = (data[0][:-1], name)
			print("[StartWizard] DEBUG readSwapDevicesCallback: %s" % str(self.deviceData))
			if callback:
				callback()

		self.console.ePopen(["/sbin/blkid", "/sbin/blkid"], callback=readSwapDevicesCallback)

	def getFreeMemory(self):
		memInfo = fileReadLines("/proc/meminfo", source=MODULE_NAME)
		return int([line for line in memInfo if "MemFree" in line][0].split(":")[1].strip().split(maxsplit=1)[0]) // 1024

	def isFlashExpanderActive(self):
		return isdir(join("/%s/%s" % (EXPANDER_MOUNT, EXPANDER_MOUNT), "bin"))


# StartEnigma.py#L528ff - RestoreSettings
wizardManager.registerWizard(LocaleWizard, config.misc.languageselected.value, priority=0)  # OPENSPA [morser] In wizard. Language Selection first.
wizardManager.registerWizard(VideoWizard, config.misc.videowizardenabled.value, priority=2)
# FrontprocessorUpgrade FPUpgrade priority = 8
# FrontprocessorUpgrade SystemMessage priority = 9
wizardManager.registerWizard(StartWizard, config.misc.firstrun.value, priority=30)
# StartWizard calls InstallWizard
# NetworkWizard priority = 25
