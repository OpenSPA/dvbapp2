# -*- coding: utf-8 -*-

from . import _
from enigma import eListboxPythonMultiContent, gFont, eEnv, getDesktop, eTimer
from boxbranding import getMachineBrand, getMachineName, getBoxType, getBrandOEM
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Sources.StaticText import StaticText
from Components.Pixmap import Pixmap
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaBlend
from Components.Network import iNetwork
from Components.NimManager import nimmanager
from Components.SystemInfo import SystemInfo
from Components.config import config, ConfigSubsection, ConfigText, ConfigSelection, ConfigYesNo

from Screens.Screen import Screen
from Screens.ParentalControlSetup import ProtectedScreen
from Screens.NetworkSetup import *
from Screens.About import About
from Screens.PluginBrowser import PluginDownloadBrowser, PluginFilter, PluginBrowser
from Screens.LanguageSelection import LanguageSelection
from Screens.Satconfig import NimSelection
from Screens.ScanSetup import ScanSimple, ScanSetup
from Screens.Setup import Setup, getSetupTitle
from Screens.SoftcamSetup import *
from Screens.HarddiskSetup import HarddiskSelection, HarddiskFsckSelection, HarddiskConvertExt4Selection
from Screens.SkinSelector import LcdSkinSelector, SkinSelector
from Screens.VideoMode import VideoSetup, AudioSetup

from Plugins.Plugin import PluginDescriptor
from Plugins.SystemPlugins.NetworkBrowser.MountManager import AutoMountManager
from Plugins.SystemPlugins.NetworkBrowser.NetworkBrowser import NetworkBrowser
from Plugins.SystemPlugins.NetworkWizard.NetworkWizard import NetworkWizard
from Plugins.Extensions.spaTeam.Epg import EPGScreen
from Plugins.Extensions.spaTeam.RestartNetwork import RestartNetwork
from Plugins.Extensions.spaTeam.MountManager import HddMount
from Plugins.Extensions.spaTeam.CronManager import *
from Plugins.Extensions.spaTeam.ScriptRunner import *
from Plugins.Extensions.spaTeam.SwapManager import Swap, SwapAutostart
from Plugins.Extensions.spaTeam.TimeJump import TimeJumpAutostart, TimeJumpMain
from Plugins.SystemPlugins.SoftwareManager.Flash_online import FlashOnline
from Plugins.SystemPlugins.SoftwareManager.ImageBackup import ImageBackup
from Plugins.SystemPlugins.SoftwareManager.plugin import SoftwareManagerSetup
from Plugins.SystemPlugins.SoftwareManager.BackupRestore import BackupScreen, RestoreScreen, BackupSelection, getBackupPath, getOldBackupPath, getBackupFilename

from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_SKIN_IMAGE, SCOPE_SKIN, fileExists
from Tools.LoadPixmap import LoadPixmap

from os import path, listdir
from time import sleep
from re import search

import NavigationInstance

plugin_path_networkbrowser = eEnv.resolve("${libdir}/enigma2/python/Plugins/SystemPlugins/NetworkBrowser")

if path.exists("/usr/lib/enigma2/python/Plugins/Extensions/AudioSync"):
	from Plugins.Extensions.AudioSync.AC3setup import AC3LipSyncSetup
	plugin_path_audiosync = eEnv.resolve("${libdir}/enigma2/python/Plugins/Extensions/AudioSync")
	AUDIOSYNC = True
else:
	AUDIOSYNC = False

if path.exists("/usr/lib/enigma2/python/Plugins/SystemPlugins/VideoEnhancement/plugin.pyo"):
	from Plugins.SystemPlugins.VideoEnhancement.plugin import VideoEnhancementSetup
	VIDEOENH = True
else:
	VIDEOENH = False

if path.exists("/usr/lib/enigma2/python/Plugins/Extensions/dFlash"):
	from Plugins.Extensions.dFlash.plugin import dFlash
	DFLASH = True
else:
	DFLASH = False

if path.exists("/usr/lib/enigma2/python/Plugins/Extensions/dBackup"):
	from Plugins.Extensions.dBackup.plugin import dBackup
	DBACKUP = True
else:
	DBACKUP = False

if path.exists("/usr/lib/enigma2/python/Plugins/SystemPlugins/PositionerSetup/plugin.pyo"):
	from Plugins.SystemPlugins.PositionerSetup.plugin import PositionerSetup, RotorNimSelection
	POSSETUP = True
else:
	POSSETUP = False

if path.exists("/usr/lib/enigma2/python/Plugins/SystemPlugins/Satfinder/plugin.pyo"):
	from Plugins.SystemPlugins.Satfinder.plugin import Satfinder
	SATFINDER = True
else:
	SATFINDER = False


def isFileSystemSupported(filesystem):
	try:
		for fs in open('/proc/filesystems', 'r'):
			if fs.strip().endswith(filesystem):
				return True
		return False
	except Exception, ex:
		print "[Harddisk] Failed to read /proc/filesystems:", ex


def Check_Softcam():
	found = False
	if fileExists("/etc/enigma2/noemu"):
		found = False
	else:
		for cam in os.listdir("/etc/init.d"):
			if cam.startswith('softcam.') and not cam.endswith('None'):
				found = True
				break
			elif cam.startswith('cardserver.') and not cam.endswith('None'):
				found = True
				break
	return found


def Check_SysSoftcam():
	syscam = "none"
	if os.path.isfile('/etc/init.d/softcam'):
		if (os.path.islink('/etc/init.d/softcam') and not os.readlink('/etc/init.d/softcam').lower().endswith('none')):
			try:
				syscam = os.readlink('/etc/init.d/softcam').rsplit('.', 1)[1]
				if syscam.lower().startswith('oscam'):
					syscam = "oscam"
				if syscam.lower().startswith('ncam'):
					syscam = "ncam"
				if syscam.lower().startswith('cccam'):
					syscam = "cccam"
			except:
				pass
	return syscam


# Hide Keymap selection when no other keymaps installed.
if config.usage.keymap.value != eEnv.resolve("${datadir}/enigma2/keymap.xml"):
	if not path.isfile(eEnv.resolve("${datadir}/enigma2/keymap.usr")) and config.usage.keymap.value == eEnv.resolve("${datadir}/enigma2/keymap.usr"):
		setDefaultKeymap()
	if not path.isfile(eEnv.resolve("${datadir}/enigma2/keymap.ntr")) and config.usage.keymap.value == eEnv.resolve("${datadir}/enigma2/keymap.ntr"):
		setDefaultKeymap()
	if not path.isfile(eEnv.resolve("${datadir}/enigma2/keymap.u80")) and config.usage.keymap.value == eEnv.resolve("${datadir}/enigma2/keymap.u80"):
		setDefaultKeymap()


def setDefaultKeymap():
	print "[spaTeam] Set Keymap to Default"
	config.usage.keymap.value = eEnv.resolve("${datadir}/enigma2/keymap.xml")
	config.save()


