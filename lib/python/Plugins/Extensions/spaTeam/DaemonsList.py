# -*- coding: utf-8 -*-

from . import _
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Tools.Directories import fileExists, crawlDirectory
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest
from Components.Button import Button
from Plugins.Extensions.spaTeam.ExtrasList import ExtrasList
from Plugins.Extensions.spaTeam.ExtraActionBox import ExtraActionBox
from Components.Ipkg import IpkgComponent
from Screens.Ipkg import Ipkg
from Screens.MessageBox import MessageBox
from time import sleep
from enigma import *
import os
import sys


def DaemonEntry(name, picture, description, started, installed):
	res = [(name,
		picture,
		description,
		started)]

	picture = picture[8:]
	picture = '/usr/lib/enigma2/python/Plugins/Extensions/spaTeam/icons/' + picture

	if started:
		picture2 = '/usr/share/enigma2/skin_default/icons/lock_on.png'
	else:
		picture2 = '/usr/share/enigma2/skin_default/icons/lock_off.png'
	if not installed:
		picture2 = '/usr/share/enigma2/skin_default/icons/lock_error.png'
	if fileExists(picture):
		res.append(MultiContentEntryPixmapAlphaTest(pos=(5, 0), size=(48, 48), png=loadPNG(picture)))
	res.append(MultiContentEntryText(pos=(65, 10), size=(135, 38), font=0, text=name))
	res.append(MultiContentEntryText(pos=(210, 10), size=(280, 38), font=0, text=description))

	if fileExists(picture2):
		res.append(MultiContentEntryPixmapAlphaTest(pos=(500, 10), size=(24, 24), png=loadPNG(picture2)))

	return res


