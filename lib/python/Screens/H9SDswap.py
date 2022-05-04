import os
from Components.Sources.StaticText import StaticText
from Components.ActionMap import ActionMap
from Components.ChoiceList import ChoiceList, ChoiceEntryComponent
from Components.Console import Console
from Components.Label import Label
from Components.SystemInfo import SystemInfo
from Screens.Standby import TryQuitMainloop
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Tools.BoundFunction import boundFunction
from Tools.Directories import fileExists, fileCheck, pathExists, fileHas
from enigma import getDesktop

def esHD():
	if getDesktop(0).size().width() > 1400:
		return True
	else:
		return False

class H9SDswap(Screen):

	if esHD():
		skin = """
		<screen name="H9SDswap" position="400,75" size="1125,1250" flags="wfNoBorder" backgroundColor="transparent">
		<eLabel name="b" position="0,0" size="1125,950" backgroundColor="#00ffffff" zPosition="-2" />
		<eLabel name="a" position="1,1" size="1122,947" backgroundColor="#00000000" zPosition="-1" />
		<widget source="Title" render="Label" position="90,15" foregroundColor="#00ffffff" size="720,75" halign="left" font="RegularHD; 28" backgroundColor="#00000000" />
		<eLabel name="line" position="1,90" size="1122,1" backgroundColor="#00ffffff" zPosition="1" />
		<eLabel name="line2" position="1,375" size="1122,6" backgroundColor="#00ffffff" zPosition="1" />
		<widget name="config" position="3,420" size="1095,570" halign="center" font="RegularHD; 22" backgroundColor="#00000000" foregroundColor="#00e5b243" />
		<widget source="labe14" render="Label" position="3,120" size="1095,45" halign="center" font="RegularHD; 22" backgroundColor="#00000000" foregroundColor="#00ffffff" />
		<widget source="labe15" render="Label" position="3,195" size="1095,90" halign="center" font="RegularHD; 22" backgroundColor="#00000000" foregroundColor="#00ffffff" />
		<widget source="key_red" render="Label" position="65,300" size="225,45" noWrap="1" zPosition="1" valign="center" font="RegularHD; 20" halign="left" backgroundColor="#00000000" foregroundColor="#00ffffff" />
		<widget source="key_green" render="Label" position="340,300" size="265,45" noWrap="1" zPosition="1" valign="center" font="RegularHD; 20" halign="left" backgroundColor="#00000000" foregroundColor="#00ffffff" />
		<widget source="key_yellow" render="Label" position="685,300" size="225,45" noWrap="1" zPosition="1" valign="center" font="RegularHD; 20" halign="left" backgroundColor="#00000000" foregroundColor="#00ffffff" />
		<ePixmap pixmap="buttons/red_HD.png" position="25,300" size="225,60" alphatest="on" />
		<ePixmap pixmap="buttons/green_HD.png" position="360,300" size="225,60" alphatest="on" />
		<ePixmap pixmap="buttons/yellow_HD.png" position="690,300" size="225,60" alphatest="on" />
	</screen>"""
	else:
		skin = """
		<screen name="H9SDswap" position="250,50" size="750,850" flags="wfNoBorder" backgroundColor="transparent">
		<eLabel name="b" position="0,0" size="750,650" backgroundColor="#00ffffff" zPosition="-2" />
		<eLabel name="a" position="1,1" size="748,648" backgroundColor="#00000000" zPosition="-1" />
		<widget source="Title" render="Label" position="60,10" foregroundColor="#00ffffff" size="480,50" halign="left" font="Regular; 28" backgroundColor="#00000000" />
		<eLabel name="line" position="1,60" size="748,1" backgroundColor="#00ffffff" zPosition="1" />
		<eLabel name="line2" position="1,250" size="748,4" backgroundColor="#00ffffff" zPosition="1" />
		<widget name="config" position="2,280" size="730,380" halign="center" font="Regular; 22" backgroundColor="#00000000" foregroundColor="#00e5b243" />
		<widget source="labe14" render="Label" position="2,80" size="730,30" halign="center" font="Regular; 22" backgroundColor="#00000000" foregroundColor="#00ffffff" />
		<widget source="labe15" render="Label" position="2,130" size="730,60" halign="center" font="Regular; 22" backgroundColor="#00000000" foregroundColor="#00ffffff" />
		<widget source="key_red" render="Label" position="30,200" size="150,30" noWrap="1" zPosition="1" valign="center" font="Regular; 20" halign="left" backgroundColor="#00000000" foregroundColor="#00ffffff" />
		<widget source="key_green" render="Label" position="230,200" size="180,30" noWrap="1" zPosition="1" valign="center" font="Regular; 20" halign="left" backgroundColor="#00000000" foregroundColor="#00ffffff" />
		<widget source="key_yellow" render="Label" position="460,200" size="150,30" noWrap="1" zPosition="1" valign="center" font="Regular; 20" halign="left" backgroundColor="#00000000" foregroundColor="#00ffffff" />
		<ePixmap pixmap="buttons/red.png" position="15,200" size="110,40" alphatest="on" />
		<ePixmap pixmap="buttons/green.png" position="245,200" size="210,40" alphatest="on" />
		<ePixmap pixmap="buttons/yellow.png" position="465,200" size="210,40" alphatest="on" />
	</screen>
	"""

	def __init__(self, session, *args):
		Screen.__init__(self, session)
		self.skinName = "H9SDswap"
		screentitle = _("H9 switch Nand and SDcard")
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("SwaptoNand"))
		self["key_yellow"] = StaticText(_("SwaptoSD"))
		self.title = screentitle
		self.switchtype = " "
		self["actions"] = ActionMap(["ColorActions", "OkCancelActions"],
		{
			"cancel": boundFunction(self.close, None),
			"red": boundFunction(self.close, None),
			"green": self.SwaptoNand,
			"yellow": self.SwaptoSD,
		}, -1)
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle(self.title)

	def SwaptoNand(self):
		self.switchtype = "Nand"
		f = open('/proc/cmdline', 'r').read()
		if "root=/dev/mmcblk0p1"  in f:
			self.container = Console()
			self.container.ePopen("dd if=/usr/share/bootargs-nand.bin of=/dev/mtdblock1", self.Unm)
		else:
			self.session.open(MessageBox, _("H9 SDcard switch ERROR! - already on Nand"), MessageBox.TYPE_INFO, timeout=20)

	def SwaptoSD(self):
		self.switchtype = "mmc"
		f = open('/proc/cmdline', 'r').read()
		print("[H9SDswap] switchtype %s cmdline %s" %(self.switchtype, f))
		if "root=/dev/mmcblk0p1" in f:
			self.session.open(MessageBox, _("H9 SDcard switch ERROR! - already on mmc"), MessageBox.TYPE_INFO, timeout=20)
		elif os.path.isfile("/media/mmc/usr/bin/enigma2"):
			self.container = Console()
			self.container.ePopen("dd if=/usr/share/bootargs-mmc.bin of=/dev/mtdblock1", self.Unm)
		else:
			self.session.open(MessageBox, _("H9 SDcard switch ERROR! - H9 root files not transferred to SD card"), MessageBox.TYPE_INFO, timeout=20)

	def SwaptoUSB(self):
		self.switchtype = "usb"
		f = open('/proc/cmdline', 'r').read()
		print("[H9SDswap] switchtype %s cmdline %s" %(self.switchtype, f))
		if "root=/dev/SDA1" in f:
			self.session.open(MessageBox, _("H9 USB switch ERROR! - already on USB"), MessageBox.TYPE_INFO, timeout=20)
		elif os.path.isfile("/media/mmc/usr/bin/enigma2"):
			self.container = Console()
			self.container.ePopen("dd if=/usr/share/bootargs-usb.bin of=/dev/mtdblock1", self.Unm)
		else:
			self.session.open(MessageBox, _("H9 USB switch ERROR! - H9 root files not transferred to USB"), MessageBox.TYPE_INFO, timeout=20)

	def Unm(self, data=None, retval=None, extra_args=None):
		self.container.killAll()
		self.session.open(TryQuitMainloop, 2)
