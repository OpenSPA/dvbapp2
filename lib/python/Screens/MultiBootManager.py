from Components.ActionMap import HelpableActionMap
from Components.ChoiceList import ChoiceEntryComponent, ChoiceList
from Components.Console import Console
from Components.Label import Label
from Components.Sources.StaticText import StaticText
from Screens.HelpMenu import HelpableScreen
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.Standby import QUIT_REBOOT, TryQuitMainloop
from Components.SystemInfo import BoxInfo
from Tools.Directories import fileExists, pathExists
from Tools.MultiBoot import MultiBoot

### OPENSPA [morser] prepare for kexec usb slots ####################
from Components.Harddisk import harddiskmanager, Harddisk
from Components.Console import Console
from Components.SystemInfo import BoxInfo
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

class MultiBootManager(Screen, HelpableScreen):
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
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		Screen.setTitle(self, _("MultiBoot Manager"))
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
			slotMsg = _("Slot '%s': %s%s")
			imageLists = {}
			for slot in slotImageList:
				for boot in slotImages[slot]["bootCodes"]:
					if imageLists.get(boot) is None:
						imageLists[boot] = []
					current = currentMsg if boot == bootCode and slot == slotCode else ""
					imageLists[boot].append(ChoiceEntryComponent("none" if boot else "", (slotMsg % (slot, slotImages[slot]["imagename"], current), (slot, boot, slotImages[slot]["status"], slotImages[slot]["ubi"], current != ""))))
			for bootCode in sorted(imageLists.keys()):
				if bootCode == "":
					continue
				imageList.append(ChoiceEntryComponent("", (MultiBoot.getBootCodeDescription(bootCode), None)))
				imageList.extend(imageLists[bootCode])
			if "" in imageLists:
				imageList.extend(imageLists[""])
			if self.initialize:
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
		if slot == slotCode or status in ("android", "androidlinuxse", "recovery"):
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
		Screen.__init__(self, session)
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
			txtgreen = self.usb and _("Add Extra USB slot") or ""
			txtdes = _("Press Green key to add more slots in USB\n\nWill reboot within 10 seconds.")
			self.txt = _("The Kexec Multiboot is Enabled")
			self.txt += "\n"
			self.txt +=_("You have 4 slots in the flash")
			if int(self.hiKey)>4:
				self.txt +="\n"
				self.txt +=_("You have %d slots in a usb device") % (int(self.hiKey)-3)
		self["description"] = Label(txtdes)
		self["config"] = Label(self.txt)
		self["key_red"] = StaticText(self.kexec_files and _("Remove forever") or "")
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
			boxmodel = BoxInfo.getItem("model")[2:]
			data = open("/STARTUP_4","r").read()
			try:
				uuid = data.split()[1].replace("root=","")
			except:
				uuid = None
			if uuid:
				MultiBoot.KexecUSBmoreSlots(boxmodel, hiKey, uuid)
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
		boxmodel = BoxInfo.getItem("model")[2:]
		MultiBoot.KexecUSBslots(boxmodel, device_uuid)
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
		for usbslot in range(1, 4):
			if pathExists("/media/hdd/%s/linuxrootfs%s" % (self.model, usbslot)):
				Console().ePopen("cp -R /media/hdd/%s/linuxrootfs%s . /" % (self.model, usbslot))
		self.session.open(TryQuitMainloop, 2)

	def removeFiles(self):
		if self.kexec_files:
			self.session.openWithCallback(self.removeFilesAnswer, MessageBox, _("Really permanently delete MultiBoot files?\n%s") % "(/usr/bin/kernel_auto.bin /usr/bin/STARTUP.cpio.gz)", simple=True)

	def removeFilesAnswer(self, answer=None):
		if answer:
			Console().ePopen("rm -rf /usr/bin/kernel_auto.bin /usr/bin/STARTUP.cpio.gz")
			self.close()

