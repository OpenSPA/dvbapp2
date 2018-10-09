from Plugins.SystemPlugins.Hotplug.plugin import hotplugNotifier
from Components.config import config
from Components.Button import Button
from Components.Label import Label
from Components.ActionMap import ActionMap
from Components.MenuList import MenuList
from Components.FileList import FileList
from Components.Task import Task, Job, job_manager, Condition
from Components.SystemInfo import SystemInfo
from Screens.Console import Console
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Screens.Screen import Screen
from Screens.HelpMenu import HelpableScreen
from Screens.TaskView import JobView
from Tools.Downloader import downloadWithProgress
from Tools.Directories import fileExists
from enigma import fbClass,getDesktop
from Components.Harddisk import harddiskmanager
import urllib2
import os
import shutil
import math
from boxbranding import getBoxType,  getImageDistro, getMachineName, getMachineBrand, getImageVersion, getMachineKernelFile, getMachineRootFile, getMachineBuild, getMachineMtdKernel, getMachineMtdRoot

distro =  getImageDistro()
ImageVersion = getImageVersion()
ROOTFSBIN = getMachineRootFile()
KERNELBIN = getMachineKernelFile()
MTDKERNEL = getMachineMtdKernel()
MTDROOTFS = getMachineMtdRoot()

#############################################################################################################
urlimage = 'https://openspa.webhop.info/Alliance/'
imagePath = '/media/hdd/images'
flashPath = imagePath + '/flash'
flashTmp = '/media/hdd/images/tmp'
ofgwritePath = '/usr/bin/ofgwrite'
#############################################################################################################
def esHD():
	if getDesktop(0).size().width() > 1400:
		return True
	else:
		return False

def Freespace(dev):
	statdev = os.statvfs(dev)
	space = (statdev.f_bavail * statdev.f_frsize) / 1024
	print "[Flash Online] Free space on %s = %i kilobytes" %(dev, space)
	return space

class miJobView(JobView):
	if esHD():
		skin = """
		<screen name="miJobView" position="center,center" size="820,380" title="Donwload">
			<widget source="job_name" render="Label" position="19,22" size="790,50" font="Regular; 20" valign="top" halign="left" transparent="1" />
			<widget source="job_task" render="Label" position="49,95" size="760,60" font="Regular; 21" valign="top" transparent="1" />
			<widget source="job_progress" render="Progress" position="20,199" size="780,12" borderWidth="2" backgroundColor="#002211" borderColor="#99ff00" foregroundColor="#99ff00" />
			<widget source="job_progress" render="Label" position="19,155" size="781,40" font="Regular; 22" foregroundColor="foreground" zPosition="2" halign="center" transparent="1">
				<convert type="ProgressToText" />
			</widget>
			<widget source="job_status" render="Label" position="19,223" size="782,45" font="Regular;23" transparent="1" />
			<widget name="config" position="19,264" size="782,20" transparent="1" />
			<widget source="cancelable" render="Pixmap" pixmap="skin_default/buttons/red_HD.png" position="8,330" size="140,40" alphatest="on">
				<convert type="ConditionalShowHide" />
			</widget>
			<widget source="cancelable" render="FixedLabel" text="Cancel" position="8,330" zPosition="1" size="140,40" font="Regular; 18" halign="center" valign="center" backgroundColor="#9f1313" transparent="1">
				<convert type="ConditionalShowHide" />
			</widget>
			<widget source="finished" render="Pixmap" pixmap="skin_default/buttons/green_HD.png" position="374,330" size="140,40" alphatest="on">
				<convert type="ConditionalShowHide" />
			</widget>
			<widget source="finished" render="FixedLabel" text="OK" font="Regular; 18" halign="center" valign="center" position="374,330" size="140,40" transparent="1" backgroundColor="#1f771f">
				<convert type="ConditionalShowHide" />
			</widget>
			<widget source="backgroundable" render="Pixmap" pixmap="skin_default/buttons/blue.png" position="661,330" size="140,40" alphatest="on">
				<convert type="ConditionalShowHide" />
			</widget>
			<widget source="backgroundable" render="FixedLabel" text="Continue in background" font="Regular; 18" halign="center" valign="center" position="661,330" size="140,40" transparent="1" backgroundColor="#18188b">
				<convert type="ConditionalShowHide" />
			</widget>
			<eLabel name="flecha" position="19,96" size="85,60" text="&gt;&gt;" font="Regular; 17" valign="top" transparent="1" />
			<eLabel name="" position="19,75" size="790,1" backgroundColor="foreground" />
		</screen>"""
	else:
		skin = """
		<screen name="miJobView" position="230,140" size="820,380" title="Donwload">
			<widget source="job_name" render="Label" position="19,22" size="790,50" font="Regular; 20" valign="top" halign="left" transparent="1" />
			<widget source="job_task" render="Label" position="49,95" size="760,60" font="Regular; 21" valign="top" transparent="1" />
			<widget source="job_progress" render="Progress" position="20,199" size="780,12" borderWidth="2" backgroundColor="#002211" borderColor="#99ff00" foregroundColor="#99ff00" />
			<widget source="job_progress" render="Label" position="19,162" size="781,32" font="Regular; 22" foregroundColor="foreground" zPosition="2" halign="center" transparent="1">
				<convert type="ProgressToText" />
			</widget>
			<widget source="job_status" render="Label" position="19,223" size="782,26" font="Regular;23" transparent="1" />
			<widget name="config" position="19,264" size="782,20" transparent="1" />
			<widget source="cancelable" render="Pixmap" pixmap="skin_default/buttons/red.png" position="8,330" size="140,40" alphatest="on">
				<convert type="ConditionalShowHide" />
			</widget>
			<widget source="cancelable" render="FixedLabel" text="Cancel" position="8,330" zPosition="1" size="140,40" font="Regular; 18" halign="center" valign="center" backgroundColor="#9f1313" transparent="1">
				<convert type="ConditionalShowHide" />
			</widget>
			<widget source="finished" render="Pixmap" pixmap="skin_default/buttons/green.png" position="374,330" size="140,40" alphatest="on">
				<convert type="ConditionalShowHide" />
			</widget>
			<widget source="finished" render="FixedLabel" text="OK" font="Regular; 18" halign="center" valign="center" position="374,330" size="140,40" transparent="1" backgroundColor="#1f771f">
				<convert type="ConditionalShowHide" />
			</widget>
			<widget source="backgroundable" render="Pixmap" pixmap="skin_default/buttons/blue.png" position="661,330" size="140,40" alphatest="on">
				<convert type="ConditionalShowHide" />
			</widget>
			<widget source="backgroundable" render="FixedLabel" text="Continue in background" font="Regular; 18" halign="center" valign="center" position="661,330" size="140,40" transparent="1" backgroundColor="#18188b">
				<convert type="ConditionalShowHide" />
			</widget>
			<eLabel name="flecha" position="19,96" size="85,60" text="&gt;&gt;" font="Regular; 17" valign="top" transparent="1" />
			<eLabel name="" position="19,75" size="790,1" backgroundColor="foreground" />
		</screen>"""

	def __init__(self, session, job, parent=None, cancelable = True, backgroundable = True, afterEventChangeable = True):
		JobView.__init__(self, session, job, parent, cancelable, backgroundable, afterEventChangeable)
