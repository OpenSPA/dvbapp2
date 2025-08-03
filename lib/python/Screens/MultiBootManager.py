from os import popen
from math import ceil
from os import listdir, remove, stat
from os.path import exists, isdir, join, realpath
from re import compile
from shlex import split

from Components.ActionMap import HelpableActionMap
from Components.ChoiceList import ChoiceEntryComponent, ChoiceList
from Components.Console import Console
from Components.Label import Label
from Components.Sources.StaticText import StaticText
from Components.SystemInfo import BoxInfo, getBoxDisplayName
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.Setup import Setup
from Screens.Standby import QUIT_REBOOT, QUIT_RESTART, TryQuitMainloop
from Screens.Console import Console as ConsoleScreen
from Tools.Directories import fileExists, fileWriteLine, fileReadLine
from Tools.MultiBoot import MultiBoot

### OPENSPA [morser] prepare for kexec usb slots ####################
from Components.Harddisk import harddiskmanager, Harddisk
from Components.Console import Console
#####################################################################

##### OPENSPA [morser] Add best sorted function ###############
def best_sort(elem):
	if elem.isdigit():
		x = int(elem)
	elif elem=="R":
		x = 0
	else:
		x = 1000
	return x
###############################################################

ACTION_SELECT = 0
ACTION_CREATE = 1

MOUNT_DEVICE = 0
MOUNT_MOUNTPOINT = 1
MOUNT_FILESYSTEM = 2
MOUNT_OPTIONS = 3
MOUNT_DUMP = 4
MOUNT_FSCK_ORDER = 5
MAX_MOUNT = 6

