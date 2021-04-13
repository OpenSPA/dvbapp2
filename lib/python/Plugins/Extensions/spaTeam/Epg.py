# -*- coding: utf-8 -*-

from . import _
from enigma import eTimer, eEPGCache
from Screens.Screen import Screen
from Screens.Standby import inStandby, TryQuitMainloop
from Screens.MessageBox import MessageBox
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.ConfigList import ConfigListScreen
from Components.config import getConfigListEntry, config, ConfigElement, ConfigYesNo, ConfigSelection, ConfigSubsection, configfile, ConfigSelectionNumber, ConfigNumber, ConfigClock, ConfigText
from Components.ProgressBar import ProgressBar
from Components.Sources.StaticText import StaticText
from Components.ScrollLabel import ScrollLabel
from Components.Harddisk import harddiskmanager
from Tools.Directories import fileExists
from Plugins.Plugin import PluginDescriptor
import gettext
import new
import _enigma
import enigma
import time
from enigma import *
import os

config.epg = ConfigSubsection()
config.epg.eit = ConfigYesNo(default=True)
config.epg.mhw = ConfigYesNo(default=True)
config.epg.mhw.wait = ConfigNumber(default=400)
config.epg.freesat = ConfigYesNo(default=True)
config.epg.viasat = ConfigYesNo(default=True)
config.epg.netmed = ConfigYesNo(default=True)
config.epg.virgin = ConfigYesNo(default=False)
config.epg.restartgui = ConfigYesNo(default=False)

hddchoises = [('/etc/enigma2/', 'Internal Flash')]
for p in harddiskmanager.getMountedPartitions():
	if os.path.exists(p.mountpoint):
		d = os.path.normpath(p.mountpoint)
		if p.mountpoint != '/':
			hddchoises.append((p.mountpoint, d))

config.misc.epgcachepath = ConfigSelection(default='/etc/enigma2/', choices=hddchoises)
config.misc.epgcachefilename = ConfigText(default='epg', fixed_size=False)
config.misc.epgcache_filename = ConfigText(default=(config.misc.epgcachepath.value + config.misc.epgcachefilename.value.replace('.dat', '') + '.dat'))


def EpgSettingsChanged(configElement):
	mask = 0xffffffff
	if not config.epg.eit.value:
		mask &= ~(eEPGCache.NOWNEXT | eEPGCache.SCHEDULE | eEPGCache.SCHEDULE_OTHER)
	if not config.epg.mhw.value:
		mask &= ~eEPGCache.MHW
	if not config.epg.freesat.value:
		mask &= ~(eEPGCache.FREESAT_NOWNEXT | eEPGCache.FREESAT_SCHEDULE | eEPGCache.FREESAT_SCHEDULE_OTHER)
	if not config.epg.viasat.value:
		mask &= ~eEPGCache.VIASAT
	if not config.epg.netmed.value:
		mask &= ~(eEPGCache.NETMED_SCHEDULE | eEPGCache.NETMED_SCHEDULE_OTHER)
	if not config.epg.virgin.value:
		mask &= ~(eEPGCache.VIRGIN_NOWNEXT | eEPGCache.VIRGIN_SCHEDULE)
	eEPGCache.getInstance().setEpgSources(mask)


config.epg.eit.addNotifier(EpgSettingsChanged)
config.epg.mhw.addNotifier(EpgSettingsChanged)
config.epg.freesat.addNotifier(EpgSettingsChanged)
config.epg.viasat.addNotifier(EpgSettingsChanged)
config.epg.netmed.addNotifier(EpgSettingsChanged)
config.epg.virgin.addNotifier(EpgSettingsChanged)

config.epg.maxdays = ConfigSelectionNumber(min=1, max=30, stepwidth=1, default=3, wraparound=True)


def EpgmaxdaysChanged(configElement):
	eEPGCache.getInstance().setEpgmaxdays(config.epg.maxdays.getValue())


config.epg.maxdays.addNotifier(EpgmaxdaysChanged)

config.epg.histminutes = ConfigSelectionNumber(min=0, max=120, stepwidth=15, default=0, wraparound=True)


def EpgHistorySecondsChanged(configElement):
	eEPGCache.getInstance().setEpgHistorySeconds(config.epg.histminutes.getValue() * 60)


config.epg.histminutes.addNotifier(EpgHistorySecondsChanged)


def mountp():
	pathmp = []
	if fileExists('/proc/mounts'):
		for line in open('/proc/mounts'):
			if line.find('/dev/sd') > -1:
				pathmp.append(line.split()[1].replace('\\040', ' ') + '/')

	pathmp.append('/usr/share/enigma2/')
	return pathmp


def _(txt):
	t = gettext.dgettext('messages', txt)
	if t == txt:
		t = gettext.gettext(txt)
	return t