class spaMenu(Screen, ProtectedScreen):
	skin = """
		<screen name="spaMenu" position="center,center" size="1280,720" backgroundColor="black" flags="wfNoBorder">
		<widget name="list" position="21,32" size="370,500" backgroundColor="black" itemHeight="50" transparent="1" />
		<widget name="sublist" position="410,32" size="320,500" backgroundColor="black" itemHeight="50" />
		<eLabel name="bar_grey" position="400,30" size="2,500" backgroundColor="grey" zPosition="3" />
		<widget source="session.VideoPicture" render="Pig" position="770,40" size="430,280" backgroundColor="transparent" zPosition="2" />
		<eLabel name="bar_grey2" position="760,30" size="450,300" backgroundColor="grey" zPosition="1" />
		<widget name="lblservices" font="Regular;24" position="760,340" zPosition="1" size="450,30" valign="center" halign="center" backgroundColor="black" foregroundColor="white" transparent="1" />
		<!-- FTP -->
		<eLabel text="FTP:" font="Regular;20" position="780,380" size="150,25" valign="center" halign="left" zPosition="1" backgroundColor="black" foregroundColor="white" transparent="1" />
		<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/spaTeam/icons/off.png" position="900,384" size="20,20" zPosition="1" alphatest="blend" />
		<widget name="ftp_on" position="900,384" size="20,20" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/spaTeam/icons/on.png" zPosition="2" alphatest="blend" />
		<!-- TELNET -->
		<eLabel text="Telnet:" font="Regular;20" position="780,410" size="150,25" valign="center" halign="left" zPosition="1" backgroundColor="black" foregroundColor="white" transparent="1" />
		<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/spaTeam/icons/off.png" position="900,414" size="20,20" zPosition="1" alphatest="blend" />
		<widget name="telnet_on" position="900,414" size="20,20" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/spaTeam/icons/on.png" zPosition="2" alphatest="blend" />
		<!-- SSH -->
		<eLabel text="SSH:" font="Regular;20" position="780,440" size="150,25" valign="center" halign="left" zPosition="1" backgroundColor="black" foregroundColor="white" transparent="1" />
		<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/spaTeam/icons/off.png" position="900,444" size="20,20" zPosition="1" alphatest="blend" />
		<widget name="ssh_on" position="900,444" size="20,20" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/spaTeam/icons/on.png" zPosition="2" alphatest="blend" />
		<!-- SAMBA -->
		<eLabel text="Samba:" font="Regular;20" position="780,470" size="150,25" valign="center" halign="left" zPosition="1" backgroundColor="black" foregroundColor="white" transparent="1" />
		<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/spaTeam/icons/off.png" position="900,474" size="20,20" zPosition="1" alphatest="blend" />
		<widget name="smb_on" position="900,474" size="20,20" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/spaTeam/icons/on.png" zPosition="2" alphatest="blend" />
		<!-- NFS -->
		<eLabel text="NFS:" font="Regular;20" position="780,500" size="150,25" valign="center" halign="left" zPosition="1" backgroundColor="black" foregroundColor="white" transparent="1" />
		<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/spaTeam/icons/off.png" position="900,504" size="20,20" zPosition="1" alphatest="blend" />
		<widget name="nfs_on" position="900,504" size="20,20" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/spaTeam/icons/on.png" zPosition="2" alphatest="blend" />
		<!-- OpenVPN -->
		<eLabel text="OpenVPN:" font="Regular;20" position="780,530" size="150,25" valign="center" halign="left" zPosition="1" backgroundColor="black" foregroundColor="white" transparent="1" />
		<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/spaTeam/icons/off.png" position="900,534" size="20,20" zPosition="1" alphatest="blend" />
		<widget name="vpn_on" position="900,534" size="20,20" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/spaTeam/icons/on.png" zPosition="2" alphatest="blend" />
		<!-- AFP -->
		<eLabel text="AFP:" font="Regular;20" position="1050,380" size="150,25" valign="center" halign="left" zPosition="1" backgroundColor="black" foregroundColor="white" transparent="1" />
		<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/spaTeam/icons/off.png" position="1170,384" size="20,20" zPosition="1" alphatest="blend" />
		<widget name="afp_on" position="1170,384" size="20,20" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/spaTeam/icons/on.png" zPosition="2" alphatest="blend" />
		<!-- SABnzbd -->
		<eLabel text="SABnzbd:" font="Regular;20" position="1050,410" size="150,25" valign="center" halign="left" zPosition="1" backgroundColor="black" foregroundColor="white" transparent="1" />
		<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/spaTeam/icons/off.png" position="1170,414" size="20,20" zPosition="1" alphatest="blend" />
		<widget name="sabnzbd_on" position="1170,414" size="20,20" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/spaTeam/icons/on.png" zPosition="2" alphatest="blend" />
		<!-- MiniDLNA -->
		<eLabel text="MiniDLNA:" font="Regular;20" position="1050,440" size="150,25" valign="center" halign="left" zPosition="1" backgroundColor="black" foregroundColor="white" transparent="1" />
		<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/spaTeam/icons/off.png" position="1170,444" size="20,20" zPosition="1" alphatest="blend" />
		<widget name="minidlna_on" position="1170,444" size="20,20" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/spaTeam/icons/on.png" zPosition="2" alphatest="blend" />
		<!-- Inadyn -->
		<eLabel text="Inadyn:" font="Regular;20" position="1050,470" size="150,25" valign="center" halign="left" zPosition="1" backgroundColor="black" foregroundColor="white" transparent="1" />
		<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/spaTeam/icons/off.png" position="1170,474" size="20,20" zPosition="1" alphatest="blend" />
		<widget name="inadyn_on" position="1170,474" size="20,20" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/spaTeam/icons/on.png" zPosition="2" alphatest="blend" />
		<!-- uShare -->
		<eLabel text="uShare:" font="Regular;20" position="1050,500" size="150,25" valign="center" halign="left" zPosition="1" backgroundColor="black" foregroundColor="white" transparent="1" />
		<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/spaTeam/icons/off.png" position="1170,504" size="20,20" zPosition="1" alphatest="blend" />
		<widget name="ushare_on" position="1170,504" size="20,20" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/spaTeam/icons/on.png" zPosition="2" alphatest="blend" />
		<!-- Crond -->
		<eLabel text="Crond:" font="Regular;20" position="1050,530" size="150,25" valign="center" halign="left" zPosition="1" backgroundColor="black" foregroundColor="white" transparent="1" />
		<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/spaTeam/icons/off.png" position="1170,534" size="20,20" zPosition="1" alphatest="blend" />
		<widget name="crond_on" position="1170,534" size="20,20" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/spaTeam/icons/on.png" zPosition="2" alphatest="blend" />
		<!-- END -->
		<!--<eLabel name="new eLabel" position="1000,380" size="2,210" backgroundColor="grey" zPosition="3" />-->
		<widget name="description" position="22,620" size="1150,110" zPosition="1" font="Regular;22" halign="center" backgroundColor="black" transparent="1" />
		<widget name="key_red" position="30,671" size="300,26" zPosition="1" font="Regular;22" halign="center" foregroundColor="white" backgroundColor="black" transparent="1" />
		<widget name="key_green" position="335,671" size="300,26" zPosition="1" font="Regular;22" halign="center" foregroundColor="white" backgroundColor="black" transparent="1" />
		<widget name="key_yellow" position="640,671" size="300,26" zPosition="1" font="Regular;22" halign="center" foregroundColor="white" backgroundColor="black" transparent="1" valign="center" />
		<widget name="key_blue" position="945,671" size="300,26" zPosition="1" font="Regular;22" halign="center" foregroundColor="white" backgroundColor="black" transparent="1" />
		<eLabel name="bar_red" position="30,667" size="300,3" zPosition="3" backgroundColor="red" />
		<eLabel name="bar_green" position="335,667" size="300,3" zPosition="3" backgroundColor="green" />
		<eLabel name="bar_yellow" position="640,667" size="300,3" zPosition="3" backgroundColor="yellow" />
		<eLabel name="bar_blue" position="945,667" size="300,3" zPosition="3" backgroundColor="blue" />
		</screen> """

	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		if config.ParentalControl.configured.value:
			ProtectedScreen.__init__(self)
		Screen.setTitle(self, _("OpenSPA Panel - Menu"))
		ProtectedScreen.__init__(self)

		self["key_red"] = Label(_("Exit"))
		self["key_green"] = Label(_("System Info"))
		self["key_yellow"] = Label(_("Devices"))
		self["key_blue"] = Label(_("Services"))
		self["lblservices"] = Label(_("Services"))
		self["description"] = Label()
		self["summary_description"] = StaticText("")

		self["ftp_on"] = Pixmap()
		self["ftp_on"].hide()
		self["ssh_on"] = Pixmap()
		self["ssh_on"].hide()
		self["telnet_on"] = Pixmap()
		self["telnet_on"].hide()
		self["smb_on"] = Pixmap()
		self["smb_on"].hide()
		self["nfs_on"] = Pixmap()
		self["nfs_on"].hide()
		self["vpn_on"] = Pixmap()
		self["vpn_on"].hide()
		self["afp_on"] = Pixmap()
		self["afp_on"].hide()
		self["crond_on"] = Pixmap()
		self["crond_on"].hide()
		self["sabnzbd_on"] = Pixmap()
		self["sabnzbd_on"].hide()
		self["minidlna_on"] = Pixmap()
		self["minidlna_on"].hide()
		self["inadyn_on"] = Pixmap()
		self["inadyn_on"].hide()
		self["ushare_on"] = Pixmap()
		self["ushare_on"].hide()

		self.menu = 0
		self.list = []
		self["list"] = spaMenuList(self.list)
		self.sublist = []
		self["sublist"] = spaMenuSubList(self.sublist)
		self.selectedList = []
		self.onChangedEntry = []
		self["list"].onSelectionChanged.append(self.selectionChanged)
		self["sublist"].onSelectionChanged.append(self.selectionSubChanged)

		self["actions"] = ActionMap(["OkCancelActions", "WizardActions"],
		{
			"ok": self.ok,
			"cancel": self.keyred,
			"left": self.goLeft,
			"right": self.goRight,
			"up": self.goUp,
			"down": self.goDown,
		}, -1)

		self["ColorActions"] = HelpableActionMap(self, "ColorActions",
			{
			"red": self.keyred,
			"green": self.keygreen,
			"yellow": self.keyyellow,
			"blue": self.keyblue,
			})

		self.MainQmenu()
		self.selectedList = self["list"]
		self.selectionChanged()
		self.onLayoutFinish.append(self.layoutFinished)

	def isProtected(self):
		return config.ParentalControl.setuppinactive.value and not config.ParentalControl.config_sections.main_menu.value and config.ParentalControl.config_sections.spateam.value

	def createSummary(self):
		pass

	def layoutFinished(self):
		self.getServicesInfo()
		self["sublist"].selectionEnabled(0)

	def selectionChanged(self):
		if self.selectedList == self["list"]:
			item = self["list"].getCurrent()
			if item:
				self["description"].text = item[4][7]
				self["summary_description"].text = item[0]
				self.okList()

	def selectionSubChanged(self):
		if self.selectedList == self["sublist"]:
			item = self["sublist"].getCurrent()
			if item:
				self["description"].text = item[4][7]
				self["summary_description"].text = item[0]

	def goLeft(self):
		if self.menu <> 0:
			self.menu = 0
			self.selectedList = self["list"]
			self["list"].selectionEnabled(1)
			self["sublist"].selectionEnabled(0)
			self.selectionChanged()

	def goRight(self):
		if self.menu == 0:
			self.menu = 1
			self.selectedList = self["sublist"]
			self["sublist"].moveToIndex(0)
			self["list"].selectionEnabled(0)
			self["sublist"].selectionEnabled(1)
			self.selectionSubChanged()

	def goUp(self):
		self.selectedList.up()

	def goDown(self):
		self.selectedList.down()

	def keyred(self):
		self.close()

	def keygreen(self):
		from Plugins.Extensions.spaTeam.SysInfo import SysInfo
		self.session.open(SysInfo)

	def keyyellow(self):
		self.session.open(spaMenuDevices)

	def keyblue(self):
		from Plugins.Extensions.spaTeam.DaemonsList import DaemonsList
		self.session.open(DaemonsList)

	def autorefresh(self):
		self.getServicesInfo()

	def getServicesInfo(self):
		import process
		p = process.ProcessList()
		ftp_process = str(p.named('vsftpd')).strip('[]')
		telnet_process = str(p.named('telnetd')).strip('[]')
		ssh_process = str(p.named('dropbear')).strip('[]')
		crond_process = str(p.named('crond')).strip('[]')
		samba_process = str(p.named('smbd')).strip('[]')
		openvpn_process = str(p.named('openvpn')).strip('[]')
		nfs_process = str(p.named('nfsd')).strip('[]')
		afp_process = str(p.named('afpd')).strip('[]')
		sabnzbd_process = str(p.named('SABnzbd.py')).strip('[]')
		minidlna_process = str(p.named('minidlnad')).strip('[]')
		inadyn_process = str(p.named('inadyn-mt')).strip('[]')
		ushare_process = str(p.named('ushare')).strip('[]')

		if ftp_process:
			self["ftp_on"].show()
		else:
			self["ftp_on"].hide()

		if telnet_process:
			self["telnet_on"].show()
		else:
			self["telnet_on"].hide()

		if ssh_process:
			self["ssh_on"].show()
		else:
			self["ssh_on"].hide()

		if crond_process:
			self["crond_on"].show()
		else:
			self["crond_on"].hide()

		if samba_process:
			self["smb_on"].show()
		else:
			self["smb_on"].hide()

		if openvpn_process:
			self["vpn_on"].show()
		else:
			self["vpn_on"].hide()

		if nfs_process:
			self["nfs_on"].show()
		else:
			self["nfs_on"].hide()

		if afp_process:
			self["afp_on"].show()
		else:
			self["afp_on"].hide()

		if sabnzbd_process:
			self["sabnzbd_on"].show()
		else:
			self["sabnzbd_on"].hide()

		if minidlna_process:
			self["minidlna_on"].show()
		else:
			self["minidlna_on"].hide()

		if inadyn_process:
			self["inadyn_on"].show()
		else:
			self["inadyn_on"].hide()

		if ushare_process:
			self["ushare_on"].show()
		else:
			self["ushare_on"].hide()