class MultiBootManager(Screen):
	# NOTE: This embedded skin will be affected by the Choicelist parameters and ChoiceList font in the current skin!  This screen should be skinned.
	# 	See Components/ChoiceList.py to see the hard coded defaults for which this embedded screen has been designed.
	skin = """
	<screen title="MultiBoot Manager" position="center,center" size="900,455">
		<widget name="slotlist" position="10,10" size="880,275" scrollbarMode="showOnDemand" />
		<widget name="description" position="10,e-160" size="880,100" font="Regular;20" valign="bottom" />
		<widget source="key_red" render="Label" position="10,e-50" size="140,40" backgroundColor="key_red" font="Regular;20" conditional="key_red" foregroundColor="key_text" halign="center" noWrap="1" valign="center">
			<convert type="ConditionalShowHide" />
		</widget>
		<widget source="key_green" render="Label" position="160,e-50" size="140,40" backgroundColor="key_green" font="Regular;20" conditional="key_green" foregroundColor="key_text" halign="center" noWrap="1" valign="center">
			<convert type="ConditionalShowHide" />
		</widget>
		<widget source="key_yellow" render="Label" position="310,e-50" size="140,40" backgroundColor="key_yellow" font="Regular;20" conditional="key_yellow" foregroundColor="key_text" halign="center" noWrap="1" valign="center">
			<convert type="ConditionalShowHide" />
		</widget>
		<widget source="key_blue" render="Label" position="460,e-50" size="140,40" backgroundColor="key_blue" font="Regular;20" conditional="key_blue" foregroundColor="key_text" halign="center" noWrap="1" valign="center">
			<convert type="ConditionalShowHide" />
		</widget>
		<widget source="key_help" render="Label" position="e-100,e-50" size="90,40" backgroundColor="key_back" font="Regular;20" conditional="key_help" foregroundColor="key_text" halign="center" noWrap="1" valign="center">
			<convert type="ConditionalShowHide" />
		</widget>
	</screen>"""

	def __init__(self, session, *args):
		Screen.__init__(self, session, enableHelp=True)
		self.setTitle(_("MultiBoot Manager"))
		self["slotlist"] = ChoiceList([ChoiceEntryComponent("", (_("Loading slot information, please wait..."), "Loading"))])
		self["description"] = Label(_("Press the UP/DOWN buttons to select a slot and press OK or GREEN to reboot to that image. If available, YELLOW will either delete or wipe the image. A deleted image can be restored with the BLUE button. A wiped image is completely removed and cannot be restored!"))
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Reboot"))
		self["key_yellow"] = StaticText()
		self["key_blue"] = StaticText()
		self["actions"] = HelpableActionMap(self, ["CancelActions", "NavigationActions"], {
			"cancel": (self.cancel, _("Cancel the slot selection and exit")),
			"close": (self.closeRecursive, _("Cancel the slot selection and exit all menus")),
			"top": (self.keyTop, _("Move to first line / screen")),
			# "pageUp": (self.keyTop, _("Move up a screen")),
			"up": (self.keyUp, _("Move up a line")),
			# "left": (self.keyUp, _("Move up a line")),
			# "right": (self.keyDown, _("Move down a line")),
			"down": (self.keyDown, _("Move down a line")),
			# "pageDown": (self.keyBottom, _("Move down a screen")),
			"bottom": (self.keyBottom, _("Move to last line / screen"))
		}, prio=0, description=_("MultiBoot Manager Actions"))
		self["restartActions"] = HelpableActionMap(self, ["OkSaveActions"], {
			"save": (self.reboot, _("Select the highlighted slot and reboot")),
			"ok": (self.reboot, _("Select the highlighted slot and reboot")),
		}, prio=0, description=_("MultiBoot Manager Actions"))
		self["restartActions"].setEnabled(False)
		self["deleteActions"] = HelpableActionMap(self, ["ColorActions"], {
			"yellow": (self.deleteImage, _("Delete or Wipe the highlighted slot"))
		}, prio=0, description=_("MultiBoot Manager Actions"))
		self["deleteActions"].setEnabled(False)
		self["restoreActions"] = HelpableActionMap(self, ["ColorActions"], {
			"blue": (self.restoreImage, _("Restore the highlighted slot"))
		}, prio=0, description=_("MultiBoot Manager Actions"))
		self["restoreActions"].setEnabled(False)
		if (BoxInfo.getItem("HasKexecMultiboot") or BoxInfo.getItem("HasGPT") or BoxInfo.getItem("HasChkrootMultiboot")) and not BoxInfo.getItem("hasUBIMB"):
			self["moreSlotActions"] = HelpableActionMap(self, ["ColorActions"], {
				"blue": (self.moreSlots, _("Add more slots"))
			}, prio=0, description=_("MultiBoot Manager Actions"))
		self.onLayoutFinish.append(self.layoutFinished)
		self.initialize = True
		self.callLater(self.getImagesList)

	def layoutFinished(self):
		self["slotlist"].instance.enableAutoNavigation(False)

	def getImagesList(self):
		MultiBoot.getSlotImageList(self.getSlotImageListCallback)

	def getSlotImageListCallback(self, slotImages):
		imageList = []
		if slotImages:
			slotCode, bootCode = MultiBoot.getCurrentSlotAndBootCodes()
			slotImageList = sorted(slotImages.keys(), key = best_sort)  ##### OPENSPA [morser] Add best sorted function ###############
			currentMsg = "  -  %s" % _("Current")
			slotMsg = _("Slot '%s' %s: %s%s")
			imageLists = {}
			for slot in slotImageList:
				for boot in slotImages[slot]["bootCodes"]:
					if imageLists.get(boot) is None:
						imageLists[boot] = []
					current = currentMsg if boot == bootCode and slot == slotCode else ""
					device = slotImages[slot]["device"]
					slotType = "eMMC" if "mmcblk" in device else "MTD" if "mtd" in device else "UBI" if "ubi" in device else "USB"
					imageLists[boot].append(ChoiceEntryComponent("none" if boot else "", (slotMsg % (slot, slotType, slotImages[slot]["imagename"], current), (slot, boot, slotImages[slot]["status"], slotImages[slot]["ubi"], current != ""))))
			for bootCode in sorted(imageLists.keys()):
				if bootCode == "":
					continue
				imageList.append(ChoiceEntryComponent("", (MultiBoot.getBootCodeDescription(bootCode), None)))
				imageList.extend(imageLists[bootCode])
			if "" in imageLists:
				imageList.extend(imageLists[""])
			if hasattr(self, "initialize"):
				self.initialize = False
				for index, item in enumerate(imageList):
					if item[0][1] and item[0][1][4]:
						break
			else:
				index = self["slotlist"].getSelectedIndex()
		else:
			imageList.append(ChoiceEntryComponent("", (_("No slot images found"), "Void")))
			index = 0
		self["slotlist"].setList(imageList)
		self["slotlist"].moveToIndex(index)
		self.selectionChanged()

	def cancel(self):
		self.close()

	def closeRecursive(self):
		self.close(True)

	def deleteImage(self):
		currentSelected = self["slotlist"].l.getCurrentSelection()[0]
		slot = currentSelected[1][0]
		current = currentSelected[1][4]
		if BoxInfo.getItem("HasChkrootMultiboot") and slot == "1" and current and not BoxInfo.getItem("hasUBIMB"):
			self.session.openWithCallback(self.disableChkrootAnswer, MessageBox, _("Are you sure you want to disable Chkroot Multiboot?"), simple=True, windowTitle=self.getTitle())
		else:
			self.session.openWithCallback(self.deleteImageAnswer, MessageBox, "%s\n\n%s" % (self["slotlist"].l.getCurrentSelection()[0][0], _("Are you sure you want to delete this image?")), simple=True, windowTitle=self.getTitle())

	def deleteImageAnswer(self, answer):
		if answer:
			currentSelected = self["slotlist"].l.getCurrentSelection()[0]
			MultiBoot.emptySlot(currentSelected[1][0], self.deleteImageCallback)

	def deleteImageCallback(self, result):
		currentSelected = self["slotlist"].l.getCurrentSelection()[0]
		if result:
			print("[MultiBootManager] %s deletion was not completely successful, status %d!" % (currentSelected[0], result))
		else:
			print("[MultiBootManager] %s marked as deleted." % currentSelected[0])
		self.getImagesList()

	def disableChkrootAnswer(self, answer):
		if answer:
			MultiBoot.wipeChkroot(self.disableChkrootCallback)

	def disableChkrootCallback(self, result):
		if result not in (0, 1):
			print("[MultiBootManager] disable was not completely successful, status %d!" % result)
			self.session.open(MessageBox, _("Disabling Chkroot failed!"), MessageBox.TYPE_ERROR, timeout=5)
		else:
			self.session.open(TryQuitMainloop, QUIT_REBOOT)

	def moreSlots(self):
		if BoxInfo.getItem("HasGPT"):
			self.session.open(GPTSlotManager)
		elif BoxInfo.getItem("HasChkrootMultiboot") and not BoxInfo.getItem("hasUBIMB"):
			self.session.open(ChkrootSlotManager)
		else:
			self.session.open(KexecSlotManager)

	def restoreImage(self):
		currentSelected = self["slotlist"].l.getCurrentSelection()[0]
		MultiBoot.restoreSlot(currentSelected[1][0], self.restoreImageCallback)

	def restoreImageCallback(self, result):
		currentSelected = self["slotlist"].l.getCurrentSelection()[0]
		if result:
			print("[MultiBootManager] %s restoration was not completely successful, status %d!" % (currentSelected[0], result))
		else:
			print("[MultiBootManager] %s restored." % currentSelected[0])
		self.getImagesList()

	def reboot(self):
		currentSelected = self["slotlist"].l.getCurrentSelection()[0]
		MultiBoot.activateSlot(currentSelected[1][0], currentSelected[1][1], self.rebootCallback)

	def rebootCallback(self, result):
		currentSelected = self["slotlist"].l.getCurrentSelection()[0]
		if result:
			print("[MultiBootManager] %s activation was not completely successful, status %d!" % (currentSelected[0], result))
		else:
			print("[MultiBootManager] %s activated." % currentSelected[0])
			self.session.open(TryQuitMainloop, QUIT_REBOOT)

	def selectionChanged(self):
		slotCode = MultiBoot.getCurrentSlotCode()
		currentSelected = self["slotlist"].l.getCurrentSelection()[0]
		slot = currentSelected[1][0]
		status = currentSelected[1][2]
		ubi = currentSelected[1][3]
		current = currentSelected[1][4]
		if BoxInfo.getItem("HasChkrootMultiboot") and slot == "1" and current and not BoxInfo.getItem("hasUBIMB"):
			self["description"].setText(_("Press the UP/DOWN buttons to select a slot, then press OK or GREEN to reboot into that image. If available, YELLOW will disable Multiboot, delete, or wipe the selected image. Press BLUE to add more slots."))
			self["key_green"].setText(_("Reboot"))
			self["key_yellow"].setText(_("Disable"))
			self["key_blue"].setText(_("Add more slots"))
			self["restartActions"].setEnabled(True)
			self["deleteActions"].setEnabled(True)
			self["restoreActions"].setEnabled(False)
			self["moreSlotActions"].setEnabled(True)
		elif slot == slotCode or status in ("android", "androidlinuxse", "recovery"):
			self["key_green"].setText(_("Reboot"))
			self["key_yellow"].setText("")
			self["key_blue"].setText("")
			self["restartActions"].setEnabled(True)
			self["deleteActions"].setEnabled(False)
			self["restoreActions"].setEnabled(False)
		elif status == "unknown":
			self["key_green"].setText("")
			self["key_yellow"].setText("")
			self["key_blue"].setText("")
			self["restartActions"].setEnabled(False)
			self["deleteActions"].setEnabled(False)
			self["restoreActions"].setEnabled(False)
		elif status == "empty":
			self["key_green"].setText("")
			self["key_yellow"].setText("")
			self["key_blue"].setText(_("Restore"))
			self["restartActions"].setEnabled(False)
			self["deleteActions"].setEnabled(False)
			self["restoreActions"].setEnabled(True)
		elif ubi:
			self["key_green"].setText(_("Reboot"))
			self["key_yellow"].setText(_("Wipe"))
			self["key_blue"].setText("")
			self["restartActions"].setEnabled(True)
			self["deleteActions"].setEnabled(True)
			self["restoreActions"].setEnabled(False)
		else:
			self["key_green"].setText(_("Reboot"))
			self["key_yellow"].setText(_("Delete"))
			self["key_blue"].setText("")
			self["restartActions"].setEnabled(True)
			self["deleteActions"].setEnabled(True)
			self["restoreActions"].setEnabled(False)
		if BoxInfo.getItem("HasGPT"):
			self["restoreActions"].setEnabled(False)
			self["moreSlotActions"].setEnabled(True)
			self["key_blue"].setText(_("Add more slots"))

	def keyTop(self):
		self["slotlist"].instance.moveSelection(self["slotlist"].instance.moveTop)
		while self["slotlist"].l.getCurrentSelection()[0][1] is None:
			self["slotlist"].instance.moveSelection(self["slotlist"].instance.moveDown)
		self.selectionChanged()

	def keyUp(self):
		self["slotlist"].instance.moveSelection(self["slotlist"].instance.moveUp)
		while self["slotlist"].l.getCurrentSelection()[0][1] is None:
			self["slotlist"].instance.moveSelection(self["slotlist"].instance.moveUp)
		self.selectionChanged()

	def keyDown(self):
		self["slotlist"].instance.moveSelection(self["slotlist"].instance.moveDown)
		while self["slotlist"].l.getCurrentSelection()[0][1] is None:
			self["slotlist"].instance.moveSelection(self["slotlist"].instance.moveDown)
		self.selectionChanged()

	def keyBottom(self):
		self["slotlist"].instance.moveSelection(self["slotlist"].instance.moveEnd)
		while self["slotlist"].l.getCurrentSelection()[0][1] is None:
			self["slotlist"].instance.moveSelection(self["slotlist"].instance.moveUp)
		self.selectionChanged()