def chkDevices():
	global net, mont, mediapath
	hddmount = False    
	net = True
	mont=0
	index=[]
	i=0
	listdev=[]
	montados =[]
	for p in harddiskmanager.getMountedPartitions():
		texto=str(p.description)
		montado=str(p.mountpoint)
		montados.append(montado)
		devi = str(p.device)
		if os.path.exists('/media/hdd/'):
			if montado=='/media/hdd/':
				net = False
		elif '/media/hdd' in montado:
			hddmount = True
		if devi != 'None': 
			mont=mont+1
			listdev.append(devi)
			index.append(i)
		i=i+1
	if mont==1:
		mediapath=montados[index[0]]
	elif net and mont==0:
		mediapath="net"
	elif mont==0 and not net:
		mediapath = "nothing"
	elif mont>1:
		mediapath = "Try device"
	imagePath = mediapath+"images"
	return mediapath, imagePath

class FlashOnline(Screen):
	if esHD():
		skin = """
		<screen name="FlashOnline" position="center,center" size="1170,780" title="Flash On the Fly" >
			<ePixmap position="0,720" zPosition="1" size="210,60" pixmap="buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap position="210,720" zPosition="1" size="210,60" pixmap="buttons/green.png" transparent="1" alphatest="on" />
			<ePixmap position="420,720" zPosition="1" size="210,60" pixmap="buttons/yellow.png" transparent="1" alphatest="on" name="kye" />
			<ePixmap position="630,720" zPosition="1" size="210,60" pixmap="buttons/blue.png" transparent="1" alphatest="on" />
			<widget name="key_red" render="Label" position="0,720" zPosition="2" size="210,60" valign="center" halign="center" font="RegularHD;21" transparent="1" borderColor="black" borderWidth="1" />
			<widget name="key_green" render="Label" position="210,720" zPosition="2" size="210,60" valign="center" halign="center" font="RegularHD;21" transparent="1" borderColor="black" borderWidth="1" />
			<widget name="key_yellow" render="Label" position="420,720" zPosition="2" size="210,60" valign="center" halign="center" font="RegularHD;21" transparent="1" borderColor="black" borderWidth="1" />
			<widget name="key_blue" render="Label" position="630,720" zPosition="2" size="210,60" valign="center" halign="center" font="RegularHD;21" transparent="1" borderColor="black" borderWidth="1" />
			<widget name="info-online" position="30,27" zPosition="5" size="1110,90" font="RegularHD;20" halign="left" valign="top" transparent="1" />
			<widget name="info-local" position="30,180" zPosition="5" size="1110,280" font="RegularHD;20" halign="left" valign="top" transparent="1" />
			<eLabel name="fondo1" position="15,13" size="1140,120" zPosition="2" />
			<eLabel name="borde1" position="13,12" size="1143,123" zPosition="0" backgroundColor="foreground" />
			<eLabel name="fondo2" position="15,165" size="1140,313" zPosition="2" />
			<eLabel name="borde2" position="13,163" size="1143,316" zPosition="0" backgroundColor="foreground" />
			<widget font="RegularHD; 22" halign="left" position="12,502" render="Label" size="1132,40" source="global.CurrentTime" transparent="1">
				<convert type="spaSysInfo">Version</convert>
			</widget>
			<widget font="RegularHD; 18" halign="right" position="15,567" render="Label" size="1131,42" source="session.RecordState" transparent="1" noWrap="1" borderColor="#000000" borderWidth="1">
				<convert type="spaSysInfo">MemTotalLong</convert>
			</widget>
			<widget font="RegularHD; 18" halign="right" position="15,615" render="Label" size="1131,91" source="session.CurrentService" transparent="1" valign="top" borderColor="#000000" borderWidth="1">
				<convert type="spaSysInfo">DiskAllSleep</convert>
			</widget>
		</screen>""" 
	else:
		skin = """
		<screen name="FlashOnline" position="center,center" size="780,520" title="Flash On the Fly" >
			<ePixmap position="0,480" zPosition="1" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap position="140,480" zPosition="1" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<ePixmap position="280,480" zPosition="1" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" name="kye" />
			<ePixmap position="420,480" zPosition="1" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
			<widget name="key_red" render="Label" position="0,480" zPosition="2" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" borderColor="black" borderWidth="1" />
			<widget name="key_green" render="Label" position="140,480" zPosition="2" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" borderColor="black" borderWidth="1" />
			<widget name="key_yellow" render="Label" position="280,480" zPosition="2" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" borderColor="black" borderWidth="1" />
			<widget name="key_blue" render="Label" position="420,480" zPosition="2" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" borderColor="black" borderWidth="1" />
			<widget name="info-online" position="20,18" zPosition="5" size="740,60" font="Regular;20" halign="left" valign="top" transparent="1" />
			<widget name="info-local" position="20,120" zPosition="5" size="740,187" font="Regular;20" halign="left" valign="top" transparent="1" />
			<eLabel name="fondo1" position="10,9" size="760,80" zPosition="2" />
			<eLabel name="borde1" position="9,8" size="762,82" zPosition="0" backgroundColor="foreground" />
			<eLabel name="fondo2" position="10,110" size="760,209" zPosition="2" />
			<eLabel name="borde2" position="9,109" size="762,211" zPosition="0" backgroundColor="foreground" />
			<widget font="Regular; 22" halign="left" position="8,335" render="Label" size="755,27" source="global.CurrentTime" transparent="1">
				<convert type="spaSysInfo">Version</convert>
			</widget>
			<widget font="Regular; 18" halign="right" position="10,378" render="Label" size="754,28" source="session.RecordState" transparent="1" noWrap="1" borderColor="#000000" borderWidth="1">
				<convert type="spaSysInfo">MemTotalLong</convert>
			</widget>
			<widget font="Regular; 18" halign="right" position="10,410" render="Label" size="754,61" source="session.CurrentService" transparent="1" valign="top" borderColor="#000000" borderWidth="1">
				<convert type="spaSysInfo">DiskAllSleep</convert>
			</widget>
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		self.selection = 0

		if getMachineBuild() in ("hd51","vs1500","h7","8100s"):
			self.devrootfs = "/dev/mmcblk0p3"
		elif getMachineBuild() in ("gb7252"):
			self.devrootfs = "/dev/mmcblk0p4"
		else:
			self.devrootfs = "/dev/mmcblk1p3"

		self.multi = 1
		self.list = self.list_files("/boot")
		self.MTDKERNEL = getMachineMtdKernel()
		self.MTDROOTFS = getMachineMtdRoot()

		Screen.setTitle(self, _("Flash On the Fly"))
		if SystemInfo["HaveMultiBoot"]:
			self["key_yellow"] = Button(_("STARTUP"))
			self.read_current_multiboot()
		else:
			self["key_yellow"] = Button("")

		self["key_green"] = Button("Online")
		self["key_red"] = Button(_("Exit"))
		self["key_blue"] = Button("Local")

		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"], 
		{
			"blue": self.blue,
			"yellow": self.yellow,
			"green": self.green,
			"red": self.quit,
			"ok": self.green,
			"cancel": self.quit,
		}, -2)

		if SystemInfo["HaveMultiBoot"]:
			if getMachineBuild() in ("gb7252"):
				self.multi = self.read_startup("/boot/" + self.list[self.selection]).split(".",1)[1].split(":",1)[0]
				self.multi = self.multi[-1:]
			else:
				self.multi = self.read_startup("/boot/" + self.list[self.selection]).split(".",1)[1].split(" ",1)[0]
				self.multi = self.multi[-1:]
			print "[Flash Online] MULTI:",self.multi
		mediapath = chkDevices()[0]
		imagePath = chkDevices()[1]
		self.mediapath = mediapath
		self.imagePath = imagePath
		self.flashPath = self.imagePath + '/flash'
		global flashTmp
		flashTmp = self.imagePath + '/tmp'
		if mediapath != "nothing":
			if mont <= 1:
				infolabel=_("Local = Flash a image from local path ") + mediapath
			else:
				infolabel=_("Local = Flash a image from local path device. Try device after pressing blue button")
		else:
			infolabel =_("You need to plug some storage device to flash image")
		self["info-local"] = Label(infolabel)
		self["info-online"] = Label(_("Online = Download a image and flash it"))

	def check_hdd(self):
		if not os.path.exists(self.mediapath):
			self.session.open(MessageBox, _("No device found !!\nPlease make sure you have a device mounted.\n\nExit plugin."), type = MessageBox.TYPE_ERROR)
			return False
		if Freespace(self.mediapath) < 300000:
			self.session.open(MessageBox, _("Not enough free space on device !!\nYou need at least 300Mb free space.\n\nExit plugin."), type = MessageBox.TYPE_ERROR)
			return False
		if not os.path.exists(ofgwritePath):
			self.session.open(MessageBox, _('ofgwrite not found !!\nPlease make sure you have ofgwrite installed in /usr/bin/ofgwrite.\n\nExit plugin.'), type = MessageBox.TYPE_ERROR)
			return False
		if not os.path.exists(self.imagePath):
			try:
				os.mkdir(self.imagePath)
			except:
				pass
		if os.path.exists(self.flashPath):
			try:
				os.system('rm -rf ' + self.flashPath)
			except:
				pass
		try:
			os.mkdir(self.flashPath)
		except:
			pass
		return True

	def quit(self):
		self.close()

	def blue(self):
		if mont == 1:
			if self.check_hdd():
				self.session.open(doFlashImage, online = False, list=self.list[self.selection], multi=self.multi, devrootfs=self.devrootfs, mtdkernel=self.MTDKERNEL, mtdrootfs=self.MTDROOTFS, mediapath=self.mediapath, imagePath=self.imagePath, flashPath=self.flashPath)
			else:
				self.close()
		elif mont > 1:
			self.session.openWithCallback(self.gochkblue,getDevices)

	def green(self):
		if mont == 1:
			if self.check_hdd():
				self.session.open(doFlashImage, online = True, list=self.list[self.selection], multi=self.multi, devrootfs=self.devrootfs, mtdkernel=self.MTDKERNEL, mtdrootfs=self.MTDROOTFS, mediapath=self.mediapath, imagePath=self.imagePath, flashPath=self.flashPath)
			else:
				self.close()
		elif mont > 1:
			self.session.openWithCallback(self.gochk,getDevices)

	def gochk(self,mediapath):
		self.mediapath=mediapath
		imagePath = mediapath + "images"
		self.imagePath = imagePath
		flashPath = imagePath + '/flash'
		self.flashPath = flashPath
		if self.check_hdd():
			self.session.open(doFlashImage, online = True, list=self.list[self.selection], multi=self.multi, devrootfs=self.devrootfs, mediapath=self.mediapath, imagePath = self.imagePath, flashPath = self.flashPath)
		else:
			self.close()

	def gochkblue(self,mediapath):
		self.mediapath=mediapath
		imagePath = mediapath + "images"
		self.imagePath = imagePath
		flashPath = imagePath + '/flash'
		self.flashPath = flashPath
		if self.check_hdd():
			self.session.open(doFlashImage, online = False, list=self.list[self.selection], multi=self.multi, devrootfs=self.devrootfs, mediapath=self.mediapath, imagePath = self.imagePath, flashPath = self.flashPath)
		else:
			self.close()

	def yellow(self):
		if SystemInfo["HaveMultiBoot"]:
			self.selection = self.selection + 1
			if self.selection == len(self.list):
				self.selection = 0
			self["key_yellow"].setText(_(self.list[self.selection]))
			if getMachineBuild() in ("gb7252"):
				self.multi = self.read_startup("/boot/" + self.list[self.selection]).split(".",1)[1].split(":",1)[0]
				self.multi = self.multi[-1:]
			else:
				self.multi = self.read_startup("/boot/" + self.list[self.selection]).split(".",1)[1].split(" ",1)[0]
				self.multi = self.multi[-1:]
			print "[Flash Online] MULTI:",self.multi
			self.devrootfs = self.find_rootfs_dev(self.list[self.selection])
			print "[Flash Online] MULTI rootfs ", self.devrootfs

			self.read_current_multiboot()

	def read_current_multiboot(self):
		if getMachineBuild() in ("hd51","vs1500","h7"):
			if self.list[self.selection] == "Recovery":
				cmdline = self.read_startup("/boot/STARTUP").split("=",3)[3].split(" ",1)[0]
			else:
				cmdline = self.read_startup("/boot/" + self.list[self.selection]).split("=",3)[3].split(" ",1)[0]
		elif getMachineBuild() in ("8100s"):
			if self.list[self.selection] == "Recovery":
				cmdline = self.read_startup("/boot/STARTUP").split("=",4)[4].split(" ",1)[0]
			else:
				cmdline = self.read_startup("/boot/" + self.list[self.selection]).split("=",4)[4].split(" ",1)[0]
		elif getMachineBuild() in ("cc1","sf8008","ustym4kpro"):
			if self.list[self.selection] == "Recovery":
				cmdline = self.read_startup("/boot/STARTUP").split("=",1)[1].split(" ",1)[0]
			else:
				cmdline = self.read_startup("/boot/" + self.list[self.selection]).split("=",1)[1].split(" ",1)[0]
		elif getMachineBuild() in ("osmio4k"):
			if self.list[self.selection] == "Recovery":
				cmdline = self.read_startup("/boot/STARTUP").split("=",1)[1].split(" ",1)[0]
			else:
				cmdline = self.read_startup("/boot/" + self.list[self.selection]).split("=",1)[1].split(" ",1)[0]
		else:
			if self.list[self.selection] == "Recovery":
				cmdline = self.read_startup("/boot/cmdline.txt").split("=",1)[1].split(" ",1)[0]
			else:
				cmdline = self.read_startup("/boot/" + self.list[self.selection]).split("=",1)[1].split(" ",1)[0]
		cmdline = cmdline.lstrip("/dev/")
		self.MTDROOTFS = cmdline
		self.MTDKERNEL = cmdline[:-1] + str(int(cmdline[-1:]) -1)
		print "[Flash Online] kernel device: ",self.MTDKERNEL
		print "[Flash Online] rootfsdevice: ",self.MTDROOTFS

	def read_startup(self, FILE):
		file = FILE
		with open(file, 'r') as myfile:
			data=myfile.read().replace('\n', '')
		myfile.close()
		return data

	def find_rootfs_dev(self, file):
		startup_content = self.read_startup("/boot/" + file)
		return startup_content[startup_content.find("root=")+5:].split()[0]

	def list_files(self, PATH):
		files = []
		if SystemInfo["HaveMultiBoot"]:
			path = PATH
			if getMachineBuild() in ("ustym4kpro","hd51","vs1500","h7","8100s","gb7252","cc1","sf8008","osmio4k"):
				for name in os.listdir(path):
					if name != 'bootname' and os.path.isfile(os.path.join(path, name)):
						try:
							cmdline = self.find_rootfs_dev(name)
						except IndexError:
							continue
						cmdline_startup = self.find_rootfs_dev("STARTUP")
						if (cmdline != cmdline_startup) and (name != "STARTUP"):
							files.append(name)
				files.insert(0,"STARTUP")
			else:
				for name in os.listdir(path):
					if name != 'bootname' and os.path.isfile(os.path.join(path, name)):
						try:
							cmdline = self.read_startup("/boot/" + name).split("=",1)[1].split(" ",1)[0]
						except IndexError:
							continue
						cmdline_startup = self.read_startup("/boot/cmdline.txt").split("=",1)[1].split(" ",1)[0]
						if (cmdline != cmdline_startup) and (name != "cmdline.txt"):
							files.append(name)
				files.insert(0,"cmdline.txt")
		else:
			files = "None"
		return files

class getDevices(Screen):
	if esHD():
		skin = """
		<screen name="getDevices" position="center,center" size="840,600" title="Try device">
			<ePixmap position="0,540" zPosition="1" size="210,60" pixmap="buttons/red_HD.png" transparent="1" alphatest="on" />
			<ePixmap position="210,540" zPosition="1" size="210,60" pixmap="buttons/green_HD.png" transparent="1" alphatest="on" />
			<widget name="key_red" render="Label" position="0,540" zPosition="2" size="210,60" valign="center" halign="center" font="RegularHD;21" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_green" render="Label" position="210,540" zPosition="2" size="210,60" valign="center" halign="center" font="RegularHD;21" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="deviceList" position="13,24" zPosition="1" size="804,253" font="RegularHD; 19" scrollbarMode="showOnDemand" transparent="1" itemHeight="40" />
			<widget name="info-label" position="13,325" zPosition="1" size="804,187" font="RegularHD;20" halign="left" valign="top" transparent="1" />
			<eLabel name="" position="13,298" size="804,1" backgroundColor="grey" />
		</screen>"""
	else:
		skin = """
		<screen name="getDevices" position="center,center" size="560,400" title="Try device">
			<ePixmap position="0,360" zPosition="1" size="140,40" pixmap="buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap position="140,360" zPosition="1" size="140,40" pixmap="buttons/green.png" transparent="1" alphatest="on" />
			<widget name="key_red" render="Label" position="0,360" zPosition="2" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_green" render="Label" position="140,360" zPosition="2" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="deviceList" position="9,16" zPosition="1" size="536,169" font="Regular; 19" scrollbarMode="showOnDemand" transparent="1" />
			<widget name="info-label" position="9,217" zPosition="1" size="536,125" font="Regular;20" halign="left" valign="top" transparent="1" />
			<eLabel name="" position="9,199" size="536,1" backgroundColor="grey" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		Screen.setTitle(self, _("Try device"))
		self["key_green"] = Button(_("Check mounts"))
		self["key_red"] = Button(_("Exit"))
		infolabel=_("By default /media/hdd is selected.\nSelect /media/usb if you want to change device")
		self["info-label"] = Label(infolabel)
		self.devicelist = []
		self["deviceList"] = MenuList(self.devicelist)

		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"], 
		{
			"ok": self.ok,
			"green": self.green,
			"red": self.quit,
			"cancel": self.quit,
		}, -2)

		self.onLayoutFinish.append(self.getList)

	def getList(self):
		self.devicelist = []
		for p in harddiskmanager.getMountedPartitions():
			texto=str(p.description)
			montado=str(p.mountpoint)
			devi = str(p.device)
			if devi != 'None':
				self.devicelist.append(texto + ' - ' + montado)
		self["deviceList"].l.setList(self.devicelist)

	def ok(self):
		sel = self["deviceList"].l.getCurrentSelection()
		mediapath = sel.split(' - ')[1]
		self.close(mediapath)

	def green(self):
		try:
			if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/spaTeam/plugin.pyo"):
				from Plugins.Extensions.spaTeam.MountManager import HddMount
				self.session.openWithCallback(self.back,HddMount)
			elif fileExists("/usr/lib/enigma2/python/Plugins/SystemPlugins/DeviceManager/plugin.pyo"):
				from Plugins.SystemPlugins.DeviceManager.HddSetup import HddSetup
				self.session.openWithCallback(self.back,HddSetup)
		except:
			pass

	def back(self):
		pass

	def quit(self):
		for x in self["deviceList"].list:
			x[1].cancel()
		self.close('Try device')