class Ttimer(Screen):
	skin = """<screen name="Ttimer" position="center,center" zPosition="10" size="1280,720" title="Update EPG" backgroundColor="#ff000000" flags="wfNoBorder">
					<ePixmap name="background" position="40,40" size="410,130" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/spaTeam/icons/background.png" zPosition="-1" alphatest="off" />
					<widget name="srclabel" halign="left" valign="center" position="49,46" size="289,30" font="Regular;17" foregroundColor="#dfdfdf" transparent="1" backgroundColor="#000000" borderColor="black" borderWidth="1" noWrap="1"/>
					<widget name="srcwait" valign="center" halign="center" position="60,82" size="360,20" font="Regular;15" foregroundColor="#dfdfdf" transparent="1" backgroundColor="#000000" borderColor="black" borderWidth="1" noWrap="1"/>
					<widget name="progress" position="60,105" size="360,8" borderWidth="1" borderColor="#1143495b" backgroundColor="#1143495b" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/spaTeam/icons/progreso.png" zPosition="2" alphatest="blend" />
			</screen>"""

	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		self.setTitle(_('Update EPG'))
		self.skin = Ttimer.skin
		self.iprogress = 0
		self['srclabel'] = Label(_('Please wait, Updating Epg'))
		self['progress'] = ProgressBar()
		self['srcwait'] = Label('')

		self.ctimer = enigma.eTimer()
		self.ctimer.callback.append(self.__run)
		self.ctimer.start(1000, 0)

	def __run(self):
		barlen = 100
		self.iprogress += 1
		count = (barlen * self.iprogress) // config.epg.mhw.wait.value
		time.sleep(0.5)
		self['progress'].setValue(count)
		if count >= 100:
			self['srcwait'].setText('100 %')
		else:
			self['srcwait'].setText(str(count) + ' %')
		if count > 100:
			count = 100
			self.ctimer.stop()
			self.session.nav.playService(eServiceReference(config.tv.lastservice.value))
			rDialog.stopDialog(self.session)
			epgcache = new.instancemethod(_enigma.eEPGCache_load, None, eEPGCache)
			epgcache = eEPGCache.getInstance().save()
			if inStandby:
				self.session.nav.stopService()
			else:
				if config.epg.restartgui.value:
					self.session.openWithCallback(self.restartCB, MessageBox, _("Need restart GUI to apply changes\n Restart now?"), MessageBox.TYPE_YESNO, timeout=15)
			self.close()
		return

	def restartCB(self, retval):
		if retval:
			self.TimerTemp = eTimer()
			self.TimerTemp.callback.append(self.session.open(TryQuitMainloop, 3))
			self.TimerTemp.startLongTimer(2)


pdialog = ''


class runDialog:

	def __init__(self):
		self.dialog = None
		return

	def startDialog(self, session):
		global pdialog
		pdialog = session.instantiateDialog(Ttimer)
		pdialog.show()

	def stopDialog(self, session):
		pdialog.hide()


rDialog = runDialog()