class KexecInit(Screen):
	model = BoxInfo.getItem("model")
	modelMtdRootKernel = model in ("vuduo4k", "vuduo4kse") and ["mmcblk0p9", "mmcblk0p6"] or model in ("vusolo4k", "vuultimo4k", "vuuno4k", "vuuno4kse") and ["mmcblk0p4", "mmcblk0p1"] or model == "vuzero4k" and ["mmcblk0p7", "mmcblk0p4"] or ["", ""]

	STARTUP = "kernel=/zImage root=/dev/%s rootsubdir=linuxrootfs0" % modelMtdRootKernel[0]                 # /STARTUP
	STARTUP_RECOVERY = "kernel=/zImage root=/dev/%s rootsubdir=linuxrootfs0" % modelMtdRootKernel[0]        # /STARTUP_RECOVERY
	STARTUP_1 = "kernel=/linuxrootfs1/zImage root=/dev/%s rootsubdir=linuxrootfs1" % modelMtdRootKernel[0]  # /STARTUP_1
	STARTUP_2 = "kernel=/linuxrootfs2/zImage root=/dev/%s rootsubdir=linuxrootfs2" % modelMtdRootKernel[0]  # /STARTUP_2
	STARTUP_3 = "kernel=/linuxrootfs3/zImage root=/dev/%s rootsubdir=linuxrootfs3" % modelMtdRootKernel[0]  # /STARTUP_3

	def __init__(self, session, *args):
		Screen.__init__(self, session, enableHelp=True)
		self.skinName = ["KexecInit", "Setup"]
		self.setTitle(_("Kexec MultiBoot Manager"))
		self.kexec_files = fileExists("/usr/bin/kernel_auto.bin") and fileExists("/usr/bin/STARTUP.cpio.gz")
		self.kexec_installed = fileExists("/STARTUP.cpio.gz") and fileExists("/STARTUP")
		if self.kexec_files:
			self.hdd = None
			self.usb = None
			txtgreen = _("Enable")
		else:
			self.hdd, self.usb = self.getHDD()
			txtgreen = ""
		txtdes = _("Press Green key to enable MultiBoot!\n\nWill reboot within 10 seconds,\nunless you have eMMC slots to restore.\nRestoring eMMC slots can take from 1 -> 5 minutes per slot.")
		self.txt = _("The Kexec Multiboot is Disabled")
		if self.kexec_installed:
			txtgreen = self.usb and _("Add Extra USB slots") or ""
			txtdes = _("Press Green key to add more slots in USB\n\nWill reboot within 10 seconds.")
			self.txt = _("The Kexec Multiboot is Enabled")
			self.txt += "\n"
			self.txt +=_("You have 4 slots in the flash")
			if int(self.hiKey)>4:
				self.txt +="\n"
				self.txt +=_("You have %d slots in a usb device") % (int(self.hiKey)-3)
		self["description"] = Label(txtdes)
		self["config"] = Label(self.txt)
		self["key_red"] = StaticText(self.kexec_files and _("Remove forever") or _("Disable"))
		self["key_green"] = StaticText(txtgreen)
		self["actions"] = HelpableActionMap(self, ["OkCancelActions", "ColorActions"], {
			"green": self.keyGreen,
			"ok": self.close,
			"cancel": self.close,
			"red": self.removeFiles,
		}, prio=-1, description=_("Kexec MultiBoot Actions"))

		self.callLater(self.getImages)

	def getImages(self):
		if self.kexec_installed:
			MultiBoot.getSlotImageList(self.getSlotImageListCallback)

	def getSlotImageListCallback(self, slotImages):
		slotImageList = sorted(slotImages.keys(), key = best_sort)
		self.txt += "\n\n"
		for slot in slotImageList:
			typeslot = "eMMC" if "mmcblk" in slotImages[slot]["device"] else "USB      "
			slotx = "'%s' -" % slot
			imagename = slotImages[slot]["imagename"]
			if "root" in imagename.lower() and fileExists("/STARTUP.cpio.gz"):
				date = "%s-%s-%s" % (BoxInfo.getItem("compiledate")[:4],BoxInfo.getItem("compiledate")[4:6],BoxInfo.getItem("compiledate")[-2:])
				revision = BoxInfo.getItem("imgrevision")
				revision = ".%03d" % revision if BoxInfo.getItem("distro") == "openvix" and isinstance(revision, int) else " %s" % revision
				if BoxInfo.getItem("distro").lower() == "openspa":
					revision = ".%s" % BoxInfo.getItem("imgrevision") if isinstance(BoxInfo.getItem("imgrevision"),str) else revision
					dev = BoxInfo.getItem("feedsurl")
					if "beta" in dev:
						revision += " BETA"
				imagename = imagename + "   -   %s %s%s (%s)" % (BoxInfo.getItem("displaydistro", BoxInfo.getItem("distro")), BoxInfo.getItem("imgversion"), revision, date)
			self.txt += "{:<6}:    Slot  {:>4}   -   {}\n".format(typeslot,slot,imagename)

		self["config"].setText(self.txt)

	def getHDD(self):
		usblist = [(hdd.device,not hdd.idle_running) for hdd in harddiskmanager.hdd]
		n = 0
		self.hiKey = ""
		while not self.hiKey.isdigit():
			self.hiKey = sorted(BoxInfo.getItem("canMultiBoot").keys(), key = best_sort, reverse=True)[n]
			n+=1

		hdd = []
		with open("/proc/mounts", "r") as fd:
			xlines = fd.readlines()
			for hddkey in range(len(usblist)):
				if usblist[hddkey][1]:
					for xline in xlines:
						if xline.find(usblist[hddkey][0]) != -1 and "ext4" in xline:
							index = xline.find(usblist[hddkey][0])
							hdd.append(xline[index:index+4])
						else:
							continue
		if not hdd:
			return None, None
		else:
			return hdd, hdd[0][0:3]

	def keyGreen(self):
		if self.kexec_files:
			self.RootInit()
		elif int(self.hiKey) == 3 and self.usb:
			self.KexecUSB()
		elif int(self.hiKey)>3 and self.usb:
			self.session.openWithCallback(self.addMoreSlots, MessageBox, _("Add 4 more Multiboot USB slots after slot %s ?") % self.hiKey, MessageBox.TYPE_YESNO, timeout=30)

	def addMoreSlots(self, answer):
		hiKey = int(self.hiKey)
		if answer is False:
			self.close()
		else:
			data = open("/STARTUP_4","r").read()
			try:
				uuid = data.split()[1].replace("root=","")
			except:
				uuid = None
			if uuid:
				MultiBoot.KexecUSBmoreSlots(self.model[2:], hiKey, uuid)
				self.session.open(TryQuitMainloop, 2)
			else:
				print("[KexecInit] Error in uuid")

	def KexecUSB(self):
		free = Harddisk(self.usb).free()
		print("[KexecInit] USB free space", free)
		if free < 1024:
			des = str(round((float(free)), 2)) + _("MB")
			print("[KexecInit][add USB STARTUP slot] limited free space", des)
			self.session.open(MessageBox, _("[KexecInit][add USB STARTUP slots] - The USB (%s) only has %s free. At least 1024MB is required.") % (self.usb, des), MessageBox.TYPE_INFO, timeout=30)
			return
		Console().ePopen("/sbin/blkid | grep " + "/dev/" + self.hdd[0], self.KexecMountRet)

	def KexecMountRet(self, result=None, retval=None, extra_args=None):
		device_uuid = "UUID=" + result.split("UUID=")[1].split(" ")[0].replace('"', '')
		MultiBoot.KexecUSBslots(self.model[2:], device_uuid)
		self.session.open(TryQuitMainloop, 2)

	def RootInit(self):
		self["actions"].setEnabled(False)  # This function takes time so disable the ActionMap to avoid responding to multiple button presses
		if self.kexec_files:
			self.setTitle(_("Kexec MultiBoot Initialisation - will reboot after 10 seconds."))
			self["description"].setText(_("Kexec MultiBoot Initialisation in progress!\n\nWill reboot after restoring any eMMC slots.\nThis can take from 1 -> 5 minutes per slot."))
			with open("/STARTUP", 'w') as f:
				f.write(self.STARTUP)
			with open("/STARTUP_RECOVERY", 'w') as f:
				f.write(self.STARTUP_RECOVERY)
			with open("/STARTUP_1", 'w') as f:
				f.write(self.STARTUP_1)
			with open("/STARTUP_2", 'w') as f:
				f.write(self.STARTUP_2)
			with open("/STARTUP_3", 'w') as f:
				f.write(self.STARTUP_3)
			cmdlist = []
			cmdlist.append("dd if=/dev/%s of=/zImage" % self.modelMtdRootKernel[1])  # backup old kernel
			cmdlist.append("dd if=/usr/bin/kernel_auto.bin of=/dev/%s" % self.modelMtdRootKernel[1])  # create new kernel
			cmdlist.append("mv /usr/bin/STARTUP.cpio.gz /STARTUP.cpio.gz")  # copy userroot routine
			Console().eBatch(cmdlist, self.RootInitEnd, debug=True)
		else:
			self.session.open(MessageBox, _("Unable to complete - Kexec Multiboot files missing!"), MessageBox.TYPE_INFO, timeout=10)
			self.close()

	def RootInitEnd(self, *args, **kwargs):
		from Screens.Standby import TryQuitMainloop
		MultiBoot.KexecRestoreImages(self.model)
		self.session.open(TryQuitMainloop, 2)

	def RootDeltEnd(self, *args, **kwargs):
		from Screens.Standby import TryQuitMainloop
		self.session.open(TryQuitMainloop, 2)

	def removeFiles(self):
		if self.kexec_files:
			self.session.openWithCallback(self.removeFilesAnswer, MessageBox, _("Really permanently delete MultiBoot files?\n%s") % "(/usr/bin/kernel_auto.bin /usr/bin/STARTUP.cpio.gz)", simple=True)
		else:
			self.session.openWithCallback(self.disableAnswer, MessageBox, _("This action will permanently delete the images in slots 1 to 3. Do you want to make a backup of these images? You will need to have a hard disk or usb. By enabling kexec they will be restored automatically. Backup eMMC slots can take from 1 -> 5 minutes per slot."), simple=True)

	def disableAnswer(self, answer=None):
		if answer:
			if MultiBoot.KexecBackupImages(self.model):
				self.disableKexec()
			else:
				self.session.openWithCallback(self.nobackupAnswer, MessageBox, _("The backup could not be made, do you want to continue? Images in slots 1 to 3 will be lost"), simple=True)
		else:
				self.session.openWithCallback(self.nobackupAnswer, MessageBox, _("Are you sure to continue? Images were lost in slots 1 to 3"), simple=True)

	def nobackupAnswer(self, answer=None):
		if answer:
			self.disableKexec()

	def disableKexec(self):
		self.setTitle(_("Kexec MultiBoot  - will reboot after 10 seconds."))
		cmdlist = []
		cmdlist.append("rm -rf /linuxrootfs*")
		cmdlist.append("dd if=/zImage of=/dev/%s" % self.modelMtdRootKernel[1])  # restore old kernel
		cmdlist.append("mv /STARTUP.cpio.gz /usr/bin/STARTUP.cpio.gz")  # copy userroot routine
		cmdlist.append("rm /STARTUP*") #delete STARTUPS
		Console().eBatch(cmdlist, self.RootDeltEnd, debug=True)

	def removeFilesAnswer(self, answer=None):
		if answer:
			Console().ePopen("rm -rf /usr/bin/kernel_auto.bin /usr/bin/STARTUP.cpio.gz")
			self.close()