######## Main Menu ##############################
	def MainQmenu(self):
		self.menu = 0
		self.list = []
		self.oldlist = []
		self.list.append(spaMenuEntryComponent("Software Manager", _("Update/Backup/Restore your box"), _("Update/Backup your firmware, Backup/Restore settings")))
		if Check_Softcam():
			self.list.append(spaMenuEntryComponent("Softcam", _("Start/stop/select cam"), _("Start/stop/select your cam, You need to install first a softcam")))
		self.list.append(spaMenuEntryComponent("System", _("System Setup"), _("Setup your System")))
		self.list.append(spaMenuEntryComponent("Mounts", _("Mount Setup"), _("Setup your mounts for network")))
		self.list.append(spaMenuEntryComponent("Network", _("Setup your local network"), _("Setup your local network. For Wlan you need to boot with a USB-Wlan stick")))
		self.list.append(spaMenuEntryComponent("AV Setup", _("Setup Video/Audio"), _("Setup your Video Mode, Video Output and other Video Settings")))
		self.list.append(spaMenuEntryComponent("Tuner Setup", _("Setup Tuner"), _("Setup your Tuner and search for channels")))
		self.list.append(spaMenuEntryComponent("Plugins", _("Setup Plugins"), _("Shows available pluigns. Here you can download and install them")))
		self.list.append(spaMenuEntryComponent("Additional Features", _("Additional Features"), _("Shows available additional pluigns")))
		self.list.append(spaMenuEntryComponent("Harddisk", _("Harddisk Setup"), _("Setup your Harddisk")))
		self["list"].l.setList(self.list)

