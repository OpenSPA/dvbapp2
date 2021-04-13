# -*- coding: utf-8 -*-

from . import _
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.ProgressBar import ProgressBar
from Components.Pixmap import Pixmap
from Components.ScrollLabel import ScrollLabel
from Tools.Directories import fileExists
from enigma import ePoint, eSize, eTimer, getDesktop
from os import system, path, remove
from bitrate import Bitrate
from time import *


class SysInfo(Screen):
	skin = """
		<screen name="SySInfo" position="0,0" size="1280,720" flags="wfNoBorder" backgroundColor="background" title="">
			<widget backgroundColor="background" font="Regular;26" foregroundColor="2ndFG" position="30,15" render="Label" size="1050,35" source="Title" transparent="1" />
			<ePixmap position="545,70" size="7,552" pixmap="skin_default/sysinfo/menuline.png" zPosition="2" alphatest="blend" />
			<!-- Panel Info 1 -->
			<ePixmap pixmap="skin_default/sysinfo/mem.png"  position="163,80" size="40,80" zPosition="2" backgroundColor="background" alphatest="blend" />
			<ePixmap pixmap="skin_default/sysinfo/root.png" position="264,80" size="40,80" zPosition="2" backgroundColor="background" alphatest="blend" />
			<ePixmap pixmap="skin_default/sysinfo/swap.png" position="359,80" size="40,80" zPosition="2" backgroundColor="background" alphatest="blend" />
			<ePixmap pixmap="skin_default/sysinfo/summ.png" position="457,80" size="40,80" zPosition="2" backgroundColor="background" alphatest="blend" />
			<widget name="mem_labels" font="Regular;17" position="50,135"  zPosition="1" size="100,110" valign="top" halign="left" backgroundColor="background" foregroundColor="un666666" transparent="1" />
			<widget name="ram"        font="Regular;17" position="163,135" zPosition="1" size="90,110" valign="top" halign="left" backgroundColor="background" transparent="1" />
			<widget name="root"       font="Regular;17" position="264,135" zPosition="1" size="90,110" valign="top" halign="left" backgroundColor="background" transparent="1" />
			<widget name="swap"       font="Regular;17" position="359,135" zPosition="1" size="90,110" valign="top" halign="left" backgroundColor="background" transparent="1" />
			<widget name="mem_tot"    font="Regular;17" position="454,135" zPosition="1" size="90,110" valign="top" halign="left" backgroundColor="background" transparent="1" />
			<widget name="membar"      position="148,155" size="5,75" pixmap="skin_default/sysinfo/bar.png" orientation="orBottomToTop" zPosition="2" backgroundColor="background" transparent="1" />
			<widget name="rootbar"     position="249,155" size="5,75" pixmap="skin_default/sysinfo/bar.png" orientation="orBottomToTop" zPosition="2" backgroundColor="background" transparent="1" />
			<widget name="swapbar"     position="342,155" size="5,75" pixmap="skin_default/sysinfo/bar.png" orientation="orBottomToTop" zPosition="2" backgroundColor="background" transparent="1" />
			<widget name="memtotalbar" position="437,155" size="5,75" pixmap="skin_default/sysinfo/bar.png" orientation="orBottomToTop" zPosition="2" backgroundColor="background" transparent="1" />
			<ePixmap pixmap="skin_default/sysinfo/bar_back.png" position="148,155" size="5,75" zPosition="1" backgroundColor="background" alphatest="blend" />
			<ePixmap pixmap="skin_default/sysinfo/bar_back.png" position="249,155" size="5,75" zPosition="1" backgroundColor="background" alphatest="blend" />
			<ePixmap pixmap="skin_default/sysinfo/bar_back.png" position="342,155" size="5,75" zPosition="1" backgroundColor="background" alphatest="blend" />
			<ePixmap pixmap="skin_default/sysinfo/bar_back.png" position="437,155" size="5,75" zPosition="1" backgroundColor="background" alphatest="blend" />
			<!-- Panel Info 2 -->
			<ePixmap pixmap="skin_default/sysinfo/hdd.png"    position="163,270" size="40,80" zPosition="2" backgroundColor="background" alphatest="blend" />
			<ePixmap pixmap="skin_default/sysinfo/usbmem.png" position="264,270" size="40,80" zPosition="2" backgroundColor="background" alphatest="blend" />
			<ePixmap pixmap="skin_default/sysinfo/usbmem.png" position="359,270" size="40,80" zPosition="2" backgroundColor="background" alphatest="blend" />
			<ePixmap pixmap="skin_default/sysinfo/usbmem.png" position="454,270" size="40,80" zPosition="2" backgroundColor="background" alphatest="blend" />
			<widget name="space_labels" font="Regular;17" position="50,325" zPosition="1" size="100,110" valign="top" halign="left" backgroundColor="background" foregroundColor="un666666" transparent="1" />
			<widget name="hdd"          font="Regular;17" position="163,325" zPosition="1" size="90,110" valign="top" halign="left" backgroundColor="background" transparent="1" />
			<widget name="usb"          font="Regular;17" position="264,325" zPosition="1" size="90,110" valign="top" halign="left" backgroundColor="background" transparent="1" />
			<widget name="usb1"         font="Regular;17" position="359,325" zPosition="1" size="90,110" valign="top" halign="left" backgroundColor="background" transparent="1" />
			<widget name="usb2"         font="Regular;17" position="454,325" zPosition="1" size="90,110" valign="top" halign="left" backgroundColor="background" transparent="1" />
			<widget name="hddbar"  position="148,340" size="5,75" pixmap="skin_default/sysinfo/bar.png" orientation="orBottomToTop" zPosition="2" backgroundColor="background" transparent="1" />
			<widget name="usbbar"  position="249,340" size="5,75" pixmap="skin_default/sysinfo/bar.png" orientation="orBottomToTop" zPosition="2" backgroundColor="background" transparent="1" />
			<widget name="usb1bar" position="342,340" size="5,75" pixmap="skin_default/sysinfo/bar.png" orientation="orBottomToTop" zPosition="2" backgroundColor="background" transparent="1" />
			<widget name="usb2bar" position="435,340" size="5,75" pixmap="skin_default/sysinfo/bar.png" orientation="orBottomToTop" zPosition="2" backgroundColor="background" transparent="1" />
			<ePixmap pixmap="skin_default/sysinfo/bar_back.png" position="148,340" size="5,75" zPosition="1" backgroundColor="background" alphatest="on" />
			<ePixmap pixmap="skin_default/sysinfo/bar_back.png" position="249,340" size="5,75" zPosition="1" backgroundColor="background" alphatest="on" />
			<ePixmap pixmap="skin_default/sysinfo/bar_back.png" position="342,340" size="5,75" zPosition="1" backgroundColor="background" alphatest="on" />
			<ePixmap pixmap="skin_default/sysinfo/bar_back.png" position="435,340" size="5,75" zPosition="1" backgroundColor="background" alphatest="on" />
			<!-- Panel Info 3 -->
			<widget name="HDDCPULabels"   font="Regular;17" position="50,460"  size="100,110" halign="left" valign="top" noWrap="1" zPosition="1" backgroundColor="background" foregroundColor="un666666" transparent="1" />
			<widget name="usb3"           font="Regular;17" position="163,460" zPosition="1" size="90,110" valign="top" halign="left" backgroundColor="background" transparent="1" />
			<widget name="hddtemperature" font="Regular;17" position="229,460" zPosition="1" size="110,100" valign="top" halign="center" backgroundColor="background" transparent="1" />
			<widget name="cpusys"         font="Regular;17" position="327,460" zPosition="1" size="110,100" valign="top" halign="center" backgroundColor="background" transparent="1" />
			<widget name="cpuusr"         font="Regular;17" position="423,460" zPosition="1" size="110,90" valign="top" halign="center" backgroundColor="background" transparent="1" />
			<ePixmap pixmap="skin_default/sysinfo/hdd_temp.png" position="264,510" size="40,80" zPosition="2" backgroundColor="background" alphatest="blend" />
			<ePixmap pixmap="skin_default/sysinfo/summ.png"     position="359,510" size="40,80" zPosition="2" backgroundColor="background" alphatest="blend" />
			<ePixmap pixmap="skin_default/sysinfo/summ.png"     position="454,510" size="40,80" zPosition="2" backgroundColor="background" alphatest="blend" />
			<widget name="usb3bar"    position="148,480" size="5,75" pixmap="skin_default/sysinfo/bar.png" orientation="orBottomToTop" zPosition="2" backgroundColor="background" transparent="1" />
			<widget name="hddtempbar" position="246,500" size="5,44" pixmap="skin_default/sysinfo/bar.png" orientation="orBottomToTop" zPosition="2" backgroundColor="background" transparent="1" />
			<widget name="cpusysbar"  position="341,500" size="5,44" pixmap="skin_default/sysinfo/bar.png" orientation="orBottomToTop" zPosition="2" backgroundColor="background" transparent="1" />
			<widget name="cpuusrbar"  position="436,500" size="5,44" pixmap="skin_default/sysinfo/bar.png" orientation="orBottomToTop" zPosition="2" backgroundColor="background" transparent="1" />
			<ePixmap pixmap="skin_default/sysinfo/bar_back.png" position="148,480" size="5,75" zPosition="1" backgroundColor="background" alphatest="on" />
			<ePixmap pixmap="skin_default/sysinfo/bar_back.png" position="246,500" size="5,44" zPosition="1" backgroundColor="background" alphatest="on" />
			<ePixmap pixmap="skin_default/sysinfo/bar_back.png" position="341,500" size="5,44" zPosition="1" backgroundColor="background" alphatest="on" />
			<ePixmap pixmap="skin_default/sysinfo/bar_back.png" position="436,500" size="5,44" zPosition="1" backgroundColor="background" alphatest="on" />
			<!-- Panel Time -->
			<widget name="uptime"    position="560,80"  size="32,32" zPosition="2" pixmap="skin_default/sysinfo/clock.png" transparent="1" alphatest="on" />
			<eLabel text="Uptime:"   position="610,80"  size="150,25" font="Regular;20" halign="left" backgroundColor="background" foregroundColor="blue" transparent="1" />
			<widget name="utday"     position="560,110" size="100,25" font="Regular;17" valign="top" halign="left"  zPosition="1" backgroundColor="background" foregroundColor="blue" transparent="1" />
			<widget name="utdayval"  position="640,110" size="100,25" font="Regular;17" valign="top" halign="right" zPosition="1" backgroundColor="background" transparent="1" />
			<widget name="uthour"    position="560,140" size="100,25" font="Regular;17" valign="top" halign="left"  zPosition="1" backgroundColor="background" foregroundColor="blue" transparent="1" />
			<widget name="uthourval" position="640,140" size="100,25" font="Regular;17" valign="top" halign="right" zPosition="1" backgroundColor="background" transparent="1" />
			<widget name="utmin"     position="560,170" size="100,25" font="Regular;17" valign="top" halign="left"  zPosition="1" backgroundColor="background" foregroundColor="blue" transparent="1" />
			<widget name="utminval"  position="640,170" size="100,25" font="Regular;17" valign="top" halign="right" zPosition="1" backgroundColor="background" transparent="1" />
			<widget name="utsec"     position="560,200" size="100,25" font="Regular;17" valign="top" halign="left"  zPosition="1" backgroundColor="background" foregroundColor="blue" transparent="1" />
			<widget name="utsecval"  position="640,200" size="100,25" font="Regular;17" valign="top" halign="right" zPosition="1" backgroundColor="background" transparent="1" />
			<!-- Panel Audio/Video -->
			<widget source="video" render="Label" position="850,80" zPosition="2" foregroundColor="blue" backgroundColor="background" transparent="1" size="80,20" font="Regular;20" />
			<widget source="min" render="Label" position="850,110" zPosition="2" backgroundColor="background" transparent="1" size="80,25" font="Regular;20" />
			<widget name="vmin" position="850,140" size="80,25" font="Regular;20" zPosition="2" backgroundColor="background" transparent="1" />
			<widget source="max" render="Label" position="920,110" zPosition="2" backgroundColor="background" transparent="1" size="80,25" font="Regular;20" />
			<widget name="vmax" position="920,140" size="80,25" font="Regular;20" zPosition="2" backgroundColor="background" transparent="1" />
			<widget source="avg" render="Label" position="990,110" zPosition="2" backgroundColor="background" transparent="1" size="80,25" font="Regular;20" />
			<widget name="vavg" position="990,140" size="80,25" font="Regular;20" zPosition="2" backgroundColor="background" transparent="1" />
			<widget source="cur" render="Label" position="1090,110" zPosition="2" backgroundColor="background" transparent="1" size="80,25" font="Regular;20" />
			<widget name="vcur" position="1090,140" size="80,20" font="Regular;20" zPosition="2" backgroundColor="background" transparent="1" />
			<widget source="audio" render="Label" position="850,170" zPosition="2" foregroundColor="blue" backgroundColor="background" transparent="1" size="80,20" font="Regular;20" />
			<widget source="min" render="Label" position="850,200" zPosition="2" backgroundColor="background" transparent="1" size="80,25" font="Regular;20" />
			<widget name="amin" position="850,230" size="80,25" font="Regular;20" zPosition="2" backgroundColor="background" transparent="1" />
			<widget source="max" render="Label" position="920,200" zPosition="2" backgroundColor="background" transparent="1" size="80,25" font="Regular;20" />
			<widget name="amax" position="920,230" size="80,25" font="Regular;20" zPosition="2" backgroundColor="background" transparent="1" />
			<widget source="avg" render="Label" position="990,200" zPosition="2" backgroundColor="background" transparent="1" size="80,25" font="Regular;20" />
			<widget name="aavg" position="990,230" size="80,25" font="Regular;20" zPosition="2" backgroundColor="background" transparent="1" />
			<widget source="cur" render="Label" position="1090,200" zPosition="2" backgroundColor="background" transparent="1" size="80,25" font="Regular;20" />
			<widget name="acur" position="1090,230" size="80,25" font="Regular;20" zPosition="2" backgroundColor="background" transparent="1" />
			<eLabel position="560, 260" size="680, 1" backgroundColor="background" zPosition="1" />
			<eLabel position="560, 260" size="682, 1" backgroundColor="background" zPosition="1" />
			<!-- Panel Kernel Info -->
			<eLabel text="Kernelversion:" position="560,290" size="140,25"  font="Regular;20" halign="left" foregroundColor="blue" backgroundColor="background" transparent="1" />
			<widget name="kernelversion"  position="560,320" size="680,200" font="Regular;19" halign="left" zPosition="2" backgroundColor="background" transparent="1" />
			<eLabel position="560, 460" size="673, 1" backgroundColor="background" zPosition="1" />
			<eLabel position="560, 462" size="673, 1" backgroundColor="background" zPosition="1" />
			<!-- Panel Audio/Video -->
			<eLabel text="Dmesg Info" font="Regular;20" position="560,460" size="680,25" halign="left" foregroundColor="blue" backgroundColor="background" transparent="1"/>
			<widget name="DmesgInfo"  noWrap="1" position="560,490" size="680,160" font="Regular;17" zPosition="2" halign="left" valign="top" backgroundColor="background" transparent="1" />
			<widget name="key_red" position="30,671" size="300,26" zPosition="1" font="Regular;22" halign="center" foregroundColor="white" backgroundColor="black" transparent="1" />
			<widget name="key_green" position="335,671" size="300,26" zPosition="1" font="Regular;22" halign="center" foregroundColor="white" backgroundColor="black" transparent="1" />
			<widget name="key_yellow" position="640,671" size="300,26" zPosition="1" font="Regular;22" halign="center" foregroundColor="white" backgroundColor="black" transparent="1" valign="center" />
			<eLabel name="bar_red" position="30,667" size="300,3" zPosition="3" backgroundColor="red" />
			<eLabel name="bar_green" position="335,667" size="300,3" zPosition="3" backgroundColor="green" />
			<eLabel name="bar_yellow" position="640,667" size="300,3" zPosition="3" backgroundColor="yellow" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		Screen.setTitle(self, _("System Info Panel"))
		self['mem_labels'] = Label(_('\nTotal:\nFree:\nUsed:\nUsed(%):'))
		self['ram'] = Label()
		self['root'] = Label()
		self['swap'] = Label()
		self['mem_tot'] = Label()
		self['membar'] = ProgressBar()
		self['rootbar'] = ProgressBar()
		self['swapbar'] = ProgressBar()
		self['memtotalbar'] = ProgressBar()
		self['space_labels'] = Label(_('\nTotal:\nFree:\nUsed:\nUsed(%):'))
		self['hdd'] = Label()
		self['usb'] = Label()
		self['usb1'] = Label()
		self['usb2'] = Label()
		self['hddbar'] = ProgressBar()
		self['usbbar'] = ProgressBar()
		self['usb1bar'] = ProgressBar()
		self['usb2bar'] = ProgressBar()
		self['HDDCPULabels'] = Label(_('Sensor:\nValue:'))
		self['usb3'] = Label()
		self['hddtemperature'] = Label(_('HDD Temp:\n....'))
		self['cpusys'] = Label()
		self['cpuusr'] = Label()
		self['usb3bar'] = ProgressBar()
		self['hddtempbar'] = ProgressBar()
		self['cpusysbar'] = ProgressBar()
		self['cpuusrbar'] = ProgressBar()
		self['uptime'] = Pixmap()
		self['utday'] = Label()
		self['uthour'] = Label()
		self['utmin'] = Label()
		self['utsec'] = Label()
		self['utdayval'] = Label()
		self['uthourval'] = Label()
		self['utminval'] = Label()
		self['utsecval'] = Label()
		self['utday'].hide()
		self['uthour'].hide()
		self['utmin'].hide()
		self['utsec'].hide()
		self['utdayval'].hide()
		self['uthourval'].hide()
		self['utminval'].hide()
		self['utsecval'].hide()
		self['kernelversion'] = Label('N/A')
		self['key1'] = Pixmap()
		self['key2'] = Pixmap()
		self['key3'] = Pixmap()
		self['key4'] = Pixmap()
		self['key5'] = Pixmap()
		self['key6'] = Pixmap()
		self['key_red'] = Label(_('Close'))
		self['key_green'] = Label(_('Refresh'))
		self['key_yellow'] = Label(_('Start Bitrate'))
		self['video'] = Label(_('Video'))
		self['audio'] = Label(_('Audio'))
		self['min'] = Label(_('Min'))
		self['max'] = Label(_('Max'))
		self['cur'] = Label(_('Current'))
		self['avg'] = Label(_('Average'))
		self['vmin'] = Label('')
		self['vmax'] = Label('')
		self['vavg'] = Label('')
		self['vcur'] = Label('')
		self['amin'] = Label('')
		self['amax'] = Label('')
		self['aavg'] = Label('')
		self['acur'] = Label('')
		self['DmesgInfo'] = ScrollLabel('')

		self['actions'] = ActionMap(['OkCancelActions', 'WizardActions', 'ColorActions'],
			{
				'down': self.pageDown,
				'up': self.pageUp,
				'ok': self.keyCancel,
				'cancel': self.keyCancel,
				'back': self.keyCancel,
				'red': self.keyCancel,
				'green': self.KeyGreen,
				'yellow': self.KeyYellow,
			})

		self.startDelayTimer = eTimer()
		self.startDelayTimer.callback.append(self.bitrateAfterDelayStart)

		self.bitrate = Bitrate(session, self.refreshEvent, self.bitrateStopped)
		self.onLayoutFinish.append(self.updateList)

	def updateList(self):
		self.getUptime()
		self.getMemInfo()
		self.getSpaceInfo()
		self.getCPUInfo()
		self.getKernelVersion()
		self.bitrateStopped()
		self['DmesgInfo'].setText(self.getDmesg())

	def KeyGreen(self):
		self.refresh()

	def KeyYellow(self):
		if self.bitrateUpdateStatus():
			self.bitrate.stop()
			self['key_yellow'].setText(_('Start Bitrate'))
		else:
			self.bitrate.start()
			self['key_yellow'].setText(_('Stop Bitrate'))

	def keyCancel(self):
		self.bitrate.stop()
		self.close()

	def pageUp(self):
		self['DmesgInfo'].pageUp()

	def pageDown(self):
		self['DmesgInfo'].pageDown()

	def refresh(self):
		self.updateList()

	def bitrateUpdateStart(self, delay=0):
		self.startDelayTimer.stop()
		self.startDelayTimer.start(delay, True)

	def bitrateAfterDelayStart(self):
		if not self.bitrateUpdateStatus():
			self.bitrate.start()

	def bitrateUpdateStatus(self):
		return self.bitrate.running

	def bitrateUpdateStop(self):
		self.startDelayTimer.stop()
		if self.bitrateUpdateStatus():
			self.bitrate.stop()

	def bitrateStopped(self):
		self.refreshEvent()

	def refreshEvent(self):
		self["vmin"].setText(str(self.bitrate.vmin))
		self["vmax"].setText(str(self.bitrate.vmax))
		self["vavg"].setText(str(self.bitrate.vavg))
		self["vcur"].setText(str(self.bitrate.vcur))
		self["amin"].setText(str(self.bitrate.amin))
		self["amax"].setText(str(self.bitrate.amax))
		self["aavg"].setText(str(self.bitrate.aavg))
		self["acur"].setText(str(self.bitrate.acur))

	def getCPUInfo(self):
		cmd = ('mpstat | grep "all" | awk \'{print $3 " " $5}\' > /tmp/cpuinfo.tmp')
		system(cmd)
		if fileExists('/tmp/cpuinfo.tmp'):
			f = open('/tmp/cpuinfo.tmp', 'r')
		line = f.readlines()
		for lines in line:
			parts = lines.split(' ')
			if len(parts) > 1:
				usr = parts[0].replace(' ', '')
				sys = parts[1].replace(' ', '')
				usrint = int(float(usr))
				sysint = int(float(sys))
				self['cpuusrbar'].setValue(usrint)
				self['cpusysbar'].setValue(sysint)
				self['cpuusr'].setText('CPU Usr:\n' + usr + ' %')
				self['cpusys'].setText('CPU Sys:\n' + sys + ' %')
				f.close()
				remove('/tmp/cpuinfo.tmp')
		cmd = ('killall -9 top')
		system(cmd)

	def getUptime(self):
		fp = open('/proc/uptime')
		contents = fp.read().split()
		fp.close()
		total_seconds = float(contents[0])
		days = int(total_seconds / 86400)
		hours = int(total_seconds / 3600 - days * 24)
		minutes = int(total_seconds / 60 - days * 1440 - hours * 60)
		seconds = int(total_seconds % 60)
		if days > 0:
			print days
			if days == 1:
				days = str(days)
				self['utday'].setText(_('Day'))
				self['utday'].show()
				self['utdayval'].setText(days)
				self['utdayval'].show()
			else:
				days = str(days)
				self['utday'].setText(_('Days'))
				self['utday'].show()
				self['utdayval'].setText(days)
				self['utdayval'].show()
		if hours > 0:
			if hours == 1:
				hours = str(hours)
				self['uthour'].setText(_('Hour:'))
				self['uthour'].show()
				self['uthourval'].setText(hours)
				self['uthourval'].show()
			else:
				hours = str(hours)
				self['uthour'].setText(_('Hours:'))
				self['uthour'].show()
				self['uthourval'].setText(hours)
				self['uthourval'].show()
		if minutes > 0:
			if minutes == 1:
				minutes = str(minutes)
				self['utmin'].setText(_('Minute:'))
				self['utmin'].show()
				self['utminval'].setText(minutes)
				self['utminval'].show()
			else:
				minutes = str(minutes)
				self['utmin'].setText(_('Minutes:'))
				self['utmin'].show()
				self['utminval'].setText(minutes)
				self['utminval'].show()
		if seconds > 0:
			if seconds == 1:
				seconds = str(seconds)
				self['utsec'].setText(_('Second:'))
				self['utsec'].show()
				self['utsecval'].setText(seconds)
				self['utsecval'].show()
			else:
				seconds = str(seconds)
				self['utsec'].setText(_('Seconds:'))
				self['utsec'].show()
				self['utsecval'].setText(seconds)
				self['utsecval'].show()

	def getKernelVersion(self):
		try:
			fp = open('/proc/version', 'r')
			line = fp.readline()
			fp.close
		except:
			line = 'N/A'

		self['kernelversion'].setText(line.replace('\n', ''))

	def getMemInfo(self):
		ramperc = 0
		swapperc = 0
		totperc = 0
		ramtot = 0
		swaptot = 0
		tottot = 0
		ramfree = 0
		swapfree = 0
		totfree = 0
		ramused = 0
		swapused = 0
		totused = 0
		rc = system('free -t > /tmp/ninfo.tmp')
		if fileExists('/tmp/ninfo.tmp'):
			f = open('/tmp/ninfo.tmp', 'r')
			for line in f.readlines():
				parts = line.strip().split()
				if parts[0] == 'Mem:':
					ramperc = int(int(parts[2]) * 100 / int(parts[1]))
					ramtot = int(int(parts[1]) / 1000)
					ramfree = int(int(parts[3]) / 1000)
					ramused = int(int(parts[2]) / 1000)
				elif parts[0] == 'Swap:':
					if int(parts[1]) > 1:
						swapperc = int(int(parts[2]) * 100 / int(parts[1]))
						swaptot = int(int(parts[1]) / 1000)
						swapfree = int(int(parts[3]) / 1000)
						swapused = int(int(parts[2]) / 1000)
				elif parts[0] == 'Total:':
					totperc = int(int(parts[2]) * 100 / int(parts[1]))
					tottot = int(int(parts[1]) / 1000)
					totfree = int(int(parts[3]) / 1000)
					totused = int(int(parts[2]) / 1000)
			f.close()
			remove('/tmp/ninfo.tmp')

		self['ram'].setText('Ram:\n' + str(ramtot) + 'MB\n' + str(ramfree) + 'MB\n' + str(ramused) + 'MB\n' + str(ramperc) + '%')
		self['swap'].setText('Swap:\n' + str(swaptot) + 'MB\n' + str(swapfree) + 'MB\n' + str(swapused) + 'MB\n' + str(swapperc) + '%')
		self['mem_tot'].setText('Total:\n' + str(tottot) + 'MB\n' + str(totfree) + 'MB\n' + str(totused) + 'MB\n' + str(totperc) + '%')
		self['memtotalbar'].setValue(int(totperc))
		self['swapbar'].setValue(int(swapperc))
		self['membar'].setValue(int(ramperc))

	def getSpace(self):
		rc = system('df -m > /tmp/ninfo.tmp')
		flashperc = 0
		flashused = 0
		flashtot = 0
		cfused = 0
		cftot = 0
		cfperc = 0
		usused = 0
		ustot = 0
		usperc = 0
		us1used = 0
		us1tot = 0
		us1perc = 0
		hdused = 0
		hdtot = 0
		hdperc = 0
		fperc = 0
		if fileExists('/tmp/ninfo.tmp'):
			f = open('/tmp/ninfo.tmp', 'r')
			for line in f.readlines():
				line = line.replace('part1', ' ')
				parts = line.strip().split()
				totsp = len(parts) - 1
				if parts[totsp] == '/':
					flashperc2 = parts[4]
					flashperc = int(parts[4].replace('%', ''))
					flashtot = int(parts[1])
					flashused = int(parts[2])
				if parts[totsp] == '/media/usb':
					usperc = int(parts[4].replace('%', ''))
					ustot = int(parts[1])
					usused = int(parts[2])
				if parts[totsp] == '/media/usb1':
					us1perc = int(parts[4].replace('%', ''))
					us1tot = int(parts[1])
					us1used = int(parts[2])
				if parts[totsp] == '/media/hdd':
					strview = parts[4].replace('%', '')
					if strview.isdigit():
						hdperc = int(parts[4].replace('%', ''))
						hdtot = int(parts[1])
						hdused = int(parts[2])
			f.close()
			remove('/tmp/ninfo.tmp')

			ftot = cftot + ustot + us1used + hdtot
			fused = int(cfused) + int(usused) + int(us1used) + int(hdused)
			if ftot > 100:
				fperc = fused * 100 / ftot

		self['flashg'].setValue(int(flashperc))
		self['usbg'].setValue(int(usperc * 100 / 120 + 50))
		hddbar = str(hdperc)
		self['hddg'].setValue(int(hdperc))

	def getSpaceInfo(self):
		rc = system('df -h > /tmp/ninfo.tmp')
		flashperc = 0
		flashused = 0
		flashtot = 0
		rootperc = 0
		roottot = 0
		rootused = 0
		rootfree = 0
		usbused = 0
		usbtot = 0
		usbperc = 0
		usb1used = 0
		usb1tot = 0
		usb1perc = 0
		usb2used = 0
		usb2tot = 0
		usb2perc = 0
		usb3used = 0
		usb3tot = 0
		usb3perc = 0
		hddused = 0
		hddtot = 0
		hddperc = 0
		fperc = 0
		usbsumm = 'USB:\n.... \n.... \n.... \n....'
		usb1summ = 'USB1:\n.... \n.... \n.... \n....'
		usb2summ = 'USB2:\n.... \n.... \n.... \n....'
		usb3summ = 'USB3:\n.... \n.... \n.... \n....'
		hddsumm = 'HDD:\n.... \n.... \n.... \n....'
		if fileExists('/tmp/ninfo.tmp'):
			f = open('/tmp/ninfo.tmp', 'r')
			for line in f.readlines():
				line = line.replace('part1', ' ')
				parts = line.strip().split()
				totsp = len(parts) - 1
				if parts[totsp] == '/':
					rootperc = parts[4]
					roottot = parts[1]
					rootused = parts[2]
					rootfree = parts[3]
					self['root'].setText('Flash:\n' + str(roottot) + 'B\n' + str(rootfree) + 'B\n' + str(rootused) + 'B\n' + str(rootperc))
					rootperc = rootperc.replace('%', '')
					self['rootbar'].setValue(int(rootperc))
				if parts[totsp] == '/media/usb':
					usbperc = parts[4]
					usbtot = parts[1]
					usbused = parts[2]
					usbfree = parts[3]
					usbsumm = 'USB:\n' + str(usbtot) + 'B\n' + str(usbfree) + 'B\n' + str(usbused) + 'B\n' + str(usbperc)
					usbperc = usbperc.replace('%', '')
				if parts[totsp] == '/media/usb1':
					usb1perc = parts[4]
					usb1tot = parts[1]
					usb1used = parts[2]
					usb1free = parts[3]
					usb1summ = 'USB1:\n' + str(usb1tot) + 'B\n' + str(usb1free) + 'B\n' + str(usb1used) + 'B\n' + str(usb1perc)
					usb1perc = usb1perc.replace('%', '')
				if parts[totsp] == '/media/usb2':
					usb2perc = parts[4]
					usb2tot = parts[1]
					usb2used = parts[2]
					usb2free = parts[3]
					usb2summ = 'USB2:\n' + str(usb2tot) + 'B\n' + str(usb2free) + 'B\n' + str(usb2used) + 'B\n' + str(usb2perc)
					usb2perc = usb2perc.replace('%', '')
				if parts[totsp] == '/media/usb3':
					usb3perc = parts[4]
					usb3tot = parts[1]
					usb3used = parts[2]
					usb3free = parts[3]
					usb3summ = 'USB3:\n' + str(usb3tot) + 'B\n' + str(usb3free) + 'B\n' + str(usb3used) + 'B\n' + str(usb3perc)
					usb3perc = usb3perc.replace('%', '')
				if parts[totsp] == '/media/hdd':
					strview = parts[4].replace('%', '')
					if strview.isdigit():
						hddperc = parts[4]
						hddtot = parts[1]
						hddused = parts[2]
						hddfree = parts[3]
						hddsumm = 'HDD:\n' + str(hddtot) + 'B\n' + str(hddfree) + 'B\n' + str(hddused) + 'B\n' + str(hddperc)
						hddperc = hddperc.replace('%', '')
			f.close()
			remove('/tmp/ninfo.tmp')

			self['usb'].setText(usbsumm)
			self['usb1'].setText(usb1summ)
			self['usb2'].setText(usb2summ)
			self['usb3'].setText(usb3summ)
			self['hdd'].setText(hddsumm)
			self['usbbar'].setValue(int(usbperc))
			self['usb1bar'].setValue(int(usb1perc))
			self['usb2bar'].setValue(int(usb2perc))
			self['usb3bar'].setValue(int(usb3perc))
			self['hddbar'].setValue(int(hddperc))

	def getHddtemp(self):
		temperature = 'N/A'
		temperc = 0
		hddloc = ''
		if fileExists('/proc/mounts'):
			f = open('/proc/mounts', 'r')
			for line in f.readlines():
				if line.find('/hdd') != -1:
					hddloc = line
					pos = hddloc.find(' ')
					hddloc = hddloc[0:pos]
					hddloc = hddloc.strip()
			f.close()
		if hddloc:
			cmd = 'hddtemp -w ' + hddloc + ' > /tmp/ninfo.tmp'
			rc = system(cmd)
			if fileExists('/tmp/ninfo.tmp'):
				f = open('/tmp/ninfo.tmp', 'r')
				for line in f.readlines():
					if line.find('WARNING') != -1:
						continue
					parts = line.strip().split(':')
					temperature = parts[2].strip()
					pos = temperature.find(' ')
					temperature = temperature[0:pos]
					if temperature.isdigit():
						temperc = int(temperature)
					else:
						temperature = 'N/A'
				f.close()
			remove('/tmp/ninfo.tmp')
			temperature = str(temperc)

		self['hddtempg'].setRange((0, 80))
		self['hddtempg'].setValue(temperc)
		self['hddtempbar'].setRange((0, 80))
		self['hddtempbar'].setValue(temperc)

	def getHddTempInfo(self):
		temperature = 'HDD Temp:\nN/A'
		temperc = 0
		hddloc = ''
		if fileExists('/proc/mounts'):
			f = open('/proc/mounts', 'r')
			for line in f.readlines():
				if line.find('/hdd') != -1:
					hddloc = line
					pos = hddloc.find(' ')
					hddloc = hddloc[0:pos]
					hddloc = hddloc.strip()
			f.close()
		if hddloc:
			cmd = 'hddtemp -w ' + hddloc + ' > /tmp/ninfo.tmp'
			rc = system(cmd)
			if fileExists('/tmp/ninfo.tmp'):
				f = open('/tmp/ninfo.tmp', 'r')
				for line in f.readlines():
					if line.find('WARNING') != -1:
						continue
					parts = line.strip().split(':')
					temperature = parts[2].strip()
					pos = temperature.find(' ')
					temperature = temperature[0:pos]
					if temperature.isdigit():
						temperc = int(temperature)
					else:
						temperature = 'HDD Temp:\nN/A'
				f.close()
			remove('/tmp/ninfo.tmp')
			temperature = str(temperc)

		self['hddtempbar'].setRange((0, 80))
		self['hddtempbar'].setValue(int(temperc))
		self['hddtemperature'].setText('HDD Temp:\n' + temperature + ' \xc2\xb0C')

	def getDmesg(self):
		dmesg = ''
		system('dmesg > /tmp/tempinfo.tmp')
		if fileExists('/tmp/tempinfo.tmp'):
			f = open('/tmp/tempinfo.tmp', 'r')
			for line in f.readlines():
				txt = line.strip() + '\n'
				dmesg += txt
			f.close()
			remove('/tmp/tempinfo.tmp')
		return dmesg