class GPTSlotManager(Setup):
	def __init__(self, session):
		def getGreenHelpText():
			return {
				ACTION_SELECT: _("Select a device to use for the additional slots"),
				ACTION_CREATE: _("Create the additional slots on the selected device")
			}.get(self.green, _("Help text uninitialized"))

		self.GPTSlotManagerLocation = ConfigSelection(default=None, choices=[(None, _("<Select a device>"))])
		self.GPTSlotManagerDevice = None
		Setup.__init__(self, session=session, setup="GPTSlotManager")
		self.setTitle(_("Slot Manager"))
		self["fullUIActions"] = HelpableActionMap(self, ["CancelSaveActions"], {
			"cancel": (self.keyCancel, _("Cancel any changed settings and exit")),
			"close": (self.closeRecursive, _("Cancel any changed settings and exit all menus"))
		}, prio=0, description=_("Common Setup Actions"))  # Override the ConfigList "fullUIActions" action map so that we can control the GREEN button here.
		self["actions"] = HelpableActionMap(self, ["ColorActions"], {
			"green": (self.keyGreen, getGreenHelpText)
		}, prio=-1, description=_("Slot Manager Actions"))
		self.console = Console()
		self.deviceData = {}
		self.green = ACTION_SELECT

	def layoutFinished(self):
		Setup.layoutFinished(self)
		self.readDevices()

	def selectionChanged(self):
		Setup.selectionChanged(self)
		self.updateStatus()

	def changedEntry(self):
		Setup.changedEntry(self)
		self.updateStatus()

	def keySelect(self):
		if self.getCurrentItem() == self.GPTSlotManagerLocation:
			self.showDeviceSelection()
		else:
			Setup.keySelect(self)

	def keyGreen(self):
		def restartCallback(answer):
			if answer is True:
				self.session.open(TryQuitMainloop, QUIT_REBOOT)
			else:
				self.close()

		def createSlots():
			createStartupFiles()
			update_bootconfig()
			formatDevice()

		def createStartupFiles():
			files = {
				"STARTUP_5": "root=/dev/mmcblk1p2 rootfstype=ext4 kernel=/kernel2.img",
				"STARTUP_6": "root=/dev/mmcblk1p3 rootfstype=ext4 kernel=/kernel3.img",
				"STARTUP_7": "root=/dev/mmcblk1p4 rootfstype=ext4 kernel=/kernel4.img",
				"STARTUP_8": "root=/dev/mmcblk1p5 rootfstype=ext4 kernel=/kernel5.img"
			}
			for filename, content in files.items():
				path = join("/data", filename)
				if not exists(path):
					with open(path, "w") as fd:
						fd.write(f"{content}\n")

		def update_bootconfig():
			bootInfo = """
[SDcard Slot 5]
cmd=fatload mmc 0:1 1080000 /kernel2.img;bootm;
arg=${bootargs} logo=osd0,loaded,0x7f800000 vout=1080p50hz,enable hdmimode=1080p50hz fb_width=1280 fb_height=720 panel_type=lcd_4
[SDcard Slot 6]
cmd=fatload mmc 0:1 1080000 /kernel3.img;bootm;
arg=${bootargs} logo=osd0,loaded,0x7f800000 vout=1080p50hz,enable hdmimode=1080p50hz fb_width=1280 fb_height=720 panel_type=lcd_4
[SDcard Slot 7]
cmd=fatload mmc 0:1 1080000 /kernel4.img;bootm;
arg=${bootargs} logo=osd0,loaded,0x7f800000 vout=1080p50hz,enable hdmimode=1080p50hz fb_width=1280 fb_height=720 panel_type=lcd_4
[SDcard Slot 8]
cmd=fatload mmc 0:1 1080000 /kernel5.img;bootm;
arg=${bootargs} logo=osd0,loaded,0x7f800000 vout=1080p50hz,enable hdmimode=1080p50hz fb_width=1280 fb_height=720 panel_type=lcd_4
"""
			bootConfig = "/data/bootconfig.txt"
			with open(bootConfig, 'r') as file:
				lines = file.readlines()
			mmc_0_present = any("mmc 0" in line for line in lines)
			if not mmc_0_present:
				for i in range(len(lines) - 1, -1, -1):
					if lines[i].strip().startswith("["):
						lines.insert(i, bootInfo.strip() + '\n')
						break
				with open(bootConfig, 'w') as file:
					file.writelines(lines)
			with open(bootConfig, 'r') as file:
				lines = file.readlines()
			recovery_index = None
			for i, line in enumerate(lines):
				if line.strip() == "[   Recovery   ]":
					recovery_index = i
					break
			if recovery_index is not None:
				del lines[recovery_index:recovery_index + 3]
			with open(bootConfig, 'w') as file:
				file.writelines(lines)

		def formatDevice():
			TARGET = "mmcblk1"
			TARGET_DEVICE = f"/dev/{TARGET}"
			DEVICE_LABEL = "dreambox-rootfs"

			if exists(TARGET_DEVICE):
				cmdlist = []
				cmdlist.append(f"for n in {TARGET_DEVICE}* ; do umount -lf $n > /dev/null 2>&1 ; done")
				cmdlist.append(f"/usr/sbin/sgdisk -z {TARGET_DEVICE}")
				cmdlist.append(f"/usr/sbin/parted --script {TARGET_DEVICE} mklabel gpt")
				for i in range(1, 5):
					cmdlist.append(f"/bin/touch /dev/nomount.{TARGET}p{i} > /dev/null 2>&1")
				cmdlist.append(f"/usr/sbin/partprobe {TARGET_DEVICE}")
				cmdlist.append(f"/usr/sbin/parted --script {TARGET_DEVICE} mkpart DREAMCARD fat16 8192s 100MB")
				cmdlist.append(f"/usr/sbin/parted --script {TARGET_DEVICE} mkpart {DEVICE_LABEL} ext4 100MB 25%")
				cmdlist.append(f"/usr/sbin/parted --script {TARGET_DEVICE} mkpart {DEVICE_LABEL} ext4 25% 50%")
				cmdlist.append(f"/usr/sbin/parted --script {TARGET_DEVICE} mkpart {DEVICE_LABEL} ext4 50% 75%")
				cmdlist.append(f"/usr/sbin/parted --script {TARGET_DEVICE} mkpart {DEVICE_LABEL} ext4 75% 100%")
				cmdlist.append(f"/usr/sbin/partprobe {TARGET_DEVICE}")
				cmdlist.append(f"/bin/umount -lf {TARGET_DEVICE}p1 > /dev/null 2>&1")
				cmdlist.append(f"/usr/sbin/mkfs.fat -F 16 -S 512 -v -n DREAMCARD {TARGET_DEVICE}p1")
				for i in range(2, 5):
					cmdlist.append(f"/bin/umount -lf {TARGET_DEVICE}p{i} > /dev/null 2>&1")
					cmdlist.append(f"/sbin/mkfs.ext4 -F {TARGET_DEVICE}p{i}")
				self.session.openWithCallback(formatDeviceCallback, ConsoleScreen, title=self.getTitle(), cmdlist=cmdlist, closeOnSuccess=True)

		def formatDeviceCallback():
			self.session.openWithCallback(restartCallback, MessageBox, _("Restart necessary, restart GUI now?"), MessageBox.TYPE_YESNO, windowTitle=self.getTitle())

		if self.GPTSlotManagerDevice:
			createSlots()
		else:
			self.showDeviceSelection()

	def showDeviceSelection(self):
		def readDevicesCallback():
			choiceList = [
				(_("Cancel"), "")
			]
			for deviceData in self.deviceData.items():
				choiceList.append(("%s (%s)" % (deviceData[1], deviceData[0]), 1))
			self.session.openWithCallback(self.deviceSelectionCallback, MessageBox, text=_("Please select the device or Cancel to cancel the selection."), list=choiceList, windowTitle=self.getTitle())

		self.readDevices(readDevicesCallback)

	def deviceSelectionCallback(self, selection):
		if selection:
			print("[GPTSlotManager] deviceSelectionCallback DEBUG: selection=%s." % selection)
			self.GPTSlotManagerDevice = selection
			locations = self.GPTSlotManagerLocation.getSelectionList()
			path = self.deviceData[selection][0]
			name = self.deviceData[selection][1]
			if (path, path) not in locations:
				locations.append((path, path))
				self.GPTSlotManagerLocation.setSelectionList(default=None, choices=locations)
				self.GPTSlotManagerLocation.value = path
			self.GPTSlotManagerDevice = selection
			self.updateStatus("Found SDCARD: %s" % name)

	def readDevices(self, callback=None):
		def readDevicesCallback(output=None, retVal=None, extraArgs=None):
			def getDeviceID(deviceInfo):
				mode = "UUID="
				for token in deviceInfo:
					if token.startswith(mode):
						return token[len(mode):]
				return None

			print("[GPTSlotManager] readDevicesCallback DEBUG: retVal=%s, output='%s'." % (retVal, output))
			lines = [line for line in output.splitlines() if "/dev/mmcblk1p1" in line]
			self.deviceData = {}
			for (name, hdd) in harddiskmanager.HDDList():
				for line in lines:
					data = split(line.strip())
					if data and data[0][:-1].startswith(hdd.dev_path):
						self.deviceData[1] = (data[0][:-1], name)
			self.updateStatus()
			if callback and callable(callback):
				callback()

		self.console.ePopen(["/sbin/blkid", "/sbin/blkid"], callback=readDevicesCallback)

	def updateStatus(self, footnote=None):
		self.green = ACTION_CREATE if self.GPTSlotManagerDevice else ACTION_SELECT
		self["key_green"].setText({
			ACTION_SELECT: _("Select Device"),
			ACTION_CREATE: _("Create Slots")
		}.get(self.green, _("Invalid")))