class EPGScreen(Screen, ConfigListScreen):
	skin = """
			<screen name="EPGScreen" position="center,center" size="710,500">
				<widget position="15,50" size="680,400" name="config" scrollbarMode="showOnDemand" />
				<eLabel backgroundColor="red" position="15,490" size="165,3" zPosition="0" />
				<eLabel backgroundColor="green" position="185,490" size="165,3" zPosition="0" />
				<eLabel backgroundColor="yellow" position="355,490" size="165,3" zPosition="0" />
				<eLabel backgroundColor="blue" position="525,490" size="165,3" zPosition="0" />
				<widget source="key_red" render="Label" position="15,460" zPosition="2" size="165,30" font="Regular;20" halign="center" valign="center" backgroundColor="background" foregroundColor="foreground" transparent="1" />
				<widget source="key_green" render="Label" position="185,460" zPosition="2" size="165,30" font="Regular;20" halign="center" valign="center" backgroundColor="background" foregroundColor="foreground" transparent="1" />
				<widget source="key_yellow" render="Label" position="355,460" zPosition="2" size="165,30" font="Regular;20" halign="center" valign="center" backgroundColor="background" foregroundColor="foreground" transparent="1" />
				<widget source="key_blue" render="Label" position="525,460" zPosition="2" size="165,30" font="Regular;20" halign="center" valign="center" backgroundColor="background" foregroundColor="foreground" transparent="1" />
			</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.setTitle(_('EPG Settings'))

		self.list = []
		ConfigListScreen.__init__(self, self.list)

		self['key_blue'] = StaticText(_('Show log'))
		self['key_red'] = StaticText(_('Close'))
		self['key_green'] = StaticText(_('Save'))
		self['key_yellow'] = StaticText(_('Update'))

		self['setupActions'] = ActionMap(['SetupActions', 'ColorActions'],
		{
			'blue': self.log,
			'red': self.cancel,
			'cancel': self.cancel,
			'yellow': self.downepg,
			'green': self.save,
			'ok': self.save
		}, -2)

		self.list.append(getConfigListEntry(_('EPG location'), config.misc.epgcachepath))
		self.list.append(getConfigListEntry(_("EPG file name"), config.misc.epgcachefilename))
		self.list.append(getConfigListEntry(_('Show EIT now/next in infobar'), config.usage.show_eit_nownext))
		self.list.append(getConfigListEntry(_('Enable EIT EPG'), config.epg.eit))
		self.list.append(getConfigListEntry(_('Enable MHW EPG'), config.epg.mhw))
		self.list.append(getConfigListEntry(_('Enable freesat EPG'), config.epg.freesat))
		self.list.append(getConfigListEntry(_('Enable ViaSat EPG'), config.epg.viasat))
		self.list.append(getConfigListEntry(_('Enable Netmed EPG'), config.epg.netmed))
		self.list.append(getConfigListEntry(_('Enable Virgin EPG'), config.epg.virgin))
		self.list.append(getConfigListEntry(_('Maximum number of days in EPG'), config.epg.maxdays))
		self.list.append(getConfigListEntry(_('Maintain old EPG data for'), config.epg.histminutes))
		self.list.append(getConfigListEntry(_('Restart GUI after download EPG?'), config.epg.restartgui))
		self.list.append(getConfigListEntry(_('Include EIT in http streams'), config.streaming.stream_eit))
		self.list.append(getConfigListEntry(_('Include AIT in http streams'), config.streaming.stream_ait))
		self.list.append(getConfigListEntry(_('Country for EPG event rating information'), config.misc.epgratingcountry))
		self.list.append(getConfigListEntry(_('Country for EPG event genre information'), config.misc.epggenrecountry))
		self.list.append(getConfigListEntry(_('Time to wait in the channel for EPG download (secs)'), config.epg.mhw.wait))

		self['config'].list = self.list
		self['config'].l.setList(self.list)

	def zapTo(self, reftozap):
		self.session.nav.playService(eServiceReference(reftozap))

	def downepg(self):
		recordings = self.session.nav.getRecordings()
		rec_time = self.session.nav.RecordTimer.getNextRecordingTime()
		mytime = time.time()
		try:
			if not recordings or rec_time > 0 and rec_time - mytime() < 360:
				channel = '1:0:1:75C6:422:1:C00000:0:0:0:'
				self.zapTo(channel)
				diag = runDialog()
				diag.startDialog(self.session)
			else:
				self.mbox = self.session.open(MessageBox, _('EPG Download Cancelled - Recording active'), MessageBox.TYPE_ERROR, timeout=5)
		except:
			print 'Error download EPG, record active?'

	def log(self):
		self.session.open(ViewLog)

	def cancel(self):
		for i in self['config'].list:
			i[1].cancel()

		self.close(False)

	def save(self):
		config.misc.epgcache_filename.save()
		config.misc.epgcachefilename.save()
		config.misc.epgcachepath.save()
		epgcache = new.instancemethod(_enigma.eEPGCache_save, None, eEPGCache)
		epgcache = eEPGCache.getInstance().save()
		config.epg.mhw.wait.save()
		config.epg.restartgui.save()
		config.epg.save()
		config.epg.maxdays.save()
		configfile.save()
		self.mbox = self.session.open(MessageBox, _('configuration is saved'), MessageBox.TYPE_INFO, timeout=4)

	def restart(self):
		self.session.open(TryQuitMainloop, 3)


class ViewLog(Screen):
	skin = """
			<screen name="ViewLog" position="center,80" size="1170,600" title="View Log File">
				<eLabel backgroundColor="red" position="20,590" size="170,3" zPosition="0" />
				<widget source="key_red" render="Label" position="20,560" zPosition="2" size="170,30" font="Regular;20" halign="center" valign="center" backgroundColor="background" foregroundColor="foreground" transparent="1" />
				<widget name="text" position="20,10" size="1130,542" font="Console;22" />
			</screen>"""

	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		self.setTitle(_('View Log File'))

		self['shortcuts'] = ActionMap(['ShortcutActions', 'WizardActions'],
		{
			'ok': self.exit,
			'cancel': self.exit,
			'back': self.exit,
			'red': self.exit,
		})

		self['key_red'] = StaticText(_('Close'))
		self['text'] = ScrollLabel('')
		self.viewlog()

	def exit(self):
		self.close()

	def viewlog(self):
		list = ''
		if fileExists('/etc/mhw_Log.epg'):
			for line in open('/etc/mhw_Log.epg'):
				list += line

		self['text'].setText(list)

		self['actions'] = ActionMap(['OkCancelActions', 'DirectionActions'],
		{
			'cancel': self.close,
			'up': self['text'].pageUp,
			'left': self['text'].pageUp,
			'down': self['text'].pageDown,
			'right': self['text'].pageDown
		}, -1)