######## System Setup Menu ##############################
	def Qsystem(self):
		self.sublist = []
		self.sublist.append(spaMenuEntryComponent("Customise", _("Setup Enigma2"), _("Customise enigma2 personal settings")))
		self.sublist.append(spaMenuEntryComponent("OSD settings", _("OSD Setup"), _("Setup your OSD")))
		if SystemInfo["FrontpanelDisplay"] and SystemInfo["Display"]:
			self.sublist.append(spaMenuEntryComponent("Display Settings", _("Display Setup"), _("Setup your display")))
		if SystemInfo["LCDSKINSetup"]:
			self.sublist.append(spaMenuEntryComponent("LCD Skin Setup", _("Select LCD Skin"), _("Setup your LCD")))
		self.sublist.append(spaMenuEntryComponent("Skin Setup", _("Select Enigma2 Skin"), _("Setup your Skin")))
		self.sublist.append(spaMenuEntryComponent("Keymap Selection", _("Select Keymap"), _("Select your keymap style")))
		self.sublist.append(spaMenuEntryComponent("Recording settings", _("Recording Setup"), _("Setup your recording config")))
		self.sublist.append(spaMenuEntryComponent("EPG settings", _("EPG Setup"), _("Setup your EPG config")))
		self["sublist"].l.setList(self.sublist)

######## Network Menu ##############################
	def Qnetwork(self):
		self.sublist = []
		self.sublist.append(spaMenuEntryComponent("Network Wizard", _("Configure your Network"), _("Use the Networkwizard to configure your Network. The wizard will help you to setup your network")))
		if len(self.adapters) > 1: # show only adapter selection if more as 1 adapter is installed
			self.sublist.append(spaMenuEntryComponent("Network Adapter Selection", _("Select Lan/Wlan"), _("Setup your network interface. If no Wlan stick is used, you only can select Lan")))
		if not self.activeInterface == None: # show only if there is already a adapter up
			self.sublist.append(spaMenuEntryComponent("Network Interface", _("Setup interface"), _("Setup network. Here you can setup DHCP, IP, DNS")))
		self.sublist.append(spaMenuEntryComponent("Network Restart", _("Restart network to with current setup"), _("Restart network and remount connections")))
		self.sublist.append(spaMenuEntryComponent("Network Services", _("Setup Network Services"), _("Setup Network Services (Samba, Ftp, NFS, ...)")))
		self["sublist"].l.setList(self.sublist)

#### Network Services Menu ##############################
	def Qnetworkservices(self):
		self.sublist = []
		self.sublist.append(spaMenuEntryComponent("Samba", _("Setup Samba"), _("Setup Samba")))
		self.sublist.append(spaMenuEntryComponent("NFS", _("Setup NFS"), _("Setup NFS")))
		self.sublist.append(spaMenuEntryComponent("FTP", _("Setup FTP"), _("Setup FTP")))
		self.sublist.append(spaMenuEntryComponent("AFP", _("Setup AFP"), _("Setup AFP")))
		self.sublist.append(spaMenuEntryComponent("OpenVPN", _("Setup OpenVPN"), _("Setup OpenVPN")))
		self.sublist.append(spaMenuEntryComponent("MiniDLNA", _("Setup MiniDLNA"), _("Setup MiniDLNA")))
		self.sublist.append(spaMenuEntryComponent("Inadyn", _("Setup Inadyn"), _("Setup Inadyn")))
		self.sublist.append(spaMenuEntryComponent("SABnzbd", _("Setup SABnzbd"), _("Setup SABnzbd")))
		self.sublist.append(spaMenuEntryComponent("uShare", _("Setup uShare"), _("Setup uShare")))
		self.sublist.append(spaMenuEntryComponent("Telnet", _("Setup Telnet"), _("Setup Telnet")))
		self["sublist"].l.setList(self.sublist)

######## Mount Settings Menu ##############################
	def Qmount(self):
		self.sublist = []
		self.sublist.append(spaMenuEntryComponent("Mount Manager", _("Manage network mounts"), _("Setup your network mounts")))
		self.sublist.append(spaMenuEntryComponent("Network Browser", _("Search for network shares"), _("Search for network shares")))
		self.sublist.append(spaMenuEntryComponent("Device Manager", _("Mounts Devices"), _("Setup your Device mounts (USB, HDD, others...)")))
		self["sublist"].l.setList(self.sublist)

######## Softcam Menu ##############################
	def Qsoftcam(self):
		self.sublist = []
		if Check_Softcam(): # show only when there is a softcam installed
			self.sublist.append(spaMenuEntryComponent("SoftcamSetup", _("Control your Softcams"), _("Use the Softcam Panel to control your Cam. This let you start/stop/select a cam")))
		if Check_SysSoftcam() is "oscam":
			self.sublist.append(spaMenuEntryComponent("OScamInfo", _("Show OScam Info"), _("Show more detailed information of OScam")))
		if Check_SysSoftcam() is "ncam":
			self.sublist.append(spaMenuEntryComponent("NcamInfo", _("Show Ncam Info"), _("Show more detailed information of Ncam")))
		self.sublist.append(spaMenuEntryComponent("Download Softcams", _("Download and install cam"), _("Shows available softcams. Here you can download and install them")))
		self["sublist"].l.setList(self.sublist)

######## A/V Settings Menu ##############################
	def Qavsetup(self):
		self.sublist = []
		self.sublist.append(spaMenuEntryComponent("Video Settings", _("Setup Videomode"), _("Setup your Video Mode, Video Output and other Video Settings")))
		self.sublist.append(spaMenuEntryComponent("Audio Settings", _("Setup Audiomode"), _("Setup your Audio Mode")))
		if AUDIOSYNC == True:
			self.sublist.append(spaMenuEntryComponent("Audio Sync", _("Setup Audio Sync"), _("Setup Audio Sync settings")))
		self.sublist.append(spaMenuEntryComponent("Auto Language", _("Auto Language Selection"), _("Select your Language for Audio/Subtitles")))
		if os_path.exists("/proc/stb/vmpeg/0/pep_apply") and VIDEOENH == True:
			self.sublist.append(spaMenuEntryComponent("VideoEnhancement", _("VideoEnhancement Setup"), _("VideoEnhancement Setup")))

		self["sublist"].l.setList(self.sublist)

######## Tuner Menu ##############################
	def Qtuner(self):
		self.sublist = []
		self.sublist.append(spaMenuEntryComponent("Tuner Configuration", _("Setup tuner(s)"), _("Setup each tuner for your satellite system")))
		if POSSETUP == True:
			self.sublist.append(spaMenuEntryComponent("Positioner Setup", _("Setup rotor"), _("Setup your positioner for your satellite system")))
		self.sublist.append(spaMenuEntryComponent("Automatic Scan", _("Automatic Service Searching"), _("Automatic scan for services")))
		self.sublist.append(spaMenuEntryComponent("Manual Scan", _("Manual Service Searching"), _("Manual scan for services")))
		if SATFINDER == True:
			self.sublist.append(spaMenuEntryComponent("Sat Finder", _("Search Sats"), _("Search Sats, check signal and lock")))
		self["sublist"].l.setList(self.sublist)