class ChkrootInit(Screen):
	skin = """
	<screen name="ChkrootInit" title="Chkroot MultiBoot Manager" position="center,center" size="900,600" resolution="1280,720">
		<widget name="description" position="0,0" size="e,e-50" font="Regular;20" />
		<widget source="key_red" render="Label" position="0,e-40" size="180,40" backgroundColor="key_red" conditional="key_red" font="Regular;20" foregroundColor="key_text" halign="center" valign="center">
			<convert type="ConditionalShowHide" />
		</widget>
		<widget source="key_green" render="Label" position="190,e-40" size="180,40" backgroundColor="key_green" conditional="key_green" font="Regular;20" foregroundColor="key_text" halign="center" valign="center">
			<convert type="ConditionalShowHide" />
		</widget>
		<widget source="key_help" render="Label" position="e-80,e-40" size="80,40" backgroundColor="key_back" conditional="key_help" font="Regular;20" foregroundColor="key_text" halign="center" valign="center">
			<convert type="ConditionalShowHide" />
		</widget>
	</screen>"""

	def __init__(self, session, *args):
		Screen.__init__(self, session, enableHelp=True)
		self.skinName = "KexecInit"
		self.setTitle(_("Chkroot MultiBoot Manager"))
		self["key_red"] = StaticText()
		self["key_green"] = StaticText()
		self["description"] = Label()
		self["actions"] = HelpableActionMap(self, ["OkCancelActions", "ColorActions"], {
			"ok": (self.close, _("Close the Chkroot MultiBoot Manager")),
			"cancel": (self.close, _("Close the Chkroot MultiBoot Manager")),
			"red": (self.disableChkroot, _("Disable the MultiBoot option")),
			"green": (self.ubimbInit if BoxInfo.getItem("hasUBIMB") else self.rootInit, _("Start the Chkroot initialization"))
		}, prio=-1, description=_("Chkroot Manager Actions"))
		if BoxInfo.getItem("HasChkrootMultiboot"):
			self["key_red"].setText(_("Remove Chkroot"))
			self["key_green"].setText("")
			buttondesc = _("Press RED to remove MultiBoot!")
		else:
			self["key_red"].setText(_("Disable Chkroot"))
			self["key_green"].setText(_("Initialize"))
			buttondesc = _("Press GREEN to enable MultiBoot!")
		self.descriptionSuffix = _("The %s %s will reboot within 1 seconds.") % getBoxDisplayName()
		self["description"].setText("%s\n\n%s" % (buttondesc, self.descriptionSuffix))

	def ubimbInit(self):
		self.session.open(UBISlotManager)

	def rootInit(self):
		def rootInitCallback(*args, **kwargs):
			self.session.open(TryQuitMainloop, QUIT_REBOOT)

		if BoxInfo.getItem("canchkroot"):
			self["description"].setText("%s\n\n%s" % (_("Chkroot MultiBoot Initialization in progress!"), self.descriptionSuffix))
			device = "/dev/block/by-name/others"
			mountpoint = "/boot"
			mtdRootFs = BoxInfo.getItem("mtdrootfs")
			mtdKernel = BoxInfo.getItem("mtdkernel")
			machinebuild = BoxInfo.getItem("machinebuild")
			if machinebuild in ("dm900", "dm920", "dm820", "dm7080"):
				with open("/sys/block/mmcblk0/mmcblk0p1/size", "r") as fd:
					sectors = int(fd.read().strip())
				if machinebuild in ("dm900", "dm920"):
					rootMap = [
						("mmcblk0p2", "linuxrootfs1"),
						("mmcblk0p2", "linuxrootfs1")
					]
					rootMap.append(("mmcblk0p3" if sectors < 2097152 else "mmcblk0p2", "linuxrootfs2"))
					rootMap.extend([
						("mmcblk0p3", "linuxrootfs3"),
						("mmcblk0p3", "linuxrootfs4"),
						("mmcblk0p3", "linuxrootfs5"),
						("mmcblk0p3", "linuxrootfs6")
					])
				else:
					rootMap = [
						("mmcblk0p1", "linuxrootfs1"),
						("mmcblk0p1", "linuxrootfs1")
					]
					rootMap.append(("mmcblk0p2" if sectors < 2097152 else "mmcblk0p1", "linuxrootfs2"))
					rootMap.extend([
						("mmcblk0p2", "linuxrootfs3"),
						("mmcblk0p2", "linuxrootfs4")
					])
			else:
				rootMap = [
					(mtdRootFs, "linuxrootfs1"),
					(mtdRootFs, "linuxrootfs1"),
					(mtdRootFs, "linuxrootfs2"),
					(mtdRootFs, "linuxrootfs3"),
					(mtdRootFs, "linuxrootfs4")
				]

			cmdList = [
				f"mkfs.vfat -F 32 -n CHKROOT {device}",
				f"mkdir -p {mountpoint}",
				f"mount {device} {mountpoint}",
			]

			for idx, (rootdev, subdir) in enumerate(rootMap):
				suffix = "" if idx == 0 else f"_{idx}"
				cmdList.append(f"echo 'kernel=/dev/{mtdKernel} root=/dev/{rootdev} rootsubdir={subdir}' > {mountpoint}/STARTUP{suffix}")

			cmdList.append(f"umount {mountpoint}")
			Console().eBatch(cmdList, rootInitCallback, debug=True)

	def removeChkrootCallback(self, answer):
		if answer:
			self["description"].setText("%s\n\n%s" % (_("Chkroot MultiBoot Remove in progress!"), self.descriptionSuffix))
			MultiBoot.getSlotImageList(self.removeSlots)

	def removeSlots(self, slotImages):
		def finalremove(answer):
			pass
		def removeCallback(*args, **kwargs):
			self.session.open(TryQuitMainloop, QUIT_REBOOT)

		if slotImages:
			for slot in slotImages:
				if slotImages[slot]["status"] == "active" and int(slot) > 1:
					MultiBoot.emptySlot(slot, finalremove, True)
			partition = popen("ls -ln /dev/block/by-name/ | grep 'others'").read()
			if "others" in partition:
				partition = partition.split()[-1]
				cmdList = [
					f"echo 0 > {partition}/force_ro",
					f"dd if=/dev/zero of={partition} bs=512"
				]
				Console().eBatch(cmdList, removeCallback, debug=True)

	def disableChkroot(self):
		def disableChkrootCallback(answer):
			if answer:
				fileWriteLine("/etc/.disableChkroot", "disabled\n", source=MODULE_NAME)
				self.close()

		if BoxInfo.getItem("HasChkrootMultiboot"):
			self.session.openWithCallback(self.removeChkrootCallback, MessageBox, _("Really permanently delete MultiBoot Images?") , simple=True)
		else:
			self.session.openWithCallback(disableChkrootCallback, MessageBox, _("Permanently disable the MultiBoot option?"), simple=True)