from time import time

class doFlashImage(Screen):
	if esHD():
		skin = """
		<screen name="doFlashImageSPZ" position="center,center" size="875,855" title="Flash On the fly (select a image)">
			<ePixmap position="0,787" zPosition="1" size="210,60" pixmap="skin_default/buttons/red_HD.png" transparent="1" alphatest="on" />
			<ePixmap position="210,787" zPosition="1" size="210,60" pixmap="skin_default/buttons/green_HD.png" transparent="1" alphatest="on" />
			<ePixmap position="420,787" zPosition="1" size="210,60" pixmap="skin_default/buttons/yellow_HD.png" transparent="1" alphatest="on" />
			<ePixmap position="630,787" zPosition="1" size="210,60" pixmap="skin_default/buttons/blue_HD.png" transparent="1" alphatest="on" />
			<widget name="key_red" borderColor="black" borderWidth="1" render="Label" position="0,787" zPosition="2" size="210,60" valign="center" halign="center" font="Regular; 18" transparent="1" />
			<widget name="key_green" render="Label" position="210,787" zPosition="2" size="210,60" valign="center" halign="center" font="Regular; 18" transparent="1" borderColor="black" borderWidth="1" />
			<widget name="key_yellow" render="Label" position="420,787" zPosition="2" size="210,60" valign="center" halign="center" font="Regular; 18" transparent="1" borderColor="black" borderWidth="1" />
			<widget name="key_blue" render="Label" position="630,787" zPosition="2" size="210,60" valign="center" halign="center" font="Regular; 18" transparent="1" borderColor="black" borderWidth="1" />
			<widget name="imageList" position="7,15" zPosition="1" size="972,750" font="Regular; 19" scrollbarMode="showOnDemand" transparent="1" itemHeight="40"/>
		</screen>"""
	else:
		skin = """
		<screen name="doFlashImageSPZ" position="center,center" size="600,570" title="Flash On the fly (select a image)">
			<ePixmap position="0,525" zPosition="1" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap position="140,525" zPosition="1" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<ePixmap position="280,525" zPosition="1" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
			<ePixmap position="420,525" zPosition="1" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
			<widget name="key_red" borderColor="black" borderWidth="1" render="Label" position="0,525" zPosition="2" size="140,40" valign="center" halign="center" font="Regular; 18" transparent="1" />
			<widget name="key_green" render="Label" position="140,525" zPosition="2" size="140,40" valign="center" halign="center" font="Regular; 18" transparent="1" borderColor="black" borderWidth="1" />
			<widget name="key_yellow" render="Label" position="280,525" zPosition="2" size="140,40" valign="center" halign="center" font="Regular; 18" transparent="1" borderColor="black" borderWidth="1" />
			<widget name="key_blue" render="Label" position="420,525" zPosition="2" size="140,40" valign="center" halign="center" font="Regular; 18" transparent="1" borderColor="black" borderWidth="1" />
			<widget name="imageList" position="9,41" zPosition="1" size="645,475" font="Regular; 19" scrollbarMode="showOnDemand" transparent="1" />
		</screen>"""

	def __init__(self, session, online, list=None, multi=None, devrootfs=None, mtdkernel=None, mtdrootfs=None, mediapath='/media/hdd/',imagePath = '/media/hdd/images',flashPath = '/media/hdd/images/flash'):
		Screen.__init__(self, session)
		self.session = session

		Screen.setTitle(self, _("Flash On the fly (select a image)"))
		self["key_green"] = Button(_("Flash"))
		self["key_red"] = Button(_("Exit"))
		self["key_blue"] = Button("")
		self["key_yellow"] = Button("")

		self.filename = None
		self.imagelist = []
		self.urllist = {}
		self.simulate = False
		self.Online = online
		self.List = list
		self.multi=multi
		self.sel = None
		self.devrootfs=devrootfs
		self.MTDKERNEL = mtdkernel
		self.MTDROOTFS = mtdrootfs
		self.feedurl = urlimage
		self.mediapath = mediapath
		self.imagePath = imagePath
		self.flashPath = flashPath
		self.flashTmp = self.imagePath + '/tmp'

		self["imageList"] = MenuList(self.imagelist)
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions","EPGSelectActions","DirectionActions"], 
		{
			"ok": self.green,
			"green": self.green,
			"yellow": self.yellow,
			"red": self.quit,
			"blue": self.blue,
			"cancel": self.quit,
		}, -2)

		self.onLayoutFinish.append(self.layoutFinished)

	def dummy(self):
		pass

	def getstamp(self):
		ts=time()
		return "&stamp="+str(ts)

	def quit(self):
		if self.simulate or self.List not in ("STARTUP","cmdline.txt"):
			fbClass.getInstance().unlock()
		self.close()

	def blue(self):
		if self.Online:
			self.layoutFinished()
			return
		sel = self["imageList"].l.getCurrentSelection()
		if sel == None:
			print"Nothing to select !!"
			return
		self.filename = sel
		self.session.openWithCallback(self.RemoveCB, MessageBox, _("Do you really want to delete\n%s ?") % (sel), MessageBox.TYPE_YESNO)

	def RemoveCB(self, ret):
		if ret:
			if os.path.exists(self.imagePath + "/" + self.filename):
				os.remove(self.imagePath + "/" + self.filename)
			self.imagelist.remove(self.filename)
			self["imageList"].l.setList(self.imagelist)

	def box(self):
		box = getBoxType()
		machinename = getMachineName()
		if box in ('uniboxhd1', 'uniboxhd2', 'uniboxhd3'):
			box = "ventonhdx"
		elif box == 'odinm6':
			box = getMachineName().lower()
		elif box == "inihde" and machinename.lower() == "xpeedlx":
			box = "xpeedlx"
		elif box in ('xpeedlx1', 'xpeedlx2'):
			box = "xpeedlx"
		elif box == "inihde" and machinename.lower() == "hd-1000":
			box = "sezam-1000hd"
		elif box == "ventonhdx" and machinename.lower() == "hd-5000":
			box = "sezam-5000hd"
		elif box == "ventonhdx" and machinename.lower() == "premium twin":
			box = "miraclebox-twin"
		elif box == "xp1000" and machinename.lower() == "sf8 hd":
			box = "sf8"
		elif box.startswith('et') and not box in ('et8000', 'et8500', 'et8500s', 'et10000'):
			box = box[0:3] + 'x00'
		elif box == 'odinm9' and self.feed == "atv":
			box = 'maram9'
		return box

	def green(self, ret = None):
		sel = self["imageList"].l.getCurrentSelection()
		self.sel = sel
		if sel == None:
			print"Nothing to select !!"
			return

		if self.Online:
			if not " ->" in sel:
				return
			asel=sel
			sel="openspa-"+sel.split(" ->")[0]+".zip"

			self.filename = self.imagePath + "/" + sel

			self.sel = sel
			box = self.box()
			url = self.feedurl + "/" + "/" + sel
			url = self.urllist[asel] + "/" + sel
			url=url.replace("Descarga de Im&aacute;genes","Descarga de Imágenes").replace(" ","%20")
			print "[Flash Online] Download image: >%s<" % url

			if os.path.exists("/etc/OpenSPAfo.xml") and ("beta" in sel.lower()):
				try:
					temphid=open("/etc/OpenSPAfo.xml").read().replace("\n","").replace("-","").split("*")
					lahid=temphid[1]
					lahid2=temphid[2]
					authinfo = urllib2.HTTPPasswordMgrWithDefaultRealm()
					authinfo.add_password(None, url, lahid, lahid2)
					handler = urllib2.HTTPBasicAuthHandler(authinfo)
					myopener = urllib2.build_opener(handler)
					opened = urllib2.install_opener(myopener)
					u = urllib2.urlopen(url)
					total_size = int(u.info().getheaders("Content-Length")[0])
					downloaded = 0
					CHUNK = 256 * 1024
					self["key_green"].setText(_("Downloading..."))
					print "Downloading: %s" % (total_size)
					with open(self.filename, 'wb') as fp:
						while True:
							chunk = u.read(CHUNK)
							downloaded += len(chunk)
							if not chunk: break
							fp.write(chunk)
					print "Downloaded: %s Bytes of %s" % (downloaded, total_size)
					self["key_green"].setText(_("Flash"))
					self.hide()
					self.ImageDownloadCB(False)
					return
				except urllib2.URLError as e:
					self.session.openWithCallback(self.dummyCb,MessageBox, _("Download beta Failed !!, bad xml " + "\n%s\n%s" % (e,url)), type = MessageBox.TYPE_ERROR)
					return
			
			self.hide()
			try:
				u = urllib2.urlopen(url)
				f = open(self.filename, 'wb')
				f.close()
				job = ImageDownloadJob(url, self.filename, sel)
				job.afterEvent = "close"
				job_manager.AddJob(job)
				job_manager.failed_jobs = []
				self.session.openWithCallback(self.ImageDownloadCB, miJobView, job, backgroundable = False, afterEventChangeable = False)
			except urllib2.URLError as e:
				print "[Flash Online] Download failed !!\n%s" % e
				debugtxt("ERROR DOWNLOAD: "+str(url))
				self.session.openWithCallback(self.dummyCb, MessageBox, _("Download Failed !!" + "\n%s\n%s" % (e,url)), type = MessageBox.TYPE_ERROR)
				self.close()
		else:
			self.hide()
			self.filename = self.imagePath + "/" + sel
			self.session.openWithCallback(self.startInstallLocal, MessageBox, _("Do you want to backup your settings now?"), default=False)

	def dummyCb(self,ret=None):
		pass
		
	def ImageDownloadCB(self, ret):
		if ret:
			return
		if job_manager.active_job:
			job_manager.active_job = None
			self.close()
			return
		if len(job_manager.failed_jobs) == 0:

			self.flashWithPostFlashActionMode = 'online'
			self.flashWithPostFlashAction()
		else:
			self.session.open(MessageBox, _("Download Failed !!"), type = MessageBox.TYPE_ERROR)

	def flashWithPostFlashAction(self, ret = True):
		if ret:
			print "flashWithPostFlashAction"
			title =_("Please select what to do after flashing the image:\n(In addition, if it exists, a local script will be executed as well at /media/hdd/images/config/myrestore.sh)")
			list = ((_("Flash and start installation wizard"), "wizard"),
			(_("Flash and restore settings and no plugins"), "restoresettingsnoplugin"),
			(_("Flash and restore settings and selected plugins (ask user)"), "restoresettings"),
			(_("Flash and restore settings and all saved plugins"), "restoresettingsandallplugins"),
			(_("Do not flash image"), "abort"))
			self.session.openWithCallback(self.postFlashActionCallback, ChoiceBox,title=title,list=list,selection=self.SelectPrevPostFashAction())
		else:
			self.show()

	def SelectPrevPostFashAction(self):
		index = 0
		Settings = False
		AllPlugins = False
		noPlugins = False

		if os.path.exists(self.imagePath + '/config/settings'):
			Settings = True
		if os.path.exists(self.imagePath + '/config/plugins'):
			AllPlugins = True
		if os.path.exists(self.imagePath + '/config/noplugins'):
			noPlugins = True

		if 	Settings and noPlugins:
			index = 1
		elif Settings and not AllPlugins and not noPlugins:
			index = 2
		elif Settings and AllPlugins:
			index = 3

		return index

	def postFlashActionCallback(self, answer):
		print "postFlashActionCallback"
		restoreSettings   = False
		restoreAllPlugins = False
		restoreSettingsnoPlugin = False
		if answer is not None:
			if answer[1] == "restoresettings":
				restoreSettings   = True
			if answer[1] == "restoresettingsnoplugin":
				restoreSettings = True
				restoreSettingsnoPlugin = True
			if answer[1] == "restoresettingsandallplugins":
				restoreSettings   = True
				restoreAllPlugins = True
			if restoreSettings:
				self.SaveEPG()
			if answer[1] != "abort":
				if restoreSettings:
					try:
						if not os.path.exists(self.imagePath + '/config'):
							os.makedirs(self.imagePath + '/config')
						open(self.imagePath + '/config/settings','w').close()
					except:
						print "postFlashActionCallback: failed to create /media/hdd/images/config/settings"
				else:
					if os.path.exists(self.imagePath + '/config/settings'):
						os.unlink(self.imagePath + '/config/settings')
				if restoreAllPlugins:
					try:
						if not os.path.exists(self.imagePath + '/config'):
							os.makedirs(self.imagePath + '/config')
						open(self.imagePath + '/config/plugins','w').close()
					except:
						print "postFlashActionCallback: failed to create /media/hdd/images/config/plugins"
				else:
					if os.path.exists(self.imagePath + '/config/plugins'):
						os.unlink(self.imagePath + '/config/plugins')
				if restoreSettingsnoPlugin:
					try:
						if not os.path.exists(self.imagePath + '/config'):
							os.makedirs(self.imagePath + '/config')
						open(self.imagePath + '/config/noplugins','w').close()
					except:
						print "postFlashActionCallback: failed to create /media/hdd/images/config/noplugins"
				else:
					if os.path.exists(self.imagePath + '/config/noplugins'):
						os.unlink(self.imagePath + '/config/noplugins')

				if restoreSettings or restoreAllPlugins or restoreSettingsnoPlugin:
					if config.plugins.softwaremanager.restoremode.value is not None:
						try:
							if not os.path.exists(self.imagePath + '/config'):
								os.makedirs(self.imagePath + 'config')
							if config.plugins.softwaremanager.restoremode.value == "slow":
								if not os.path.exists(self.imagePath + '/config/slow'):
									open(self.imagePath + '/config/slow','w').close()
								if os.path.exists(self.imagePath + '/config/fast'):
									os.unlink(self.imagePath + '/config/fast')
								if os.path.exists(self.imagePath + '/config/turbo'):
									os.unlink(self.imagePath + '/config/turbo')
							elif config.plugins.softwaremanager.restoremode.value == "fast":
								if not os.path.exists(self.imagePath + '/config/fast'):
									open(self.imagePath + '/config/fast','w').close()
								if os.path.exists(self.imagePath + '/config/slow'):
									os.unlink(self.imagePath + '/config/slow')
								if os.path.exists(self.imagePath + '/config/turbo'):
									os.unlink(self.imagePath + '/config/turbo')
							elif config.plugins.softwaremanager.restoremode.value == "turbo":
								if not os.path.exists(self.imagePath + '/config/turbo'):
									open(self.imagePath + '/config/turbo','w').close()
								if os.path.exists(self.imagePath + '/config/slow'):
									os.unlink(self.imagePath + '/config/slow')
								if os.path.exists(self.imagePath + '/config/fast'):
									os.unlink(self.imagePath + '/config/fast')
						except:
							print "postFlashActionCallback: failed to create restore mode flagfile"

				if self.flashWithPostFlashActionMode == 'online':
					self.unzip_image(self.filename, self.flashPath)
				else:
					print self.filename 
					print self.flashPath
					self.startInstallLocalCB()
			else:
				self.show()
		else:
			self.show()

	def unzip_image(self, filename, path):
		print "Unzip %s to %s" %(filename,path)
		self.session.openWithCallback(self.cmdFinished, Console, title = _("Unzipping files, Please wait ..."), cmdlist = ['unzip ' + filename + ' -o -d ' + path, "sleep 3"], closeOnSuccess = True)

	def cmdFinished(self):
		self.prepair_flashtmp(self.flashPath)
		self.Start_Flashing()

	def Start_Flashing(self):
		print "Start Flashing"
		cmdlist = []
		if os.path.exists(ofgwritePath):
			text = _("Flashing: ")
			if self.simulate:
				text += _("Simulate (no write)")
				if SystemInfo["HaveMultiBoot"]:
					if getMachineBuild() in ("cc1","sf8008","ustym4kpro"):
						cmdlist.append("%s -r%s -k%s %s > /dev/null 2>&1" % (ofgwritePath, self.MTDROOTFS, self.MTDKERNEL, self.flashTmp))
					else:
						cmdlist.append("%s -n -r -k -m%s %s > /dev/null 2>&1" % (ofgwritePath, self.multi, self.flashTmp))
				elif getMachineBuild() in ("u51", "u52", "u53", "u5", "u5pvr", "cc1", "sf8008", "ustym4kpro"):
					cmdlist.append("%s -n -r%s -k%s %s > /dev/null 2>&1" % (ofgwritePath, MTDROOTFS, MTDKERNEL, self.flashTmp))
				elif getMachineBuild() in ("h9", "i55plus"):
					cmdlist.append("%s -n -f -r -k %s > /dev/null 2>&1" % (ofgwritePath, self.flashTmp))
				else:
					cmdlist.append("%s -n -r -k %s > /dev/null 2>&1" % (ofgwritePath, self.flashTmp))
				self.close()
				message = "echo -e '\n"
				message += _('Show only found image and mtd partitions.\n')
				message += "'"
			else:
				text += _("root and kernel")
				if SystemInfo["HaveMultiBoot"]:
					if self.List not in ("STARTUP","cmdline.txt"):
						os.system('mkfs.ext4 -F ' + self.devrootfs)
					if getMachineBuild() in ("cc1","sf8008","ustym4kpro"):
						cmdlist.append("%s -r%s -k%s %s > /dev/null 2>&1" % (ofgwritePath, self.MTDROOTFS, self.MTDKERNEL, self.flashTmp))
					else:
						cmdlist.append("%s -r -k -m%s %s > /dev/null 2>&1" % (ofgwritePath, self.multi, self.flashTmp))
				elif getMachineBuild() in ("u51", "u52", "u53", "u5", "u5pvr", "cc1", "sf8008", "ustym4kpro"):
					cmdlist.append("%s -r%s -k%s %s > /dev/null 2>&1" % (ofgwritePath, MTDROOTFS, MTDKERNEL, self.flashTmp))
				elif getMachineBuild() in ("h9", "i55plus"):
					cmdlist.append("%s -f -r -k %s > /dev/null 2>&1" % (ofgwritePath, self.flashTmp))
				else:
					cmdlist.append("%s -r -k %s > /dev/null 2>&1" % (ofgwritePath, self.flashTmp))
				message = "echo -e '\n"
				if self.List not in ("STARTUP","cmdline.txt") and SystemInfo["HaveMultiBoot"]:
					message += _('ofgwrite flashing ready.\n')
					message += _('please press exit to go back to the menu.\n')
				else:
					message += _('ofgwrite will stop enigma2 now to run the flash.\n')
					message += _('Your STB will freeze during the flashing process.\n')
					message += _('Please: DO NOT reboot your STB and turn off the power.\n')
					message += _('The image or kernel will be flashing and auto booted in few minutes.\n')
					if self.box() == 'gb800solo':
						message += _('GB800SOLO takes about 20 mins !!\n')
				message += "'"
			cmdlist.append(message)
			self.session.open(Console, title = text, cmdlist = cmdlist, finishedCallback = self.quit, closeOnSuccess = False)
			if not self.simulate:
				fbClass.getInstance().lock()
			if self.List not in ("STARTUP","cmdline.txt"):
				self.close()

	def prepair_flashtmp(self, tmpPath):
		if os.path.exists(self.flashTmp):
			flashTmpold = self.flashTmp + 'old'
			os.system('mv %s %s' %(self.flashTmp, flashTmpold))
			print 'mv %s %s' %(self.flashTmp, flashTmpold)
			os.system('rm -rf %s' %flashTmpold)
		if not os.path.exists(self.flashTmp):
			os.mkdir(self.flashTmp)
		kernel = True
		rootfs = True

		for path, subdirs, files in os.walk(tmpPath):
			for name in files:
				if name.find('kernel') > -1 and name.endswith('.bin') and kernel:
					binfile = os.path.join(path, name)
					dest = self.flashTmp + '/%s' %KERNELBIN
					shutil.copyfile(binfile, dest)
					kernel = False
				elif name.find('root') > -1 and (name.endswith('.bin') or name.endswith('.ubi') or name.endswith('.jffs2') or name.endswith('.bz2')) and rootfs:
					binfile = os.path.join(path, name)
					dest = self.flashTmp + '/%s' %ROOTFSBIN
					shutil.copyfile(binfile, dest)
					rootfs = False
				elif name.find('uImage') > -1 and kernel:
					binfile = os.path.join(path, name)
					dest = self.flashTmp + '/uImage'
					shutil.copyfile(binfile, dest)
					kernel = False
				elif name.find('e2jffs2') > -1 and name.endswith('.img') and rootfs:
					binfile = os.path.join(path, name)
					dest = self.flashTmp + '/e2jffs2.img'
					shutil.copyfile(binfile, dest)
					rootfs = False

	def yellow(self):
		if not self.Online:
			self.session.openWithCallback(self.DeviceBrowserClosed, DeviceBrowser, None, matchingPattern="^.*\.(zip|bin|jffs2|img)", showDirectories=True, showMountpoints=True, inhibitMounts=["/autofs/sr0/"])
		else:
			from Plugins.SystemPlugins.SoftwareManager.BackupRestore import BackupScreen
			self.session.openWithCallback(self.green,BackupScreen, runBackup = True)

	def startInstallLocal(self, ret = None):
		if ret:
			from Plugins.SystemPlugins.SoftwareManager.BackupRestore import BackupScreen
			self.flashWithPostFlashActionMode = 'local'
			self.session.openWithCallback(self.flashWithPostFlashAction,BackupScreen, runBackup = True)
		else:
			self.flashWithPostFlashActionMode = 'local'
			self.flashWithPostFlashAction()

	def startInstallLocalCB(self, ret = None):
		if self.sel == str(self.flashTmp):
			self.Start_Flashing()
		else:
			self.unzip_image(self.filename, self.flashPath)

	def DeviceBrowserClosed(self, path, filename, binorzip):
		if path:
			print path, filename, binorzip
			strPath = str(path)
			if strPath[-1] == '/':
				strPath = strPath[:-1]
			self.imagePath = strPath
			if os.path.exists(self.flashTmp):
				os.system('rm -rf ' + self.flashTmp)
			os.mkdir(self.flashTmp)
			if binorzip == 0:
				for files in os.listdir(self.imagePath):
					if files.endswith(".ubi") or files.endswith(".bin") or files.endswith('.jffs2') or files.endswith('.img'):
						self.prepair_flashtmp(strPath)
						break
				self.Start_Flashing()
			elif binorzip == 1:
				self.unzip_image(strPath + '/' + filename, self.flashPath)
			else:
				self.layoutFinished()
		else:
			self.imagePath = self.imagePath

	def layoutFinished(self):
		box = self.box()
		self.setTitle(_("Flash online from ") + self.mediapath)
		self.imagelist = []
		self.urllist = {}

		if self.Online:
			self["key_yellow"].setText("Backup&Flash")
			self.feedurl = urlimage
			self["key_blue"].setText("")

			url = '%s/betas/getfirm.php?box=%s' % (self.feedurl,box)
			url=url +self.getstamp()
			print "URL ONLINE:[%s]" % (url)
			try:
				req = urllib2.Request(url)
				response = urllib2.urlopen(req)
			except urllib2.URLError as e:
				print "URL ERROR: %s\n%s" % (e,url)
				
				self["imageList"].l.setList(self.imagelist)
				return

			try:
				the_page = response.read()

			except urllib2.HTTPError as e:
				
				print "HTTP download ERROR: %s" % e.code
				return

			lines = the_page.split('\n')

			try:
				
				l=lines[0]
				self.feedurl = l.split("<a href='")[1].split("openspa-")[0]
			except:
				self.imagelist.append("("+_("No images found for")+" "+box+")")

			for line in lines:
				if line.find(".zip") > -1:
					name=line.split(">")[1].split("<")[0]
					name=name.replace(" ("," ").replace(" - "," - ").replace(")","").replace("openspa-","").replace(".zip"," ->")
					self.urllist[name]=line.split("<a href='")[1].split("openspa-")[0]
					self.imagelist.append(name)

		else:
			self["key_blue"].setText(_("Delete"))
			self["key_yellow"].setText(_("Devices"))
			for name in os.listdir(self.imagePath):
				if name.endswith(".zip"):
					self.imagelist.append(name)
			self.imagelist.sort()
			if os.path.exists(self.flashTmp):
				for file in os.listdir(self.flashTmp):
					if file.find(".bin")> -1 or file.find(".ubi")> -1:
						self.imagelist.insert( 0, str(self.flashTmp))
						break

		self["imageList"].l.setList(self.imagelist)

	def SaveEPG(self):
		from enigma import eEPGCache
		epgcache = eEPGCache.getInstance()
		epgcache.save()