######## Software Manager Menu ##############################
	def Qsoftware(self):
		self.sublist = []
		self.sublist.append(spaMenuEntryComponent("Software Update", _("Online software update"), _("Check/Install online updates (you must have a working internet connection)")))
		if not getBoxType().startswith('az') and not getBoxType() in ('dm500hd', 'dm500hdv2', 'dm520', 'dm800', 'dm800se', 'dm800sev2', 'dm820', 'dm7020hd', 'dm7020hdv2', 'dm7080', 'dm8000') and not getBrandOEM().startswith('cube'):
			self.sublist.append(spaMenuEntryComponent("Flash Online", _("Flash Online a new image"), _("Flash on the fly your your Receiver software.")))
		if not getBoxType().startswith('az') and not getBrandOEM().startswith('cube') and not getBrandOEM().startswith('wetek'):
			self.sublist.append(spaMenuEntryComponent("Complete Backup", _("Backup your current image"), _("Backup your current image to HDD or USB. This will make a 1:1 copy of your box")))
		self.sublist.append(spaMenuEntryComponent("Backup Settings", _("Backup your current settings"), _("Backup your current settings. This includes E2-setup, channels, network and all selected files")))
		self.sublist.append(spaMenuEntryComponent("Restore Settings", _("Restore settings from a backup"), _("Restore your settings back from a backup. After restore the box will restart to activated the new settings")))
		self.sublist.append(spaMenuEntryComponent("Show default backup files", _("Show files backed up by default"), _("Here you can browse (but not modify) the files that are added to the backupfile by default (E2-setup, channels, network).")))
		self.sublist.append(spaMenuEntryComponent("Select additional backup files", _("Select additional files to backup"), _("Here you can specify additional files that should be added to the backup file.")))
		self.sublist.append(spaMenuEntryComponent("Select excluded backup files", _("Select files to exclude from backup"), _("Here you can select which files should be excluded from the backup.")))
		self.sublist.append(spaMenuEntryComponent("Software Manager Setup", _("Manage your online update files"), _("Here you can select which files should be updated with a online update")))
		self["sublist"].l.setList(self.sublist)

######## Plugins Menu ##############################
	def Qplugin(self):
		self.sublist = []
		self.sublist.append(spaMenuEntryComponent("Plugin Browser", _("Open the Plugin Browser"), _("Shows Plugins Browser. Here you can setup installed Plugin")))
		self.sublist.append(spaMenuEntryComponent("Download Plugins", _("Download and install Plugins"), _("Shows available plugins. Here you can download and install them")))
		self.sublist.append(spaMenuEntryComponent("Remove Plugins", _("Delete Plugins"), _("Delete and unstall Plugins. This will remove the Plugin from your box")))
		self.sublist.append(spaMenuEntryComponent("Plugin Filter", _("Setup Plugin filter"), _("Setup Plugin filter. Here you can select which Plugins are showed in the PluginBrowser")))
		self.sublist.append(spaMenuEntryComponent("IPK Installer", _("Install local extension"), _("Scan for local extensions and install them")))
		self.sublist.append(spaMenuEntryComponent("IPK Uninstaller", _("Delete installed ipls"), _("Search package ipk installed and delete them")))
		self["sublist"].l.setList(self.sublist)

######## Additional Features Menu ###################
	def Qadditional(self):
		self.sublist = []
		self.sublist.append(spaMenuEntryComponent("Cron Manager", _("Open the Plugin Browser"), _("Shows Plugins Browser. Here you can setup installed Plugin")))
		self.sublist.append(spaMenuEntryComponent("Job Manager", _("Open the Plugin Browser"), _("Shows Plugins Browser. Here you can setup installed Plugin")))
		self.sublist.append(spaMenuEntryComponent("Swap Manager", _("Open the Plugin Browser"), _("Shows Plugins Browser. Here you can setup installed Plugin")))
		self["sublist"].l.setList(self.sublist)

#####################################################

######## Harddisk Menu ##############################
	def Qharddisk(self):
		self.sublist = []
		self.sublist.append(spaMenuEntryComponent("Harddisk Setup", _("Harddisk Setup"), _("Setup your Harddisk")))
		self.sublist.append(spaMenuEntryComponent("Initialization", _("Format HDD"), _("Format your Harddisk")))
		self.sublist.append(spaMenuEntryComponent("Filesystem Check", _("Check HDD"), _("Filesystem check your Harddisk")))
		if isFileSystemSupported("ext4"):
			self.sublist.append(spaMenuEntryComponent("Convert ext3 to ext4", _("Convert filesystem ext3 to ext4"), _("Convert filesystem ext3 to ext4")))
		self["sublist"].l.setList(self.sublist)

	def ok(self):
		if self.menu > 0:
			self.okSubList()
		else:
			self.goRight()

#####################################################################
######## Make Selection MAIN MENU LIST ##############################
#####################################################################
	def okList(self):
		item = self["list"].getCurrent()

######## Select Network Menu ##############################
		if item[0] == _("Network"):
			self.GetNetworkInterfaces()
			self.Qnetwork()
######## Select System Setup Menu ##############################
		elif item[0] == _("System"):
			self.Qsystem()
######## Select Mount Menu ##############################
		elif item[0] == _("Mounts"):
			self.Qmount()
######## Select Softcam Menu ##############################
		elif item[0] == _("Softcam"):
			self.Qsoftcam()
######## Select AV Setup Menu ##############################
		elif item[0] == _("AV Setup"):
			self.Qavsetup()
######## Select Tuner Setup Menu ##############################
		elif item[0] == _("Tuner Setup"):
			self.Qtuner()
######## Select Software Manager Menu ##############################
		elif item[0] == _("Software Manager"):
			self.Qsoftware()
######## Select PluginDownloadBrowser Menu ##############################
		elif item[0] == _("Plugins"):
			self.Qplugin()
######## Select PluginDownloadBrowser Menu ##############################
		elif item[0] == _("Additional Features"):
			self.Qadditional()
######## Select Harddisk Setup Menu ##############################
		elif item[0] == _("Harddisk"):
			self.Qharddisk()

		self["sublist"].selectionEnabled(0)

#####################################################################
######## Make Selection SUB MENU LIST ##############################
#####################################################################

	def okSubList(self):
		item = self["sublist"].getCurrent()

######## Select Network Menu ##############################
		if item[0] == _("Network Wizard"):
			self.session.open(NetworkWizard)
		elif item[0] == _("Network Adapter Selection"):
			self.session.open(NetworkAdapterSelection)
		elif item[0] == _("Network Interface"):
			self.session.open(AdapterSetup, self.activeInterface)
		elif item[0] == _("Network Restart"):
			self.session.open(RestartNetwork)
		elif item[0] == _("Network Services"):
			self.Qnetworkservices()
			self["sublist"].moveToIndex(0)
		elif item[0] == _("Samba"):
			try:
				self.session.open(NetworkSamba)
			except:
				self.session.open(MessageBox, _("Sorry not found!"), MessageBox.TYPE_INFO, timeout=10)
		elif item[0] == _("NFS"):
			try:
				self.session.open(NetworkNfs)
			except:
				self.session.open(MessageBox, _("Sorry not found!"), MessageBox.TYPE_INFO, timeout=10)
		elif item[0] == _("FTP"):
			try:
				self.session.open(NetworkFtp)
			except:
				self.session.open(MessageBox, _("Sorry not found!"), MessageBox.TYPE_INFO, timeout=10)
		elif item[0] == _("AFP"):
			try:
				self.session.open(NetworkAfp)
			except:
				self.session.open(MessageBox, _("Sorry not found!"), MessageBox.TYPE_INFO, timeout=10)
		elif item[0] == _("OpenVPN"):
			try:
				self.session.open(NetworkOpenvpn)
			except:
				self.session.open(MessageBox, _("Sorry not found!"), MessageBox.TYPE_INFO, timeout=10)
		elif item[0] == _("MiniDLNA"):
			try:
				self.session.open(NetworkMiniDLNA)
			except:
				self.session.open(MessageBox, _("Sorry not found!"), MessageBox.TYPE_INFO, timeout=10)
		elif item[0] == _("Inadyn"):
			try:
				self.session.open(NetworkInadyn)
			except:
				self.session.open(MessageBox, _("Sorry not found!"), MessageBox.TYPE_INFO, timeout=10)
		elif item[0] == _("SABnzbd"):
			try:
				self.session.open(NetworkSABnzbd)
			except:
				self.session.open(MessageBox, _("Sorry not found!"), MessageBox.TYPE_INFO, timeout=10)
		elif item[0] == _("uShare"):
			try:
				self.session.open(NetworkuShare)
			except:
				self.session.open(MessageBox, _("Sorry not found!"), MessageBox.TYPE_INFO, timeout=10)
		elif item[0] == _("Telnet"):
			try:
				self.session.open(NetworkTelnet)
			except:
				self.session.open(MessageBox, _("Sorry not found!"), MessageBox.TYPE_INFO, timeout=10)