class ChkrootSlotManager(Setup):
	def __init__(self, session):
		def getGreenHelpText():
			return {
				ACTION_SELECT: _("Select a device to create multiboot slots"),
				ACTION_CREATE: _("Create slots for the selected device")
			}.get(self.green, _("Help text uninitialized"))

		self.ChkrootSlotManagerLocation = ConfigSelection(default=None, choices=[(None, _("<Select a device>"))])
		self.ChkrootSlotManagerSlots = ConfigInteger(default=10, limits=(1, 20))
		self.ChkrootSlotManagerDevice = None
		Setup.__init__(self, session=session, setup="ChkrootSlotManager")
		self.setTitle(_("Slot Manager"))
		self["fullUIActions"] = HelpableActionMap(self, ["CancelSaveActions"], {
			"cancel": (self.keyCancel, _("Cancel any changed settings and exit")),
			"close": (self.closeRecursive, _("Cancel any changed settings and exit all menus"))
		}, prio=0, description=_("Common Setup Actions"))  # Override the ConfigList "fullUIActions" action map so that we can control the GREEN button here.
		self["actions"] = HelpableActionMap(self, ["ColorActions"], {
			"green": (self.keyGreen, getGreenHelpText)
		}, prio=-1, description=_("Slot Manager Actions"))
		self.console = Console()
		self.deviceData = {}
		self.green = ACTION_SELECT

	def layoutFinished(self):
		Setup.layoutFinished(self)
		self.readDevices()

	def selectionChanged(self):
		Setup.selectionChanged(self)
		self.updateStatus()

	def changedEntry(self):
		Setup.changedEntry(self)
		self.updateStatus()

	def keySelect(self):
		if self.getCurrentItem() == self.ChkrootSlotManagerLocation:
			self.showDeviceSelection()
		else:
			Setup.keySelect(self)

	def keyGreen(self):
		if self.ChkrootSlotManagerDevice:
			self.createSlots()
		else:
			self.showDeviceSelection()

	def createSlots(self):
		if not self.ChkrootSlotManagerDevice:
			self.showDeviceSelection()
			return

		TARGET = self.deviceData[self.ChkrootSlotManagerDevice][0].split("/")[-1]
		TARGET_DEVICE = f"/dev/{TARGET}"
		PART_SUFFIX = "p" if "mmcblk" in TARGET else ""
		PART = lambda n: f"{TARGET_DEVICE}{PART_SUFFIX}{n}"
		MOUNTPOINT = "/tmp/boot"
		symlinkPath = "/dev/block/by-name/others"
		if exists(symlinkPath):
			realDevice = realpath(symlinkPath)
			if realDevice == "/dev/mmcblk0boot1":
				try:
					with open("/sys/block/mmcblk0boot1/force_ro", "w") as fn:
						fn.write("0")
				except Exception as e:
					pass

			if exists(TARGET_DEVICE):
				cmdlist = []
				cmdlist.append(f"for n in {TARGET_DEVICE}* ; do umount -lf $n > /dev/null 2>&1 ; done")
				cmdlist.append(f"/usr/sbin/sgdisk -z {TARGET_DEVICE}")
				cmdlist.append(f"/bin/touch /dev/nomount.{TARGET} > /dev/null 2>&1")
				cmdlist.append(f"/usr/sbin/parted --script {TARGET_DEVICE} mklabel gpt")
				cmdlist.append(f"/usr/sbin/partprobe {TARGET_DEVICE}")
				cmdlist.append(f"/usr/sbin/parted --script {TARGET_DEVICE} mkpart rootfs ext4 1MB 100%")
				cmdlist.append(f"/usr/sbin/partprobe {TARGET_DEVICE}")
				cmdlist.append(f"/sbin/mkfs.ext4 -O ^64bit,^extent,^flex_bg,^huge_file,^dir_nlink,^extra_isize,^metadata_csum -F -L rootfs {PART(1)}")
				cmdlist.append(f"/bin/mkdir -p {MOUNTPOINT}")
				cmdlist.append(f"/bin/umount {MOUNTPOINT} > /dev/null 2>&1")
				cmdlist.append(f"/bin/mount {realDevice} {MOUNTPOINT}")
				cmdlist.append(f"find {MOUNTPOINT} -maxdepth 1 -type f -name 'STARTUP_*' -exec grep -q 'extra=true' {{}} \\; -exec rm -f {{}} \\;")
				self.session.openWithCallback(self.formatDeviceCallback, ConsoleScreen, title=self.getTitle(), cmdlist=cmdlist)
		else:
			self.session.open(MessageBox, _("Startup device not found!"), MessageBox.TYPE_ERROR, timeout=5)
			self.close()

	def formatDeviceCallback(self):
		def closeStartUpCallback(answer):
			if answer:
				self.session.open(TryQuitMainloop, QUIT_RESTART)
		MOUNTPOINT = "/tmp/boot"
		mtdRootFs = BoxInfo.getItem("mtdrootfs")
		mtdKernel = BoxInfo.getItem("mtdkernel")
		device = self.ChkrootSlotManagerDevice
		PART_SUFFIX = "p" if "mmcblk" in device else ""
		uuidRootFS = fileReadLine(f"/dev/uuid/{device}{PART_SUFFIX}1", default=None, source=MODULE_NAME)
		diskSize = self.partitionSizeGB(f"/dev/{device}")

		existingNumbers = []
		startupRe = compile(r"^STARTUP_(\d+)$")

		for fname in listdir(MOUNTPOINT):
			match = startupRe.match(fname)
			if match:
				existingNumbers.append(int(match.group(1)))

		startIndex = max(existingNumbers) + 1 if existingNumbers else 1
		maxSlots = min(diskSize, self.ChkrootSlotManagerSlots.value)
		remainingSlots = maxSlots - len(existingNumbers)
		endIndex = startIndex + remainingSlots - 1
		created = 0
		for i in range(startIndex, endIndex + 1):
			startupContent = f"kernel=/dev/{mtdKernel} root=UUID={uuidRootFS} rootsubdir=linuxrootfs{i} rootfstype=ext4 extra=true\n"
			with open(f"{MOUNTPOINT}/STARTUP_{i}", "w") as fd:
				fd.write(startupContent)
			created += 1
		Console().ePopen(["/bin/sync"])
		Console().ePopen(["/bin/umount", "/bin/umount", f"{MOUNTPOINT}"])
		self.session.openWithCallback(closeStartUpCallback, MessageBox, _("Slots have been extended by %d..\n") % created, type=MessageBox.TYPE_INFO, close_on_any_key=True, timeout=10)

	def showDeviceSelection(self):
		def readDevicesCallback():
			choiceList = [(_("Cancel"), None)]
			for device_id, (path, name) in self.deviceData.items():
				choiceList.append(("%s (%s)" % (name, path), device_id))
			self.session.openWithCallback(self.deviceSelectionCallback, MessageBox, text=_("Select target device for slot creation"), list=choiceList, windowTitle=self.getTitle())
		self.readDevices(readDevicesCallback)

	def deviceSelectionCallback(self, selection):
		if not selection:
			return

		print(f"[ChkrootSlotManager] deviceSelectionCallback: selected device ID = {selection}")
		self.ChkrootSlotManagerDevice = selection
		locations = self.ChkrootSlotManagerLocation.getSelectionList()
		path = self.deviceData[selection][0]
		name = self.deviceData[selection][1]
		if (path, path) not in locations:
			locations.append((path, path))
			self.ChkrootSlotManagerLocation.setSelectionList(default=None, choices=locations)
			self.ChkrootSlotManagerLocation.value = path
			self.createSetup()
		self.updateStatus("Selected device: %s" % self.deviceData[selection][1])

	def partitionSizeGB(self, dev):
		try:
			base = dev.replace("/dev/", "")
			path = f"/sys/class/block/{base}/size"
			path = path if exists(path) else f"/sys/block/{base}/size"
			with open(path) as fd:
				blocks = int(fd.read().strip())
				return ceil((blocks * 512) / (1024 * 1024 * 1024))
		except Exception as e:
			return 0

	def readDevices(self, callback=None):
		def readDevicesCallback(output=None, retVal=None, extraArgs=None):
			def getDeviceID(deviceInfo):
				mode = "UUID="
				for token in deviceInfo:
					if token.startswith(mode):
						return token[len(mode):]
				return None

			print("[ChkrootSlotManager] readDevicesCallback DEBUG: retVal=%s, output='%s'." % (retVal, output))
			mtdblack = BoxInfo.getItem("mtdblack") or ""
			blacklist = mtdblack.strip().split()

			self.deviceData = {}

			for (name, hdd) in harddiskmanager.HDDList():
				if any(hdd.dev_path.startswith(black) for black in blacklist) or hdd.dev_path.startswith("/dev/romblock"):
					continue

				deviceID = hdd.dev_path.split("/")[-1]
				self.deviceData[deviceID] = (hdd.dev_path, name)

			self.updateStatus()
			if callback and callable(callback):
				callback()

		self.console.ePopen(["/sbin/blkid", "/sbin/blkid"], callback=readDevicesCallback)

	def updateStatus(self, footnote=None):
		self.green = ACTION_CREATE if self.ChkrootSlotManagerDevice else ACTION_SELECT
		self["key_green"].setText({
			ACTION_SELECT: _("Select Device"),
			ACTION_CREATE: _("Create Slots")
		}.get(self.green, _("Invalid")))