class DaemonsList(Screen):
	skin = """
		<screen name="DaemonsList" position="360,160" size="560,400" title="Services List">
			<widget name="menu" position="0,10" scrollbarMode="showOnDemand" size="560,340"/>
			<eLabel name="bar_red" position="0,390" size="140,3" zPosition="1" backgroundColor="red" />
			<eLabel name="bar_green" position="140,390" size="140,3" zPosition="1" backgroundColor="green" />
			<eLabel name="bar_yellow" position="280,390" size="140,3" zPosition="1" backgroundColor="yellow" />
			<eLabel name="bar_blue" position="420,390" size="140,3" zPosition="1" backgroundColor="blue" />
			<widget name="key_red" position="0,360" zPosition="2" size="140,26" valign="center" halign="center" font="Regular;22" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_green" position="140,360" zPosition="2" size="140,26" valign="center" halign="center" font="Regular;22" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_yellow" position="280,360" zPosition="2" size="140,26" valign="center" halign="center" font="Regular;22" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_blue" position="420,360" zPosition="2" size="140,26" valign="center" halign="center" font="Regular;22" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
		</screen> """

	def __init__(self, session, args=0):
		Screen.__init__(self, session)
		self.running = list()
		self.installed = list()
		self.daemons = list()

		self['menu'] = ExtrasList(list())
		self['menu'].onSelectionChanged.append(self.selectionChanged)
		self['key_green'] = Button('')
		self['key_red'] = Button('')
		self['key_blue'] = Button(_('Exit'))
		self['key_yellow'] = Button('')

		self['actions'] = ActionMap(['OkCancelActions', 'ColorActions'],
			{
				'blue': self.quit,
				'yellow': self.yellow,
				'red': self.red,
				'green': self.green,
				'cancel': self.quit
			}, -2)

		self.onFirstExecBegin.append(self.drawList)
		self.onShown.append(self.setWindowTitle)

	def setWindowTitle(self):
		self.setTitle(_('Services List'))

	def selectionChanged(self):
		if len(self.daemons) > 0:
			index = self['menu'].getSelectionIndex()
			if self.installed[index]:
				if self.running[index]:
					self['key_red'].setText(_('Stop'))
				else:
					self['key_red'].setText(_('Start'))
				if self.daemons[index][6]:
					self['key_yellow'].setText(_('Configure'))
				else:
					self['key_yellow'].setText('')
				self['key_green'].setText('')
			else:
				self['key_red'].setText('')
				self['key_yellow'].setText('')
				if self.daemons[index][9]:
					self['key_green'].setText(_('Install'))
				else:
					self['key_green'].setText('')

	def drawList(self, ret=None):
		self.session.open(ExtraActionBox, _('Checking services status...'), _('Services'), self.actionDrawList)

	def actionDrawList(self):
		self.ishowed = True
		if len(self.daemons) == 0:
			self.loadList()
		self.checkInstalled()
		self.checkRunning()
		list = []
		i = 0
		for daemon in self.daemons:
			list.append(DaemonEntry(daemon[0], 'Daemons/%s' % daemon[2], daemon[1], self.running[i], self.installed[i]))
			i += 1

		self['menu'].setList(list)

	def checkRunning(self):
		self.running = list()
		for daemon in self.daemons:
			self.running.append(daemon[3]())

	def checkInstalled(self):
		self.installed = list()
		for daemon in self.daemons:
			self.installed.append(daemon[7]())

	def loadList(self):
		self.daemons = list()
		tdaemons = crawlDirectory('%s/Daemons/' % os.path.dirname(sys.modules[__name__].__file__), '.*\\.ext$')
		tdaemons.sort()
		for daemon in tdaemons:
			if daemon[1][:1] != '.':
				try:
					src = open(os.path.join(daemon[0], daemon[1]))
					exec src.read()
					src.close()
					self.daemons.append((daemon_name,
						daemon_description,
						daemon_icon,
						daemon_fnc_status,
						daemon_fnc_start,
						daemon_fnc_stop,
						daemon_class_config,
						daemon_fnc_installed,
						daemon_fnc_boot,
						daemon_package))
				except TypeError:
					print '[spaTeam] Could not parse servicelist while Directory crawl. Please check .ext Files for errors.'

	def yellow(self):
		index = self['menu'].getSelectionIndex()
		try:
			if self.installed[index]:
				if self.daemons[index][6]:
					if self.daemons[index][6] == 'NFSServerSetup' and fileExists('/usr/lib/enigma2/python/Plugins/PLi/NFSServer/plugin.pyo'):
						from Plugins.PLi.NFSServer.plugin import NFSServerSetup
						self.session.open(NFSServerSetup)
					elif self.daemons[index][6] == 'NFSServerSetup':
						try:
							from Screens.NetworkSetup import NetworkNfs
							self.session.open(NetworkNfs)
						except:
							self.session.open(MessageBox, _('This feature not is available.'), MessageBox.TYPE_INFO)
					elif self.daemons[index][6] == 'Openvpn':
						try:
							from Screens.NetworkSetup import NetworkOpenvpn
							self.session.open(NetworkOpenvpn)
						except:
							self.session.open(MessageBox, _('This feature not is available.'), MessageBox.TYPE_INFO)
					elif self.daemons[index][6] == 'Samba':
						try:
							from Screens.NetworkSetup import NetworkSamba
							self.session.open(NetworkSamba)
						except:
							self.session.open(MessageBox, _('This feature not is available.'), MessageBox.TYPE_INFO)
					elif self.daemons[index][6] == 'CronMang':
						try:
							from Screens.CronTimer import CronTimers
							self.session.open(CronTimers)
						except:
							self.session.open(MessageBox, _('This feature not is available.'), MessageBox.TYPE_INFO)
					elif self.daemons[index][6] == 'Telnet':
						try:
							from Screens.NetworkSetup import NetworkTelnet
							self.session.open(NetworkTelnet)
						except:
							self.session.open(MessageBox, _('This feature not is available.'), MessageBox.TYPE_INFO)
					elif self.daemons[index][6] == 'FTP':
						try:
							from Screens.NetworkSetup import NetworkFtp
							self.session.open(NetworkFtp)
						except:
							self.session.open(MessageBox, _('This feature not is available.'), MessageBox.TYPE_INFO)
					elif self.daemons[index][6] == 'NTPdConf':
						self.session.open(MessageBox, _('Please visit the following Website:\nhttp://linux-fuer-alle.de/doc_show.php?docid=7\nto gain further instructions how to configure your STB as NTP-Client/Server.'), MessageBox.TYPE_INFO)
		except IndexError:
			print '[spaTeam] no Service .ext files found.'

	def green(self):
		index = self['menu'].getSelectionIndex()
		if not self.installed[index]:
			if self.daemons[index][9]:
				filename = self.daemons[index][9]
				self.oktext = _('\nAfter pressing OK, please wait!')
				self.cmdList = []
				if not fileExists('/var/lib/opkg/lists/openspa-all') and not fileExists('/var/lib/opkg/lists/openspa-mipsel') and not fileExists('/var/lib/opkg/lists/openspa-3rd-party'):
					self.ipkg = IpkgComponent()
					self.ipkg.startCmd(IpkgComponent.CMD_UPDATE)
					sleep(5)
				self.cmdList.append((IpkgComponent.CMD_INSTALL, {'package': filename}))
				if len(self.cmdList):
					self.session.openWithCallback(self.runUpgrade, MessageBox, _('Do you want to install the package:\n') + filename + '\n' + self.oktext)

	def red(self):
		if len(self.daemons) > 0:
			index = self['menu'].getSelectionIndex()
			if self.running[index]:
				self.session.openWithCallback(self.drawList, ExtraActionBox, _('Stopping %s...') % self.daemons[index][0], _('Services'), self.startstop)
			else:
				self.session.openWithCallback(self.drawList, ExtraActionBox, _('Starting %s...') % self.daemons[index][0], _('Services'), self.startstop)

	def startstop(self):
		if len(self.daemons) > 0:
			index = self['menu'].getSelectionIndex()
			if self.installed[index]:
				if self.running[index]:
					self.daemons[index][5]()
				else:
					self.daemons[index][4]()
				self.daemons[index][8](self.daemons[index][3]())

	def quit(self):
		self.close()

	def runUpgrade(self, result):
		if result:
			self.session.openWithCallback(self.runUpgradeFinished, Ipkg, cmdList=self.cmdList)

	def runUpgradeFinished(self):
		self.session.openWithCallback(self.UpgradeReboot, MessageBox, _('Installation/Upgrade finished.') + ' ' + _('Do you want to restart Enigma2?'), MessageBox.TYPE_YESNO)

	def UpgradeReboot(self, result):
		if result is None or result is False:
			self.session.open(ExtraActionBox, _('Checking services status...'), _('Services'), self.actionDrawList)
		if result:
			quitMainloop(3)