######## Select System Setup Menu ##############################
		elif item[0] == _("Customise"):
			self.openSetup("usage")
		elif item[0] == _("Display Settings"):
			self.openSetup("display")
		elif item[0] == _("LCD Skin Setup"):
			self.session.open(LcdSkinSelector)
		elif item[0] == _("Skin Setup"):
			self.session.open(SkinSelector)
		elif item[0] == _("OSD settings"):
			self.openSetup("userinterface")
		elif item[0] == _("Keymap Selection"):
			self.session.open(KeymapSel)
		elif item[0] == _("Recording settings"):
			self.openSetup("recording")
		elif item[0] == _("EPG settings"):
			self.session.open(EPGScreen)
######## Select Mounts Menu ##############################
		elif item[0] == _("Mount Manager"):
			self.session.open(AutoMountManager, None, plugin_path_networkbrowser)
		elif item[0] == _("Network Browser"):
			self.session.open(NetworkBrowser, None, plugin_path_networkbrowser)
		elif item[0] == _("Device Manager"):
			self.session.open(HddMount)
######## Select Softcam Menu ##############################
		elif item[0] == "SoftcamSetup":
			self.session.open(SoftcamSetup)
		elif item[0] == "OScamInfo":
			from Screens.OScamInfo import OscamInfoMenu
			self.session.open(OscamInfoMenu)
		elif item[0] == "NcamInfo":
			from Screens.NcamInfo import NcamInfoMenu
			self.session.open(NcamInfoMenu)
		elif item[0] == _("Download Softcams"):
			self.session.open(PluginDownloadBrowser)
######## Select AV Setup Menu ##############################
		elif item[0] == _("Video Settings"):
			self.session.open(VideoSetup)
		elif item[0] == _("Audio Settings"):
			self.session.open(AudioSetup)
		elif item[0] == _("Auto Language"):
			self.openSetup("autolanguagesetup")
		elif item[0] == _("Audio Sync"):
			self.session.open(AC3LipSyncSetup, plugin_path_audiosync)
		elif item[0] == _("VideoEnhancement"):
			self.session.open(VideoEnhancementSetup)
######## Select TUNER Setup Menu ##############################
		elif item[0] == _("Tuner Configuration"):
			self.session.open(NimSelection)
		elif item[0] == _("Positioner Setup"):
			self.PositionerMain()
		elif item[0] == _("Automatic Scan"):
			self.session.open(ScanSimple)
		elif item[0] == _("Manual Scan"):
			self.session.open(ScanSetup)
		elif item[0] == _("Sat Finder"):
			self.SatfinderMain()
######## Select Software Manager Menu ##############################
		elif item[0] == _("Software Update"):
			self.session.open(SoftwarePanel)
		elif item[0] == _("Flash Online"):
			self.session.open(FlashOnline)
		elif item[0] == _("Complete Backup"):
			if DFLASH == True:
				self.session.open(dFlash)
			elif DBACKUP == True:
				self.session.open(dBackup)
			else:
				self.session.open(ImageBackup)
		elif item[0] == _("Backup Settings"):
			self.session.openWithCallback(self.backupDone, BackupScreen, runBackup=True)
		elif item[0] == _("Restore Settings"):
			self.backuppath = getBackupPath()
			if not path.isdir(self.backuppath):
				self.backuppath = getOldBackupPath()
			self.backupfile = getBackupFilename()
			self.fullbackupfilename = self.backuppath + "/" + self.backupfile
			if os_path.exists(self.fullbackupfilename):
				self.session.openWithCallback(self.startRestore, MessageBox, _("Are you sure you want to restore your %s %s backup?\nSTB will restart after the restore") % (getMachineBrand(), getMachineName()), default=False)
			else:
				self.session.open(MessageBox, _("Sorry no backups found!"), MessageBox.TYPE_INFO, timeout=10)
		elif item[0] == _("Show default backup files"):
			self.session.open(BackupSelection, title=_("Default files/folders to backup"), configBackupDirs=config.plugins.configurationbackup.backupdirs_default, readOnly=True)
		elif item[0] == _("Select additional backup files"):
			self.session.open(BackupSelection, title=_("Additional files/folders to backup"), configBackupDirs=config.plugins.configurationbackup.backupdirs, readOnly=False)
		elif item[0] == _("Select excluded backup files"):
			self.session.open(BackupSelection, title=_("Files/folders to exclude from backup"), configBackupDirs=config.plugins.configurationbackup.backupdirs_exclude, readOnly=False)
		elif item[0] == _("Software Manager Setup"):
			self.session.open(SoftwareManagerSetup)
######## Select PluginDownloadBrowser Menu ##############################
		elif item[0] == _("Plugin Browser"):
			self.session.open(PluginBrowser)
		elif item[0] == _("Download Plugins"):
			self.session.open(PluginDownloadBrowser, 0)
		elif item[0] == _("Remove Plugins"):
			self.session.open(PluginDownloadBrowser, 1)
		elif item[0] == _("Plugin Filter"):
			self.session.open(PluginFilter)
		elif item[0] == _("IPK Installer"):
			try:
				from Plugins.Extensions.MediaScanner.plugin import main
				main(self.session)
			except:
				self.session.open(MessageBox, _("Sorry MediaScanner is not installed!"), MessageBox.TYPE_INFO, timeout=10)
		elif item[0] == _("IPK Uninstaller"):
			try:
				from Screens.Ipkuninstall import Ipkuninstall
				self.session.open(Ipkuninstall)
			except:
				self.session.open(MessageBox, _("Sorry IPK Uninstaller is not installed!"), MessageBox.TYPE_INFO, timeout=10)
######## Select Addition Features Menu ###################################
		elif item[0] == _("Cron Manager"):
			self.session.open(CronManager)
		elif item[0] == _("Job Manager"):
			self.session.open(ScriptRunner)
		elif item[0] == _("Swap Manager"):
			self.session.open(Swap)
######## Select Harddisk Menu ############################################
		elif item[0] == _("Harddisk Setup"):
			self.openSetup("harddisk")
		elif item[0] == _("Initialization"):
			self.session.open(HarddiskSelection)
		elif item[0] == _("Filesystem Check"):
			self.session.open(HarddiskFsckSelection)
		elif item[0] == _("Convert ext3 to ext4"):
			self.session.open(HarddiskConvertExt4Selection)

######## OPEN SETUP MENUS ####################
	def openSetup(self, dialog):
		self.session.openWithCallback(self.menuClosed, Setup, dialog)

	def menuClosed(self, *res):
		pass

######## NETWORK TOOLS #######################
	def GetNetworkInterfaces(self):
		self.adapters = [(iNetwork.getFriendlyAdapterName(x), x) for x in iNetwork.getAdapterList()]

		if not self.adapters:
			self.adapters = [(iNetwork.getFriendlyAdapterName(x), x) for x in iNetwork.getConfiguredAdapters()]

		if len(self.adapters) == 0:
			self.adapters = [(iNetwork.getFriendlyAdapterName(x), x) for x in iNetwork.getInstalledAdapters()]

		self.activeInterface = None
	
		for x in self.adapters:
			if iNetwork.getAdapterAttribute(x[1], 'up') is True:
				self.activeInterface = x[1]
				return