class UBISlotManager(Setup):
	def __init__(self, session):
		def getGreenHelpText():
			return {
				ACTION_SELECT: _("Select a device to create multiboot slots"),
				ACTION_CREATE: _("Create slots for the selected device")
			}.get(self.green, _("Help text uninitialized"))

		self.UBISlotManagerLocation = ConfigSelection(default=None, choices=[(None, _("<Select a device>"))])
		self.UBISlotManagerSlots = ConfigInteger(default=10, limits=(1, 20))
		self.UBISlotManagerDevice = None
		Setup.__init__(self, session=session, setup="UBISlotManager")
		self.setTitle(_("Slot Manager"))
		self["fullUIActions"] = HelpableActionMap(self, ["CancelSaveActions"], {
			"cancel": (self.keyCancel, _("Cancel any changed settings and exit")),
			"close": (self.closeRecursive, _("Cancel any changed settings and exit all menus"))
		}, prio=0, description=_("Common Setup Actions"))  # Override the ConfigList "fullUIActions" action map so that we can control the GREEN button here.
		self["actions"] = HelpableActionMap(self, ["ColorActions"], {
			"green": (self.keyGreen, getGreenHelpText)
		}, prio=-1, description=_("Slot Manager Actions"))
		self.console = Console()
		self.deviceData = {}
		self.green = ACTION_SELECT

	def layoutFinished(self):
		Setup.layoutFinished(self)
		self.readDevices()

	def selectionChanged(self):
		Setup.selectionChanged(self)
		self.updateStatus()

	def changedEntry(self):
		Setup.changedEntry(self)
		self.updateStatus()

	def keySelect(self):
		if self.getCurrentItem() == self.UBISlotManagerLocation:
			self.showDeviceSelection()
		else:
			Setup.keySelect(self)

	def keyGreen(self):
		if self.UBISlotManagerDevice:
			self.createSlots()
		else:
			self.showDeviceSelection()

	def createSlots(self):
		if not self.UBISlotManagerDevice:
			self.showDeviceSelection()
			return

		TARGET = self.deviceData[self.UBISlotManagerDevice][0].split("/")[-1]
		TARGET_DEVICE = f"/dev/{TARGET}"
		PART_SUFFIX = "p" if "mmcblk" in TARGET else ""
		PART = lambda n: f"{TARGET_DEVICE}{PART_SUFFIX}{n}"
		MOUNTPOINT = "/tmp/boot"

		if exists(TARGET_DEVICE):
			cmdlist = []
			cmdlist.append(f"for n in {TARGET_DEVICE}* ; do umount -lf $n > /dev/null 2>&1 ; done")
			cmdlist.append(f"/usr/sbin/sgdisk -z {TARGET_DEVICE}")
			cmdlist.append(f"/bin/touch /dev/nomount.{TARGET} > /dev/null 2>&1")
			cmdlist.append(f"/bin/touch /dev/nomount.{TARGET}1 > /dev/null 2>&1")
			cmdlist.append(f"/usr/sbin/parted --script {TARGET_DEVICE} mklabel gpt")
			cmdlist.append(f"/usr/sbin/partprobe {TARGET_DEVICE}")
			cmdlist.append(f"/usr/sbin/parted --script {TARGET_DEVICE} mkpart startup fat32 8192s 5MB")
			cmdlist.append(f"/usr/sbin/parted --script {TARGET_DEVICE} mkpart rootfs ext4 5MB 100%")
			cmdlist.append(f"/usr/sbin/partprobe {TARGET_DEVICE}")
			cmdlist.append(f"/usr/sbin/mkfs.vfat -F 32 -n STARTUP {PART(1)}")
			cmdlist.append(f"/sbin/mkfs.ext4 -O ^64bit,^extent,^flex_bg,^huge_file,^dir_nlink,^extra_isize,^metadata_csum -F -L rootfs {PART(2)}")
			cmdlist.append(f"/bin/mkdir -p {MOUNTPOINT}")
			cmdlist.append(f"/bin/umount {MOUNTPOINT} > /dev/null 2>&1")
			cmdlist.append(f"/bin/mount {PART(1)} {MOUNTPOINT}")
			self.session.openWithCallback(self.formatDeviceCallback, ConsoleScreen, title=self.getTitle(), cmdlist=cmdlist)

	def formatDeviceCallback(self):
		def closeStartUpCallback(answer):
			if answer:
				self.session.open(TryQuitMainloop, QUIT_REBOOT)
		MOUNTPOINT = "/tmp/boot"
		mtdRootFs = BoxInfo.getItem("mtdrootfs")
		mtdKernel = BoxInfo.getItem("mtdkernel")
		device = self.UBISlotManagerDevice
		PART_SUFFIX = "p" if "mmcblk" in device else ""
		uuidRootFS = fileReadLine(f"/dev/uuid/{device}{PART_SUFFIX}2", default=None, source=MODULE_NAME)
		diskSize = self.partitionSizeGB(f"/dev/{device}")

		machinebuild = BoxInfo.getItem("machinebuild")
		rootfsName = "dreambox-rootfs" if machinebuild == "dm520" else "rootfs"
		startupContent = f"kernel=/dev/{mtdKernel} ubi.mtd=rootfs root=ubi0:{rootfsName} flash=1 rootfstype=ubifs\n"

		with open(f"{MOUNTPOINT}/STARTUP", "w") as fd:
			fd.write(startupContent)
		with open(f"{MOUNTPOINT}/STARTUP_FLASH", "w") as fd:
			fd.write(startupContent)
		count = min(diskSize, self.UBISlotManagerSlots.value)
		for i in range(1, count + 1):
			startupContent = f"kernel=/dev/{mtdKernel} root=UUID={uuidRootFS} rootsubdir=linuxrootfs{i} rootfstype=ext4\n"
			with open(f"{MOUNTPOINT}/STARTUP_{i}", "w") as fd:
				fd.write(startupContent)
		Console().ePopen(["/bin/sync"])
		Console().ePopen(["/bin/umount", "/bin/umount", f"{MOUNTPOINT}"])
		self.session.openWithCallback(closeStartUpCallback, MessageBox, _("%d slots have been created on the device.\n") % count, type=MessageBox.TYPE_INFO, close_on_any_key=True, timeout=10)

	def showDeviceSelection(self):
		def readDevicesCallback():
			choiceList = [(_("Cancel"), None)]
			for device_id, (path, name) in self.deviceData.items():
				choiceList.append(("%s (%s)" % (name, path), device_id))
			self.session.openWithCallback(self.deviceSelectionCallback, MessageBox, text=_("Select target device for slot creation"), list=choiceList, windowTitle=self.getTitle())
		self.readDevices(readDevicesCallback)

	def deviceSelectionCallback(self, selection):
		if not selection:
			return

		print(f"[UBISlotManager] deviceSelectionCallback: selected device ID = {selection}")
		self.UBISlotManagerDevice = selection
		locations = self.UBISlotManagerLocation.getSelectionList()
		path = self.deviceData[selection][0]
		name = self.deviceData[selection][1]
		if (path, path) not in locations:
			locations.append((path, path))
			self.UBISlotManagerLocation.setSelectionList(default=None, choices=locations)
			self.UBISlotManagerLocation.value = path
			self.createSetup()
		self.updateStatus("Selected device: %s" % self.deviceData[selection][1])

	def partitionSizeGB(self, dev):
		try:
			base = dev.replace("/dev/", "")
			path = f"/sys/class/block/{base}/size"
			path = path if exists(path) else f"/sys/block/{base}/size"
			with open(path) as fd:
				blocks = int(fd.read().strip())
				return ceil((blocks * 512) / (1024 * 1024 * 1024))
		except Exception as e:
			return 0

	def readDevices(self, callback=None):
		def readDevicesCallback(output=None, retVal=None, extraArgs=None):
			def getDeviceID(deviceInfo):
				mode = "UUID="
				for token in deviceInfo:
					if token.startswith(mode):
						return token[len(mode):]
				return None

			print("[UBISlotManager] readDevicesCallback DEBUG: retVal=%s, output='%s'." % (retVal, output))
			mtdblack = BoxInfo.getItem("mtdblack") or ""
			blacklist = mtdblack.strip().split()

			self.deviceData = {}

			for (name, hdd) in harddiskmanager.HDDList():
				if any(hdd.dev_path.startswith(black) for black in blacklist) or hdd.dev_path.startswith("/dev/romblock"):
					continue

				deviceID = hdd.dev_path.split("/")[-1]
				self.deviceData[deviceID] = (hdd.dev_path, name)

			self.updateStatus()
			if callback and callable(callback):
				callback()

		self.console.ePopen(["/sbin/blkid", "/sbin/blkid"], callback=readDevicesCallback)

	def updateStatus(self, footnote=None):
		self.green = ACTION_CREATE if self.UBISlotManagerDevice else ACTION_SELECT
		self["key_green"].setText({
			ACTION_SELECT: _("Select Device"),
			ACTION_CREATE: _("Create Slots")
		}.get(self.green, _("Invalid")))