class ImageDownloadJob(Job):
	def __init__(self, url, filename, file):
		Job.__init__(self, _("Downloading %s") %file)
		ImageDownloadTask(self, url, filename)

class DownloaderPostcondition(Condition):
	def check(self, task):
		return task.returncode == 0

	def getErrorMessage(self, task):
		return self.error_message

class ImageDownloadTask(Task):
	def __init__(self, job, url, path):
		Task.__init__(self, job, _("Downloading"))
		self.postconditions.append(DownloaderPostcondition())
		self.job = job
		self.url = url
		self.path = path
		self.error_message = ""
		self.last_recvbytes = 0
		self.error_message = None
		self.download = None
		self.aborted = False

	def run(self, callback):
		self.callback = callback
		self.download = downloadWithProgress(self.url,self.path)
		self.download.addProgress(self.download_progress)
		self.download.start().addCallback(self.download_finished).addErrback(self.download_failed)
		print "[ImageDownloadTask] downloading", self.url, "to", self.path

	def abort(self):
		print "[ImageDownloadTask] aborting", self.url
		if self.download:
			self.download.stop()
		self.aborted = True

	def download_progress(self, recvbytes, totalbytes):
		if ( recvbytes - self.last_recvbytes  ) > 100000: # anti-flicker
			self.progress = int(100*(float(recvbytes)/float(totalbytes)))
			self.name = _("Downloading") + ' ' + _("%d of %d kBytes") % (recvbytes/1024, totalbytes/1024)
			self.last_recvbytes = recvbytes

	def download_failed(self, failure_instance=None, error_message=""):
		self.error_message = error_message
		if error_message == "" and failure_instance is not None:
			self.error_message = failure_instance.getErrorMessage()
		Task.processFinished(self, 1)

	def download_finished(self, string=""):
		if self.aborted:
			self.finish(aborted = True)
		else:
			Task.processFinished(self, 0)