######## TUNER TOOLS #######################
	def PositionerMain(self):
		nimList = nimmanager.getNimListOfType("DVB-S")
		if len(nimList) == 0:
			self.session.open(MessageBox, _("No positioner capable frontend found."), MessageBox.TYPE_ERROR)
		else:
			if len(NavigationInstance.instance.getRecordings()) > 0:
				self.session.open(MessageBox, _("A recording is currently running. Please stop the recording before trying to configure the positioner."), MessageBox.TYPE_ERROR)
			else:
				usableNims = []
				for x in nimList:
					configured_rotor_sats = nimmanager.getRotorSatListForNim(x)
					if len(configured_rotor_sats) != 0:
						usableNims.append(x)
				if len(usableNims) == 1:
					self.session.open(PositionerSetup, usableNims[0])
				elif len(usableNims) > 1:
					self.session.open(RotorNimSelection)
				else:
					self.session.open(MessageBox, _("No tuner is configured for use with a diseqc positioner!"), MessageBox.TYPE_ERROR)

	def SatfinderMain(self):
		nims = nimmanager.getNimListOfType("DVB-S")

		nimList = []
		for x in nims:
			if not nimmanager.getNimConfig(x).dvbs.configMode.value in ("loopthrough", "satposdepends", "nothing"):
				nimList.append(x)

		if len(nimList) == 0:
			self.session.open(MessageBox, _("No satellite frontend found!!"), MessageBox.TYPE_ERROR)
		else:
			if len(NavigationInstance.instance.getRecordings(False, pNavigation.isAnyRecording)) > 0:
				self.session.open(MessageBox, _("A recording is currently running. Please stop the recording before trying to start the satfinder."), MessageBox.TYPE_ERROR)
			else:
				self.session.open(Satfinder)

######## SOFTWARE MANAGER TOOLS #######################
	def backupDone(self, retval=None):
		if retval is True:
			self.session.open(MessageBox, _("Backup done."), MessageBox.TYPE_INFO, timeout=10)
		else:
			self.session.open(MessageBox, _("Backup failed."), MessageBox.TYPE_INFO, timeout=10)

	def startRestore(self, ret=False):
		if (ret == True):
			self.exe = True
			self.session.open(RestoreScreen, runRestore=True)


######## Create MENULIST format #######################
def spaMenuEntryComponent(name, description, long_description=None, width=540):
	pngname = name.replace(" ", "_") 
	png = LoadPixmap("/usr/lib/enigma2/python/Plugins/Extensions/spaTeam/icons/" + pngname + ".png")
	if png is None:
		png = LoadPixmap("/usr/lib/enigma2/python/Plugins/Extensions/spaTeam/icons/empty.png")

	screenwidth = getDesktop(0).size().width()
	if screenwidth and screenwidth == 1920:
		width *= 1.5
		return [
			_(name),
			MultiContentEntryText(pos=(90, 5), size=(width - 90, 38), font=0, text=_(name)),
			MultiContentEntryText(pos=(90, 38), size=(width - 90, 30), font=1, text=_(description)),
			MultiContentEntryPixmapAlphaBlend(pos=(15, 8), size=(60, 60), png=png, backcolor=0x000000),
			MultiContentEntryText(pos=(0, 0), size=(0, 0), font=0, text=_(long_description))
		]
	else:
		return [
			_(name),
			MultiContentEntryText(pos=(60, 3), size=(width - 60, 25), font=0, text=_(name)),
			MultiContentEntryText(pos=(60, 25), size=(width - 60, 20), font=1, text=_(description)),
			MultiContentEntryPixmapAlphaBlend(pos=(10, 5), size=(40, 40), png=png, backcolor=0x000000),
			MultiContentEntryText(pos=(0, 0), size=(0, 0), font=0, text=_(long_description))
		]


def spaSubMenuEntryComponent(name, description, long_description=None, width=540):
	screenwidth = getDesktop(0).size().width()
	if screenwidth and screenwidth == 1920:
		width *= 1.5
		return [
			_(name),
			MultiContentEntryText(pos=(15, 5), size=(width - 15, 38), font=0, text=_(name)),
			MultiContentEntryText(pos=(15, 38), size=(width - 15, 30), font=1, text=_(description)),
			MultiContentEntryText(pos=(0, 0), size=(0, 0), font=0, text=_(long_description))
		]
	else:
		return [
			_(name),
			MultiContentEntryText(pos=(10, 3), size=(width - 10, 25), font=0, text=_(name)),
			MultiContentEntryText(pos=(10, 25), size=(width - 10, 20), font=1, text=_(description)),
			MultiContentEntryText(pos=(0, 0), size=(0, 0), font=0, text=_(long_description))
		]


class spaMenuList(MenuList):
	def __init__(self, list, enableWrapAround=True):
		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)
		screenwidth = getDesktop(0).size().width()
		if screenwidth and screenwidth == 1920:
			self.l.setFont(0, gFont("Regular", 30))
			self.l.setFont(1, gFont("Regular", 24))
			self.l.setItemHeight(75)
		else:
			self.l.setFont(0, gFont("Regular", 20))
			self.l.setFont(1, gFont("Regular", 16))
			self.l.setItemHeight(50)


class spaMenuSubList(MenuList):
	def __init__(self, sublist, enableWrapAround=True):
		MenuList.__init__(self, sublist, enableWrapAround, eListboxPythonMultiContent)
		screenwidth = getDesktop(0).size().width()
		if screenwidth and screenwidth == 1920:
			self.l.setFont(0, gFont("Regular", 30))
			self.l.setFont(1, gFont("Regular", 24))
			self.l.setItemHeight(75)
		else:
			self.l.setFont(0, gFont("Regular", 20))
			self.l.setFont(1, gFont("Regular", 16))
			self.l.setItemHeight(50)