class DeviceBrowser(Screen, HelpableScreen):
	skin = """
		<screen name="DeviceBrowser" position="center,center" size="520,430" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
			<widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<widget source="message" render="Label" position="5,50" size="510,150" font="Regular;16" />
			<widget name="filelist" position="5,210" size="510,220" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session, startdir, message="", showDirectories = True, showFiles = True, showMountpoints = True, matchingPattern = "", useServiceRef = False, inhibitDirs = False, inhibitMounts = False, isTop = False, enableWrapAround = False, additionalExtensions = None):
		Screen.__init__(self, session)

		HelpableScreen.__init__(self)
		Screen.setTitle(self, _("Please select medium"))

		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button("")
		self["message"] = Label(message)

		self.filelist = FileList(startdir, showDirectories = showDirectories, showFiles = showFiles, showMountpoints = showMountpoints, matchingPattern = matchingPattern, useServiceRef = useServiceRef, inhibitDirs = inhibitDirs, inhibitMounts = inhibitMounts, isTop = isTop, enableWrapAround = enableWrapAround, additionalExtensions = additionalExtensions)
		self["filelist"] = self.filelist

		self["FilelistActions"] = ActionMap(["SetupActions", "ColorActions"],
			{
				"green": self.use,
				"red": self.exit,
				"ok": self.ok,
				"cancel": self.exit
			})

		hotplugNotifier.append(self.hotplugCB)
		self.onShown.append(self.updateButton)
		self.onClose.append(self.removeHotplug)

	def hotplugCB(self, dev, action):
		print "[hotplugCB]", dev, action
		self.updateButton()

	def updateButton(self):
		if self["filelist"].getFilename() or self["filelist"].getCurrentDirectory():
			self["key_green"].setText(_("Flash"))
		else:
			self["key_green"].setText("")

	def removeHotplug(self):
		print "[removeHotplug]"
		hotplugNotifier.remove(self.hotplugCB)

	def ok(self):
		if self.filelist.canDescent():
			if self["filelist"].showMountpoints == True and self["filelist"].showDirectories == False:
				self.use()
			else:
				self.filelist.descent()

	def use(self):
		print "[use]", self["filelist"].getCurrentDirectory(), self["filelist"].getFilename()
		if self["filelist"].getFilename() is not None and self["filelist"].getCurrentDirectory() is not None:
			if self["filelist"].getFilename().endswith(".bin") or self["filelist"].getFilename().endswith(".ubi") or self["filelist"].getFilename().endswith(".jffs2"):
				self.close(self["filelist"].getCurrentDirectory(), self["filelist"].getFilename(), 0)
			elif self["filelist"].getFilename().endswith(".zip"):
				self.close(self["filelist"].getCurrentDirectory(), self["filelist"].getFilename(), 1)
			else:
				return

	def exit(self):
		self.close(False, False, -1)