class spaMenuDevices(Screen):
	skin = """
		<screen name="spaMenuDevices" position="center,center" size="840,525" title="Devices" flags="wfBorder">
		<widget source="devicelist" render="Listbox" position="30,46" size="780,450" font="Regular;16" scrollbarMode="showOnDemand" transparent="1" backgroundColorSelected="grey" foregroundColorSelected="black">
		<convert type="TemplatedMultiContent">
				{"template": [
				 MultiContentEntryText(pos = (90, 0), size = (600, 30), font=0, text = 0),
				 MultiContentEntryText(pos = (110, 30), size = (600, 50), font=1, flags = RT_VALIGN_TOP, text = 1),
				 MultiContentEntryPixmapAlphaBlend(pos = (0, 0), size = (80, 80), png = 2),
				],
				"fonts": [gFont("Regular", 24),gFont("Regular", 20)],
				"itemHeight": 85
				}
			</convert>
	</widget>
	<widget name="lab1" zPosition="2" position="126,92" size="600,40" font="Regular;22" halign="center" backgroundColor="black" transparent="1" />
	</screen> """

	def __init__(self, session):
		Screen.__init__(self, session)
		Screen.setTitle(self, _("Devices"))
		self['lab1'] = Label()
		self.devicelist = []
		self['devicelist'] = List(self.devicelist)

		self['actions'] = ActionMap(['WizardActions'], 
		{
			'back': self.close,
		})
		self.activityTimer = eTimer()
		self.activityTimer.timeout.get().append(self.updateList2)
		self.updateList()

	def updateList(self, result=None, retval=None, extra_args=None):
		scanning = _("Wait please while scanning for devices...")
		self['lab1'].setText(scanning)
		self.activityTimer.start(10)

	def updateList2(self):
		self.activityTimer.stop()
		self.devicelist = []
		list2 = []
		f = open('/proc/partitions', 'r')
		for line in f.readlines():
			parts = line.strip().split()
			if not parts:
				continue
			device = parts[3]
			if not search('sd[a-z][1-9]', device):
				continue
			if device in list2:
				continue
			self.buildMy_rec(device)
			list2.append(device)

		f.close()
		self['devicelist'].list = self.devicelist
		if len(self.devicelist) == 0:
			self['lab1'].setText(_("No Devices Found !!"))
		else:
			self['lab1'].hide()

	def buildMy_rec(self, device):
		device2 = device[:-1]	#strip device number
		devicetype = path.realpath('/sys/block/' + device2 + '/device')
		d2 = device
		name = 'USB: '
		mypixmap = '/usr/lib/enigma2/python/Plugins/Extensions/spaTeam/icons/dev_usbstick.png'
		model = file('/sys/block/' + device2 + '/device/model').read()
		model = str(model).replace('\n', '')
		des = ''
		if devicetype.find('/devices/pci') != -1:
			name = _("HARD DISK: ")
			mypixmap = '/usr/lib/enigma2/python/Plugins/Extensions/spaTeam/icons/dev_hdd.png'
		name = name + model

		from Components.Console import Console
		self.Console = Console()
		self.Console.ePopen("sfdisk -l /dev/sd? | grep swap | awk '{print $(NF-9)}' >/tmp/devices.tmp")
		sleep(0.5)
		f = open('/tmp/devices.tmp', 'r')
		swapdevices = f.read()
		f.close()
		swapdevices = swapdevices.replace('\n', '')
		swapdevices = swapdevices.split('/')
		f = open('/proc/mounts', 'r')
		for line in f.readlines():
			if line.find(device) != -1:
				parts = line.strip().split()
				d1 = parts[1]
				dtype = parts[2]
				rw = parts[3]
				break
				continue
			else:
				if device in swapdevices:
					parts = line.strip().split()
					d1 = _("None")
					dtype = 'swap'
					rw = _("None")
					break
					continue
				else:
					d1 = _("None")
					dtype = _("unavailable")
					rw = _("None")
		f.close()
		f = open('/proc/partitions', 'r')
		for line in f.readlines():
			if line.find(device) != -1:
				parts = line.strip().split()
				size = int(parts[2])
				if ((size / 1024) / 1024) > 1:
					des = _("Size: ") + str((size / 1024) / 1024) + _("GB")
				else:
					des = _("Size: ") + str(size / 1024) + _("MB")
			else:
				try:
					size = file('/sys/block/' + device2 + '/' + device + '/size').read()
					size = str(size).replace('\n', '')
					size = int(size)
				except:
					size = 0
				if (((size / 2) / 1024) / 1024) > 1:
					des = _("Size: ") + str(((size / 2) / 1024) / 1024) + _("GB")
				else:
					des = _("Size: ") + str((size / 2) / 1024) + _("MB")
		f.close()
		if des != '':
			if rw.startswith('rw'):
				rw = ' R/W'
			elif rw.startswith('ro'):
				rw = ' R/O'
			else:
				rw = ""
			des += '\t' + _("Mount: ") + d1 + '\n' + _("Device: ") + ' /dev/' + device + '\t' + _("Type: ") + dtype + rw
			png = LoadPixmap(mypixmap)
			res = (name, des, png)
			self.devicelist.append(res)


class KeymapSel(ConfigListScreen, Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		self.skinName = ["SetupInfo", "Setup"]
		Screen.setTitle(self, _("Keymap Selection") + "...")
		self.setup_title = _("Keymap Selection") + "..."
		self["HelpWindow"] = Pixmap()
		self["HelpWindow"].hide()
		self["status"] = StaticText()
		self["footnote"] = Label()
		self["description"] = Label("")

		usrkey = eEnv.resolve("${datadir}/enigma2/keymap.usr")
		ntrkey = eEnv.resolve("${datadir}/enigma2/keymap.ntr")
		u80key = eEnv.resolve("${datadir}/enigma2/keymap.u80")
		self.actkeymap = self.getKeymap(config.usage.keymap.value)
		keySel = [('keymap.xml', _("Default  (keymap.xml)"))]
		if path.isfile(usrkey):
			keySel.append(('keymap.usr', _("User  (keymap.usr)")))
		if path.isfile(ntrkey):
			keySel.append(('keymap.ntr', _("Neutrino  (keymap.ntr)")))
		if path.isfile(u80key):
			keySel.append(('keymap.u80', _("UP80  (keymap.u80)")))
		if self.actkeymap == usrkey and not path.isfile(usrkey):
			setDefaultKeymap()
		if self.actkeymap == ntrkey and not path.isfile(ntrkey):
			setDefaultKeymap()
		if self.actkeymap == u80key and not path.isfile(u80key):
			setDefaultKeymap()
		self.keyshow = ConfigSelection(keySel)
		self.keyshow.value = self.actkeymap

		self.onChangedEntry = []
		self.list = []
		ConfigListScreen.__init__(self, self.list, session=self.session, on_change=self.changedEntry)
		self.createSetup()

		self["actions"] = ActionMap(["SetupActions", 'ColorActions'],
		{
			"ok": self.keySave,
			"cancel": self.keyCancel,
			"red": self.keyCancel,
			"green": self.keySave,
			"menu": self.keyCancel,
		}, -2)

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		if not self.selectionChanged in self["config"].onSelectionChanged:
			self["config"].onSelectionChanged.append(self.selectionChanged)
		self.selectionChanged()

	def createSetup(self):
		self.editListEntry = None
		self.list = []
		self.list.append(getConfigListEntry(_("Use Keymap"), self.keyshow))

		self["config"].list = self.list
		self["config"].setList(self.list)
		if config.usage.sort_settings.value:
			self["config"].list.sort()

	def selectionChanged(self):
		self["status"].setText(self["config"].getCurrent()[0])

	def changedEntry(self):
		for x in self.onChangedEntry:
			x()
		self.selectionChanged()

	def getCurrentEntry(self):
		return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())

	def getCurrentDescription(self):
		return self["config"].getCurrent() and len(self["config"].getCurrent()) > 2 and self["config"].getCurrent()[2] or ""

	def createSummary(self):
		from Screens.Setup import SetupSummary
		return SetupSummary

	def saveAll(self):
		config.usage.keymap.value = eEnv.resolve("${datadir}/enigma2/" + self.keyshow.value)
		config.usage.keymap.save()
		configfile.save()
		if self.actkeymap != self.keyshow.value:
			self.changedFinished()

	def keySave(self):
		self.saveAll()
		self.close()

	def cancelConfirm(self, result):
		if not result:
			return
		for x in self["config"].list:
			x[1].cancel()
		self.close()

	def keyCancel(self):
		if self["config"].isChanged():
			self.session.openWithCallback(self.cancelConfirm, MessageBox, _("Really close without saving settings?"))
		else:
			self.close()

	def getKeymap(self, file):
		return file[file.rfind('/') + 1:]

	def changedFinished(self):
		self.session.openWithCallback(self.ExecuteRestart, MessageBox, _("Keymap changed, you need to restart the GUI") + "\n" + _("Do you want to restart now?"), MessageBox.TYPE_YESNO)
		self.close()

	def ExecuteRestart(self, result):
		if result:
			quitMainloop(3)
		else:
			self.close()


def panel(menuid, **kwargs):
	if menuid == "mainmenu":
		return [(_("OpenSPA Panel"), main, "spaTeam", 3)]
	else:
		return []


def main(session, **kwargs):
	session.open(spaMenu)


def Plugins(**kwargs):
	return [
		PluginDescriptor(name=_("OpenSPA Panel"), description=_("OpenSPA Panel"), where=PluginDescriptor.WHERE_MENU, fnc=panel),
		PluginDescriptor(name=_("OpenSPA Panel"), description=_("OpenSPA Panel"), where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main),
		PluginDescriptor(name=_("TimeJump Setup"), description=_("Step back/forward in time playing movies"), where=PluginDescriptor.WHERE_PLUGINMENU, fnc=TimeJumpMain),
		PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART], fnc=SwapAutostart),
		PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART], fnc=TimeJumpAutostart), ]
