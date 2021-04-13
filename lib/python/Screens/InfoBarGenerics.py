# -*- coding: utf-8 -*-
from Components.ActionMap import ActionMap, HelpableActionMap, NumberActionMap
from Components.Harddisk import harddiskmanager, findMountPoint
from Components.Input import Input
from Components.Label import Label
from Components.MovieList import AUDIO_EXTENSIONS, MOVIE_EXTENSIONS, DVD_EXTENSIONS
from Components.PluginComponent import plugins
from Components.ServiceEventTracker import ServiceEventTracker
from Components.Sources.ServiceEvent import ServiceEvent
from Components.Sources.Boolean import Boolean
from Components.Sources.List import List
from Components.config import config, configfile, ConfigBoolean, ConfigClock, ConfigText
from Components.SystemInfo import SystemInfo
from Components.UsageConfig import preferredInstantRecordPath, defaultMoviePath, preferredTimerPath, ConfigSelection
from Components.VolumeControl import VolumeControl
from Components.Pixmap import MovingPixmap, MultiPixmap
from Components.Sources.StaticText import StaticText
from Components.ScrollLabel import ScrollLabel
from Plugins.Plugin import PluginDescriptor

from Components.Timeshift import InfoBarTimeshift

from Screens.Screen import Screen
from Screens import ScreenSaver
from Screens.ChannelSelection import ChannelSelection, PiPZapSelection, BouquetSelector, SilentBouquetSelector, service_types_tv
from Screens.ChoiceBox import ChoiceBox
from Screens.Dish import Dish
from Screens.EventView import EventViewEPGSelect, EventViewSimple
from Screens.EpgSelection import EPGSelection
from Screens.InputBox import InputBox
from Screens.MessageBox import MessageBox
from Screens.MinuteInput import MinuteInput
from Screens.TimerSelection import TimerSelection
from Screens.PictureInPicture import PictureInPicture
from Screens.PVRState import PVRState, TimeshiftState
from Screens.SubtitleDisplay import SubtitleDisplay
from Screens.RdsDisplay import RdsInfoDisplay, RassInteractive
from Screens.Standby import Standby, TryQuitMainloop
from Screens.TimeDateInput import TimeDateInput
from Screens.TimerEdit import TimerEditList
from Screens.UnhandledKey import UnhandledKey
from ServiceReference import ServiceReference, isPlayableForCur
from RecordTimer import RecordTimer, RecordTimerEntry, parseEvent, AFTEREVENT, findSafeRecordPath
from Screens.TimerEntry import TimerEntry as TimerEntry

from Tools import Directories, Notifications
from Tools.Directories import pathExists, fileExists, getRecordingFilename, copyfile, moveFiles, resolveFilename, SCOPE_TIMESHIFT, SCOPE_CURRENT_SKIN
from Tools.KeyBindings import getKeyDescription
from Tools.ServiceReference import hdmiInServiceRef
from enigma import eTimer, eServiceCenter, eDVBServicePMTHandler, iServiceInformation, iPlayableService, eServiceReference, eEPGCache, eActionMap, eDVBVolumecontrol, getDesktop, quitMainloop, eDVBDB
from boxbranding import getBoxType, getMachineProcModel, getMachineBuild, getMachineBrand, getMachineName

from time import time, localtime, strftime
from bisect import insort
from keyids import KEYIDS
from datetime import datetime
import itertools
import datetime
from sys import maxint

import os
import cPickle

# hack alert!
from Screens.Menu import MainMenu, Menu, mdom
from Screens.Setup import Setup
import Screens.Standby

AUDIO = False
seek_withjumps_muted = False
jump_pts_adder = 0
jump_last_pts = None
jump_last_pos = None


def isStandardInfoBar(self):
	return self.__class__.__name__ == "InfoBar"

def isMoviePlayerInfoBar(self):
	return self.__class__.__name__ == "MoviePlayer"

def setResumePoint(session):
	global resumePointCache, resumePointCacheLast
	service = session.nav.getCurrentService()
	ref = session.nav.getCurrentlyPlayingServiceOrGroup()
	if (service is not None) and (ref is not None): # and (ref.type != 1):
		# ref type 1 has its own memory...
		seek = service.seek()
		if seek:
			pos = seek.getPlayPosition()
			if not pos[0]:
				key = ref.toString()
				lru = int(time())
				l = seek.getLength()
				if l:
					l = l[1]
				else:
					l = None
				resumePointCache[key] = [lru, pos[1], l]
				for k, v in resumePointCache.items():
					if v[0] < lru:
						candidate = k
						filepath = os.path.realpath(candidate.split(':')[-1])
						mountpoint = findMountPoint(filepath)
						if os.path.ismount(mountpoint) and not os.path.exists(filepath):
							del resumePointCache[candidate]
				saveResumePoints()

def delResumePoint(ref):
	global resumePointCache, resumePointCacheLast
	try:
		del resumePointCache[ref.toString()]
	except KeyError:
		pass
	saveResumePoints()

def getResumePoint(session):
	global resumePointCache
	ref = session.nav.getCurrentlyPlayingServiceOrGroup()
	if (ref is not None) and (ref.type != 1):
		try:
			entry = resumePointCache[ref.toString()]
			entry[0] = int(time()) # update LRU timestamp
			return entry[1]
		except KeyError:
			return None

def saveResumePoints():
	global resumePointCache, resumePointCacheLast
	try:
		f = open('/etc/enigma2/resumepoints.pkl', 'wb')
		cPickle.dump(resumePointCache, f, cPickle.HIGHEST_PROTOCOL)
		f.close()
	except Exception, ex:
		print "[InfoBar] Failed to write resumepoints:", ex
	resumePointCacheLast = int(time())

def loadResumePoints():
	try:
		file = open('/etc/enigma2/resumepoints.pkl', 'rb')
		PickleFile = cPickle.load(file)
		file.close()
		return PickleFile
	except Exception, ex:
		print "[InfoBar] Failed to load resumepoints:", ex
		return {}

def updateresumePointCache():
	global resumePointCache
	resumePointCache = loadResumePoints()

def ToggleVideo():
	mode = open("/proc/stb/video/policy").read()[:-1]
	print mode
	if mode == "letterbox":
		f = open("/proc/stb/video/policy", "w")
		f.write("panscan")
		f.close()
	elif mode == "panscan":
		f = open("/proc/stb/video/policy", "w")
		f.write("letterbox")
		f.close()
	else:
		# if current policy is not panscan or letterbox, set to panscan
		f = open("/proc/stb/video/policy", "w")
		f.write("panscan")
		f.close()
resumePointCache = loadResumePoints()
resumePointCacheLast = int(time())

subservice_groupslist = None
def reload_subservice_groupslist(force=False):
	global subservice_groupslist
	if subservice_groupslist is None or force:
		try:
			groupedservices = "/etc/enigma2/groupedservices"
			if not os.path.isfile(groupedservices):
				groupedservices = "/usr/share/enigma2/groupedservices"
			subservice_groupslist = [list(g) for k,g in itertools.groupby([line.split('#')[0].strip() for line in open(groupedservices).readlines()], lambda x:not x) if not k]
		except:
			subservice_groupslist = []
reload_subservice_groupslist()

def getPossibleSubservicesForCurrentChannel(current_service):
	if current_service and subservice_groupslist:
		ref_in_subservices_group = [x for x in subservice_groupslist if current_service in x]
		if ref_in_subservices_group:
			return ref_in_subservices_group[0]
	return []

def getActiveSubservicesForCurrentChannel(current_service):
	if current_service:
		possibleSubservices = getPossibleSubservicesForCurrentChannel(current_service)
		activeSubservices = []
		epgCache = eEPGCache.getInstance()
		idx = 0
		for subservice in possibleSubservices:
			events = epgCache.lookupEvent(['BDTS', (subservice, 0, -1)])
			if events and len(events) == 1:
				event = events[0]
				title = event[2]
				if title and "Sendepause" not in title:
					starttime = datetime.datetime.fromtimestamp(event[0]).strftime('%H:%M')
					endtime = datetime.datetime.fromtimestamp(event[0] + event[1]).strftime('%H:%M')
					current_show_name = title + " " + str(starttime) + "-" + str(endtime)
					activeSubservices.append((current_show_name, subservice))
		return activeSubservices

def hasActiveSubservicesForCurrentChannel(current_service):
	activeSubservices = getActiveSubservicesForCurrentChannel(current_service)
	return bool(activeSubservices and len(activeSubservices) > 1)

class InfoBarDish:
	def __init__(self):
		self.dishDialog = self.session.instantiateDialog(Dish)
		self.dishDialog.setAnimationMode(0)

class InfoBarLongKeyDetection:
	def __init__(self):
		eActionMap.getInstance().bindAction('', -maxint -1, self.detection) #highest prio
		self.LongButtonPressed = False

	#this function is called on every keypress!
	def detection(self, key, flag):
		if flag == 3:
			self.LongButtonPressed = True
		elif flag == 0:
			self.LongButtonPressed = False

class InfoBarUnhandledKey:
	def __init__(self):
		self.unhandledKeyDialog = self.session.instantiateDialog(UnhandledKey)
		self.unhandledKeyDialog.setAnimationMode(0)
		self.hideUnhandledKeySymbolTimer = eTimer()
		self.hideUnhandledKeySymbolTimer.callback.append(self.unhandledKeyDialog.hide)
		self.checkUnusedTimer = eTimer()
		self.checkUnusedTimer.callback.append(self.checkUnused)
		self.onLayoutFinish.append(self.unhandledKeyDialog.hide)
		eActionMap.getInstance().bindAction('', -maxint -1, self.actionA) #highest prio
		eActionMap.getInstance().bindAction('', maxint, self.actionB) #lowest prio
		self.flags = (1<<1)
		self.uflags = 0

	#this function is called on every keypress!
	def actionA(self, key, flag):
		try:
			print 'KEY: %s %s %s %s' % (key,flag,(key_name for key_name,value in KEYIDS.items() if value==key).next(),getKeyDescription(key)[0])
		except:
			try:
				print 'KEY: %s %s %s' % (key,flag,(key_name for key_name,value in KEYIDS.items() if value==key).next()) # inverse dictionary lookup in KEYIDS
			except:
				print 'KEY: %s %s' % (key,flag)
		self.unhandledKeyDialog.hide()
		if flag != 4:
			if self.flags & (1<<1):
				self.flags = self.uflags = 0
			self.flags |= (1<<flag)
			if flag == 1: # break
				self.checkUnusedTimer.start(0, True)
		return 0

	#this function is only called when no other action has handled this key
	def actionB(self, key, flag):
		if flag != 4:
			self.uflags |= (1<<flag)

	def checkUnused(self):
		if self.flags == self.uflags:
			self.unhandledKeyDialog.show()
			self.hideUnhandledKeySymbolTimer.start(2000, True)

class InfoBarScreenSaver:
	def __init__(self):
		self.onExecBegin.append(self.__onExecBegin)
		self.onExecEnd.append(self.__onExecEnd)
		self.screenSaverTimer = eTimer()
		self.screenSaverTimer.callback.append(self.screensaverTimeout)
		self.screensaver = self.session.instantiateDialog(ScreenSaver.Screensaver)
		self.onLayoutFinish.append(self.__layoutFinished)

	def __layoutFinished(self):
		self.screensaver.hide()

	def __onExecBegin(self):
		self.ScreenSaverTimerStart()

	def __onExecEnd(self):
		if self.screensaver.shown:
			self.screensaver.hide()
			eActionMap.getInstance().unbindAction('', self.keypressScreenSaver)
		self.screenSaverTimer.stop()

	def ScreenSaverTimerStart(self):
		time = int(config.usage.screen_saver.value)
		flag = self.seekstate[0]
		if not flag:
			ref = self.session.nav.getCurrentlyPlayingServiceOrGroup()
			if ref and not (hasattr(self.session, "pipshown") and self.session.pipshown):
				ref = ref.toString().split(":")
				flag = ref[2] == "2" or os.path.splitext(ref[10])[1].lower() in AUDIO_EXTENSIONS
		if time and flag:
			self.screenSaverTimer.startLongTimer(time)
		else:
			self.screenSaverTimer.stop()

	def screensaverTimeout(self):
		if self.execing and not Screens.Standby.inStandby and not Screens.Standby.inTryQuitMainloop:
			self.hide()
			if hasattr(self, "pvrStateDialog"):
				try:
					self.pvrStateDialog.hide()
				except:
					pass
			self.screensaver.show()
			eActionMap.getInstance().bindAction('', -maxint - 1, self.keypressScreenSaver)

	def keypressScreenSaver(self, key, flag):
		if flag:
			self.screensaver.hide()
			self.show()
			self.ScreenSaverTimerStart()
			eActionMap.getInstance().unbindAction('', self.keypressScreenSaver)

class HideVBILine(Screen):
	skin = """<screen position="0,0" size="%s,%s" backgroundColor="#000000" flags="wfNoBorder"/>""" % (getDesktop(0).size().width(), getDesktop(0).size().height() / 360)
	def __init__(self, session):
		Screen.__init__(self, session)

class SecondInfoBar(Screen):

	def __init__(self, session):
		Screen.__init__(self, session)
		self.skin = None

class InfoBarShowHide(InfoBarScreenSaver):
	""" InfoBar show/hide control, accepts toggleShow and hide actions, might start
	fancy animations. """
	STATE_HIDDEN = 0
	STATE_HIDING = 1
	STATE_SHOWING = 2
	STATE_SHOWN = 3
	FLAG_CENTER_DVB_SUBS = 2048
	skipToggleShow = False

	def __init__(self):
		self["ShowHideActions"] = ActionMap( ["InfobarShowHideActions"] ,
			{
				"toggleShow": self.okButtonCheck,
				"hide": self.keyHide,
			}, 1) # lower prio to make it possible to override ok and cancel..

		self.__event_tracker = ServiceEventTracker(screen=self, eventmap={
				iPlayableService.evStart: self.serviceStarted,
			})

		InfoBarScreenSaver.__init__(self)
		self.__state = self.STATE_SHOWN
		self.__locked = 0

		self.DimmingTimer = eTimer()
		self.DimmingTimer.callback.append(self.doDimming)
		self.hideTimer = eTimer()
		self.hideTimer.callback.append(self.doTimerHide)
		self.hideTimer.start(5000, True)

		self.onShow.append(self.__onShow)
		self.onHide.append(self.__onHide)

		self.hideVBILineScreen = self.session.instantiateDialog(HideVBILine)
		self.hideVBILineScreen.show()

		self.onShowHideNotifiers = []

		self.standardInfoBar = False
		self.lastResetAlpha = True

		self.secondInfoBarScreen = ""
		if isStandardInfoBar(self):
			self.secondInfoBarScreen = self.session.instantiateDialog(SecondInfoBar)
			self.secondInfoBarScreen.show()

		self.onLayoutFinish.append(self.__layoutFinished)
		self.onExecBegin.append(self.__onExecBegin)

	def __onExecBegin(self):
		self.showHideVBI()

	def __layoutFinished(self):
		if self.secondInfoBarScreen:
			self.secondInfoBarScreen.hide()
			self.standardInfoBar = True
		self.hideVBILineScreen.hide()
		try:
			if self.pvrStateDialog:
				pass
		except:
			self.pvrStateDialog = None

	def __onShow(self):
		self.__state = self.STATE_SHOWN
		for x in self.onShowHideNotifiers:
			x(True)
		self.startHideTimer()
		VolumeControl.instance and VolumeControl.instance.showMute()

	def doDimming(self):
		if config.usage.show_infobar_do_dimming.value:
			self.dimmed = self.dimmed-1
		else:
			self.dimmed = 0
		self.DimmingTimer.stop()
		self.doHide()

	def unDimming(self):
		self.unDimmingTimer.stop()
		self.doWriteAlpha(config.av.osd_alpha.value)

	def doWriteAlpha(self, value):
		if fileExists("/proc/stb/video/alpha"):
			f=open("/proc/stb/video/alpha","w")
			f.write("%i" % (value))
			f.close()
			if value == config.av.osd_alpha.value:
				self.lastResetAlpha = True
			else:
				self.lastResetAlpha = False

	def __onHide(self):
		self.__state = self.STATE_HIDDEN
		if self.secondInfoBarScreen:
			self.secondInfoBarScreen.hide()
		self.resetAlpha()
		for x in self.onShowHideNotifiers:
			x(False)

	def resetAlpha(self):
		if config.usage.show_infobar_do_dimming.value and self.lastResetAlpha is False:
			self.unDimmingTimer = eTimer()
			self.unDimmingTimer.callback.append(self.unDimming)
			self.unDimmingTimer.start(300, True)

	def keyHide(self):
		if self.__state == self.STATE_HIDDEN and self.session.pipshown and "popup" in config.usage.pip_hideOnExit.value:
			if config.usage.pip_hideOnExit.value == "popup":
				self.session.openWithCallback(self.hidePipOnExitCallback, MessageBox, _("Disable Picture in Picture"), simple=True)
			else:
				self.hidePipOnExitCallback(True)
		elif config.usage.ok_is_channelselection.value and hasattr(self, "openServiceList"):
			self.toggleShow()
		else:
			self.hide()
			if hasattr(self, "pvrStateDialog"):
				try:
					self.pvrStateDialog.hide()
				except:
					pass

	def hidePipOnExitCallback(self, answer):
		if answer:
			self.showPiP()

	def connectShowHideNotifier(self, fnc):
		if not fnc in self.onShowHideNotifiers:
			self.onShowHideNotifiers.append(fnc)

	def disconnectShowHideNotifier(self, fnc):
		if fnc in self.onShowHideNotifiers:
			self.onShowHideNotifiers.remove(fnc)

	def serviceStarted(self):
		if self.execing:
			if config.usage.show_infobar_on_zap.value:
				self.doShow()
		self.showHideVBI()

	def startHideTimer(self):
		if self.__state == self.STATE_SHOWN and not self.__locked:
			self.hideTimer.stop()
			if self.secondInfoBarScreen and self.secondInfoBarScreen.shown:
				idx = config.usage.show_second_infobar.index - 1
			else:
				idx = config.usage.infobar_timeout.index
			if idx:
				self.hideTimer.startLongTimer(idx)
		elif hasattr(self, "pvrStateDialog"):
			self.hideTimer.stop()
		self.skipToggleShow = False

	def doShow(self):
		self.show()
		self.hideTimer.stop()
		self.DimmingTimer.stop()
		self.doWriteAlpha(config.av.osd_alpha.value)
		self.startHideTimer()

	def doTimerHide(self):
		self.hideTimer.stop()
		self.DimmingTimer.start(300, True)
		self.dimmed = config.usage.show_infobar_dimming_speed.value
		self.skipToggleShow = False

	def doHide(self):
		if self.__state != self.STATE_HIDDEN:
			if self.dimmed > 0:
				self.doWriteAlpha((config.av.osd_alpha.value*self.dimmed/config.usage.show_infobar_dimming_speed.value))
				self.DimmingTimer.start(5, True)
			else:
				self.DimmingTimer.stop()
				self.hide()
		elif self.__state == self.STATE_HIDDEN and self.secondInfoBarScreen and self.secondInfoBarScreen.shown:
			if self.dimmed > 0:
				self.doWriteAlpha((config.av.osd_alpha.value*self.dimmed/config.usage.show_infobar_dimming_speed.value))
				self.DimmingTimer.start(5, True)
			else:
				self.DimmingTimer.stop()
				self.secondInfoBarScreen.hide()
				self.secondInfoBarWasShown = False
				self.resetAlpha()

	def okButtonCheck(self):
		if config.usage.ok_is_channelselection.value and hasattr(self, "openServiceList"):
			if isinstance(self, InfoBarTimeshift) and self.timeshiftEnabled() and isinstance(self, InfoBarSeek) and self.seekstate == self.SEEK_STATE_PAUSE:
				return
			self.openServiceList()
		else:
			self.toggleShow()

	def toggleShow(self):
		if self.skipToggleShow:
			self.skipToggleShow = False
			return
		if not hasattr(self, "LongButtonPressed"):
			self.LongButtonPressed = False
		if not self.LongButtonPressed:
			if self.__state == self.STATE_HIDDEN:
				self.show()
				if self.secondInfoBarScreen:
					self.secondInfoBarScreen.hide()
			elif isStandardInfoBar(self) and config.usage.show_second_infobar.value == "EPG":
				self.showDefaultEPG()
			elif self.secondInfoBarScreen and config.usage.show_second_infobar.value and not self.secondInfoBarScreen.shown:
				self.secondInfoBarScreen.show()
				self.startHideTimer()
			else:
				self.hide()
				self.hideTimer.stop()

	def lockShow(self):
		try:
			self.__locked += 1
		except:
			self.__locked = 0
		if self.execing:
			self.show()
			self.hideTimer.stop()
			self.skipToggleShow = False

	def unlockShow(self):
		if config.usage.show_infobar_do_dimming.value and self.lastResetAlpha is False:
			self.doWriteAlpha(config.av.osd_alpha.value)
		try:
			self.__locked -= 1
		except:
			self.__locked = 0
		if self.__locked  <0:
			self.__locked = 0
		if self.execing:
			self.startHideTimer()

	def checkHideVBI(self):
		service = self.session.nav.getCurrentlyPlayingServiceReference()
		servicepath = service and service.getPath()
		if servicepath and servicepath.startswith("/"):
			if service.toString().startswith("1:"):
				info = eServiceCenter.getInstance().info(service)
				service = info and info.getInfoString(service, iServiceInformation.sServiceref)
				FLAG_HIDE_VBI = 512
				return service and eDVBDB.getInstance().getFlag(eServiceReference(service)) & FLAG_HIDE_VBI and True
			else:
				return ".hidvbi." in servicepath.lower()
		service = self.session.nav.getCurrentService()
		info = service and service.info()
		return info and info.getInfo(iServiceInformation.sHideVBI) == 1

	def showHideVBI(self):
		if self.checkHideVBI():
			self.hideVBILineScreen.show()
		else:
			self.hideVBILineScreen.hide()

class BufferIndicator(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self["status"] = Label()
		self.mayShow = False
		self.__event_tracker = ServiceEventTracker(screen=self, eventmap={
				iPlayableService.evBuffering: self.bufferChanged,
				iPlayableService.evStart: self.__evStart,
				iPlayableService.evGstreamerPlayStarted: self.__evGstreamerPlayStarted,
			})

	def bufferChanged(self):
		if self.mayShow:
			service = self.session.nav.getCurrentService()
			info = service and service.info()
			if info:
				value = info.getInfo(iServiceInformation.sBuffer)
				if value and value != 100:
					self["status"].setText(_("Buffering %d%%") % value)
					if not self.shown:
						self.show()

	def __evStart(self):
		self.mayShow = True
		self.hide()

	def __evGstreamerPlayStarted(self):
		self.mayShow = False
		self.hide()

class InfoBarBuffer():
	def __init__(self):
		self.bufferScreen = self.session.instantiateDialog(BufferIndicator)
		self.bufferScreen.hide()

class NumberZap(Screen):
	def quit(self):
		self.Timer.stop()
		self.close()

	def keyOK(self):
		self.Timer.stop()
		self.close(self.service, self.bouquet)

	def handleServiceName(self):
		if self.searchNumber:
			self.service, self.bouquet = self.searchNumber(int(self["number"].getText()))
			self["servicename"].setText(ServiceReference(self.service).getServiceName())
			if not self.startBouquet:
				self.startBouquet = self.bouquet

	def keyBlue(self):
		self.Timer.start(3000, True)
		if self.searchNumber:
			if self.startBouquet == self.bouquet:
				self.service, self.bouquet = self.searchNumber(int(self["number"].getText()), firstBouquetOnly=True)
			else:
				self.service, self.bouquet = self.searchNumber(int(self["number"].getText()))
			self["servicename"].setText(ServiceReference(self.service).getServiceName())

	def keyNumberGlobal(self, number):
		if config.usage.numzaptimeoutmode.value != "off":
			if config.usage.numzaptimeoutmode.value == "standard":
				self.Timer.start(1000, True)
			else:
				self.Timer.start(config.usage.numzaptimeout2.value, True)
		self.numberString += str(number)
		self["number"].setText(self.numberString)
		self["servicenumber"].setText(self.numberString)
		self["number_summary"].setText(self.numberString)
		self.field = self.numberString

		self.handleServiceName()
		self["service_summary"].setText(self["servicename"].getText())
		if config.usage.numzappicon.value:
			self.showPicon()

		if len(self.numberString) >= int(config.usage.maxchannelnumlen.value):
			if self.Timer.isActive():
				self.Timer.stop()
			self.Timer.start(100, True)

	def showPicon(self):
		self["Service"].newService(self.service)

	def __init__(self, session, number, searchNumberFunction=None):
		Screen.__init__(self, session)

		if config.usage.numzappicon.value:
			self.onLayoutFinish.append(self.showPicon)
			self.skinName = ["NumberZapPicon", "NumberZapWithName"]

		self.onChangedEntry = [ ]
		self.numberString = str(number)
		self.field = str(number)
		self.searchNumber = searchNumberFunction
		self.startBouquet = None

		self["channel"] = Label(_("Channel:"))
		self["channel_summary"] = StaticText(_("Channel:"))

		self["number"] = Label(self.numberString)
		self["servicenumber"] = Label(self.numberString)
		self["number_summary"] = StaticText(self.numberString)
		self["servicename"] = Label()
		self["service_summary"] = StaticText("")
		self["Service"] = ServiceEvent()
		self.handleServiceName()
		self["service_summary"].setText(self["servicename"].getText())

		self["actions"] = NumberActionMap( [ "SetupActions", "ShortcutActions" ],
			{
				"cancel": self.quit,
				"ok": self.keyOK,
				"blue": self.keyBlue,
				"1": self.keyNumberGlobal,
				"2": self.keyNumberGlobal,
				"3": self.keyNumberGlobal,
				"4": self.keyNumberGlobal,
				"5": self.keyNumberGlobal,
				"6": self.keyNumberGlobal,
				"7": self.keyNumberGlobal,
				"8": self.keyNumberGlobal,
				"9": self.keyNumberGlobal,
				"0": self.keyNumberGlobal
			})

		self.Timer = eTimer()
		self.Timer.callback.append(self.keyOK)
		if config.usage.maxchannelnumlen.value == "1":
			self.Timer.start(100, True)
		elif config.usage.numzaptimeoutmode.value != "off":
			if config.usage.numzaptimeoutmode.value == "standard":
				self.Timer.start(3000, True)
			else:
				self.Timer.start(config.usage.numzaptimeout1.value, True)

class InfoBarNumberZap:
	""" Handles an initial number for NumberZapping """
	def __init__(self):
		self["NumberActions"] = NumberActionMap( [ "NumberActions"],
			{
				"1": self.keyNumberGlobal,
				"2": self.keyNumberGlobal,
				"3": self.keyNumberGlobal,
				"4": self.keyNumberGlobal,
				"5": self.keyNumberGlobal,
				"6": self.keyNumberGlobal,
				"7": self.keyNumberGlobal,
				"8": self.keyNumberGlobal,
				"9": self.keyNumberGlobal,
				"0": self.keyNumberGlobal,
			})

	def keyNumberGlobal(self, number):
		if self.pvrStateDialog.has_key("PTSSeekPointer") and self.timeshiftEnabled() and self.isSeekable():
			InfoBarTimeshiftState._mayShow(self)
			self.pvrStateDialog["PTSSeekPointer"].setPosition((self.pvrStateDialog["PTSSeekBack"].instance.size().width()-4)/2, self.pvrStateDialog["PTSSeekPointer"].position[1])
			if self.seekstate != self.SEEK_STATE_PLAY:
				self.setSeekState(self.SEEK_STATE_PLAY)
			self.ptsSeekPointerOK()
			return

		if self.pts_blockZap_timer.isActive():
			return

		# if self.save_current_timeshift and self.timeshiftEnabled():
		# 	InfoBarTimeshift.saveTimeshiftActions(self)
		# 	return

		if number == 0:
			if isinstance(self, InfoBarPiP) and self.pipHandles0Action():
				self.pipDoHandle0Action()
			elif len(self.servicelist.history) > 1 or config.usage.panicbutton.value:
				self.checkTimeshiftRunning(self.recallPrevService)
		else:
			if self.has_key("TimeshiftActions") and self.timeshiftEnabled():
				ts = self.getTimeshift()
				if ts and ts.isTimeshiftActive():
					return
			self.session.openWithCallback(self.numberEntered, NumberZap, number, self.searchNumber)

	def recallPrevService(self, reply):
		if reply:
			if config.usage.panicbutton.value:
				if self.session.pipshown:
					del self.session.pip
					self.session.pipshown = False
				try:
					if config.misc.spazeChannelSelection.value:
						from Screens.newChannelSelection import newChannelSelection
						self.servicelist = self.session.instantiateDialog(newChannelSelection)
					else:
						self.servicelist = self.session.instantiateDialog(ChannelSelection)
				except:
					self.servicelist = self.session.instantiateDialog(ChannelSelection)

				self.servicelist.history_tv = []
				self.servicelist.history_radio = []
				self.servicelist.history = self.servicelist.history_tv
				self.servicelist.history_pos = 0
				self.servicelist2 = self.session.instantiateDialog(PiPZapSelection)
				self.servicelist2.history_tv = []
				self.servicelist2.history_radio = []
				self.servicelist2.history = self.servicelist.history_tv
				self.servicelist2.history_pos = 0
				if config.usage.multibouquet.value:
					bqrootstr = '1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "bouquets.tv" ORDER BY bouquet'
				else:
					self.service_types = service_types_tv
					bqrootstr = '%s FROM BOUQUET "userbouquet.favourites.tv" ORDER BY bouquet'% self.service_types
				serviceHandler = eServiceCenter.getInstance()
				rootbouquet = eServiceReference(bqrootstr)
				bouquet = eServiceReference(bqrootstr)
				bouquetlist = serviceHandler.list(bouquet)
					
				if not bouquetlist is None:
					while True:
						bouquet = bouquetlist.getNext()
						if bouquet.flags & eServiceReference.isDirectory:
							self.servicelist.clearPath()
							self.servicelist.setRoot(bouquet)
							servicelist = serviceHandler.list(bouquet)
							if not servicelist is None:
								serviceIterator = servicelist.getNext()
								while serviceIterator.valid():
									service, bouquet2 = self.searchNumber(config.usage.panicchannel.value)
									if service == serviceIterator:
										break
									serviceIterator = servicelist.getNext()
								if serviceIterator.valid() and service == serviceIterator:
									break
					self.servicelist.enterPath(rootbouquet)
					self.servicelist.enterPath(bouquet)
					self.servicelist.saveRoot()
					self.servicelist2.enterPath(rootbouquet)
					self.servicelist2.enterPath(bouquet)
					self.servicelist2.saveRoot()
				self.selectAndStartService(service, bouquet)
			else:
				self.servicelist.recallPrevService()

	def numberEntered(self, service=None, bouquet=None):
		if service:
			self.selectAndStartService(service, bouquet)

	def searchNumberHelper(self, serviceHandler, num, bouquet):
		servicelist = serviceHandler.list(bouquet)
		if servicelist:
			serviceIterator = servicelist.getNext()
			while serviceIterator.valid():
				if num == serviceIterator.getChannelNum():
					return serviceIterator
				serviceIterator = servicelist.getNext()
		return None

	def searchNumber(self, number, firstBouquetOnly=False, bouquet=None):
		bouquet = bouquet or self.servicelist.getRoot()
		service = None
		serviceHandler = eServiceCenter.getInstance()
		if not firstBouquetOnly:
			service = self.searchNumberHelper(serviceHandler, number, bouquet)
		if config.usage.multibouquet.value and not service:
			bouquet = self.servicelist.bouquet_root
			bouquetlist = serviceHandler.list(bouquet)
			if bouquetlist:
				bouquet = bouquetlist.getNext()
				while bouquet.valid():
					if bouquet.flags & eServiceReference.isDirectory:
						service = self.searchNumberHelper(serviceHandler, number, bouquet)
						if service:
							playable = not (service.flags & (eServiceReference.isMarker|eServiceReference.isDirectory)) or (service.flags & eServiceReference.isNumberedMarker)
							if not playable:
								service = None
							break
						if config.usage.alternative_number_mode.value or firstBouquetOnly:
							break
					bouquet = bouquetlist.getNext()
		return service, bouquet

	def selectAndStartService(self, service, bouquet):
		if service:
			if self.servicelist.getRoot() != bouquet: #already in correct bouquet?
				self.servicelist.clearPath()
				if self.servicelist.bouquet_root != bouquet:
					self.servicelist.enterPath(self.servicelist.bouquet_root)
				self.servicelist.enterPath(bouquet)
			self.servicelist.setCurrentSelection(service) #select the service in servicelist
			self.servicelist.zap(enable_pipzap=True)
			self.servicelist.correctChannelNumber()
			self.servicelist.startRoot = None

	def zapToNumber(self, number):
		service, bouquet = self.searchNumber(number)
		self.selectAndStartService(service, bouquet)

config.misc.initialchannelselection = ConfigBoolean(default=True)

class InfoBarChannelSelection:
	""" ChannelSelection - handles the channelSelection dialog and the initial
	channelChange actions which open the channelSelection dialog """
	def __init__(self):
		#instantiate forever
		try:
			if config.misc.spazeChannelSelection.value:
				from Screens.newChannelSelection import newChannelSelection
				self.servicelist = self.session.instantiateDialog(newChannelSelection)
			else:
				self.servicelist = self.session.instantiateDialog(ChannelSelection)
		except:
			self.servicelist = self.session.instantiateDialog(ChannelSelection)
		self.servicelist2 = self.session.instantiateDialog(PiPZapSelection)
		self.tscallback = None

		if config.misc.initialchannelselection.value:
			self.onShown.append(self.firstRun)

		self["ChannelSelectActions"] = HelpableActionMap(self, "InfobarChannelSelection",
			{
				"keyUp": (self.keyUpCheck, self.getKeyUpHelptext),
				"keyDown": (self.keyDownCheck, self.getKeyDownHelptext),
				"keyLeft": (self.keyLeftCheck, self.getKeyLeftHelptext),
				"keyRight": (self.keyRightCheck, self.getKeyRightHelptext),
				"zapUp": (self.zapUp, _("Switch to previous channel")),
				"zapDown": (self.zapDown, _("Switch next channel")),
				"volumeUp": (self.volumeUp, _("change Volume up")),
				"volumeDown": (self.volumeDown, _("change Volume down")),
				"historyBack": (self.historyBack, _("Switch to previous channel in history")),
				"historyNext": (self.historyNext, _("Switch to next channel in history")),
				"keyChannelUp": (self.keyChannelUpCheck, self.getKeyChannelUpHelptext),
				"keyChannelDown": (self.keyChannelDownCheck, self.getKeyChannelDownHelptext),
			})

	def firstRun(self):
		self.onShown.remove(self.firstRun)
		config.misc.initialchannelselection.value = False
		config.misc.initialchannelselection.save()
		self.openServiceList()

	def showTvChannelList(self, zap=False):
		self.servicelist.setModeTv()
		if zap:
			self.servicelist.zap()
		if config.usage.show_servicelist.value:
			self.session.execDialog(self.servicelist)

	def showRadioChannelList(self, zap=False):
		self.servicelist.setModeRadio()
		if zap:
			self.servicelist.zap()
		if config.usage.show_servicelist.value:
			self.session.execDialog(self.servicelist)

	def historyBack(self):
		if config.usage.historymode.value == "0":
			self.servicelist.historyBack()
		else:
			self.servicelist.historyZap(-1)

	def historyNext(self):
		if config.usage.historymode.value == "0":
			self.servicelist.historyNext()
		else:
			self.servicelist.historyZap(+1)

	def keyUpCheck(self):
		if config.usage.oldstyle_zap_controls.value == "neutrino" or config.usage.oldstyle_zap_controls.value == "openspa":
			self.zapDown()
		else:
			self.switchChannelUp()

	def keyDownCheck(self):
		if config.usage.oldstyle_zap_controls.value == "neutrino" or config.usage.oldstyle_zap_controls.value == "openspa":
			self.zapUp()
		else:
			self.switchChannelDown()

	def keyLeftCheck(self):
		if config.usage.oldstyle_zap_controls.value == "neutrino":
			self.switchChannelUp()
		elif config.usage.oldstyle_zap_controls.value == "openspa":
			self.volumeDown()
		else:
			self.zapUp()

	def keyRightCheck(self):
		if config.usage.oldstyle_zap_controls.value == "neutrino":
			self.switchChannelDown()
		elif config.usage.oldstyle_zap_controls.value == "openspa":
			self.volumeUp()
		else:
			self.zapDown()

	def keyChannelUpCheck(self):
		if config.usage.zap_with_ch_buttons.value:
			self.zapDown()
		else:
			self.openServiceList()

	def keyChannelDownCheck(self):
		if config.usage.zap_with_ch_buttons.value:
			self.zapUp()
		else:
			self.openServiceList()

	def getKeyUpHelptext(self):
		if config.usage.oldstyle_zap_controls.value == "neutrino" or config.usage.oldstyle_zap_controls.value == "openspa":
			value = _("Switch to next channel")
		else:
			value = _("Open service list")
			if not "keep" in config.usage.servicelist_cursor_behavior.value:
				value += " " + _("and select previous channel")
		return value

	def getKeyDownHelptext(self):
		if config.usage.oldstyle_zap_controls.value == "neutrino" or config.usage.oldstyle_zap_controls.value == "openspa":
			value = _("Switch to previous channel")
		else:
			value = _("Open service list")
			if not "keep" in config.usage.servicelist_cursor_behavior.value:
				value += " " + _("and select next channel")
		return value

	def getKeyLeftHelptext(self):
		if config.usage.oldstyle_zap_controls.value == "neutrino":
			value = _("Open service list")
			if not "keep" in config.usage.servicelist_cursor_behavior.value:
				value += " " + _("and select previous channel")
		elif config.usage.oldstyle_zap_controls.value == "openspa":
			value = _("Volume down")
		else:
			value = _("Switch to previous channel")
		return value

	def getKeyRightHelptext(self):
		if config.usage.oldstyle_zap_controls.value == "nuetrino":
			value = _("Open service list")
			if not "keep" in config.usage.servicelist_cursor_behavior.value:
				value += " " + _("and select next channel")
		elif config.usage.oldstyle_zap_controls.value == "openspa":
			value = _("Volume up")
		else:
			value = _("Switch to next channel")
		return value

	def getKeyChannelUpHelptext(self):
		return config.usage.zap_with_ch_buttons.value and _("Switch to next channel") or _("Open service list")

	def getKeyChannelDownHelptext(self):
		return config.usage.zap_with_ch_buttons.value and _("Switch to previous channel") or _("Open service list")

	def switchChannelUp(self):
		if not self.secondInfoBarScreen or not self.secondInfoBarScreen.shown:
			self.keyHide()
			if not self.LongButtonPressed or SystemInfo.get("NumVideoDecoders", 1) <= 1:
				if not config.usage.show_bouquetalways.value:
					if "keep" not in config.usage.servicelist_cursor_behavior.value:
						self.servicelist.moveUp()
					self.session.execDialog(self.servicelist)
				else:
					self.servicelist.showFavourites()
					self.session.execDialog(self.servicelist)
			elif self.LongButtonPressed:
				if not config.usage.show_bouquetalways.value:
					if "keep" not in config.usage.servicelist_cursor_behavior.value:
						self.servicelist2.moveUp()
					self.session.execDialog(self.servicelist2)
				else:
					self.servicelist2.showFavourites()
					self.session.execDialog(self.servicelist2)

	def switchChannelDown(self):
		if not self.secondInfoBarScreen or not self.secondInfoBarScreen.shown:
			self.keyHide()
			if not self.LongButtonPressed or SystemInfo.get("NumVideoDecoders", 1) <= 1:
				if not config.usage.show_bouquetalways.value:
					if "keep" not in config.usage.servicelist_cursor_behavior.value:
						self.servicelist.moveDown()
					self.session.execDialog(self.servicelist)
				else:
					self.servicelist.showFavourites()
					self.session.execDialog(self.servicelist)
			elif self.LongButtonPressed:
				if not config.usage.show_bouquetalways.value:
					if "keep" not in config.usage.servicelist_cursor_behavior.value:
						self.servicelist2.moveDown()
					self.session.execDialog(self.servicelist2)
				else:
					self.servicelist2.showFavourites()
					self.session.execDialog(self.servicelist2)

	def openServiceList(self):
		self.session.execDialog(self.servicelist)

	def openServiceListPiP(self):
		self.session.execDialog(self.servicelist2)

	def openSatellites(self):
		self.servicelist.showSatellites()
		self.session.execDialog(self.servicelist)

	def openBouquets(self):
		self.servicelist.showFavourites()
		self.session.execDialog(self.servicelist)

	def zapUp(self):
		if not hasattr(self, "LongButtonPressed"):
			self.LongButtonPressed = False
		if not self.LongButtonPressed or SystemInfo.get("NumVideoDecoders", 1) <= 1:
			if self.pts_blockZap_timer.isActive():
				return

			self["SeekActionsPTS"].setEnabled(False)
			if self.servicelist.inBouquet():
				prev = self.servicelist.getCurrentSelection()
				if prev:
					prev = prev.toString()
					while True:
						if config.usage.quickzap_bouquet_change.value and self.servicelist.atBegin():
							self.servicelist.prevBouquet()
							self.servicelist.moveEnd()
						else:
							self.servicelist.moveUp()
						cur = self.servicelist.getCurrentSelection()
						if cur:
							if self.servicelist.dopipzap:
								isPlayable = self.session.pip.isPlayableForPipService(cur)
							else:
								isPlayable = isPlayableForCur(cur)
						if cur and (cur.toString() == prev or isPlayable):
							break
			else:
				self.servicelist.moveUp()
			self.servicelist.zap(enable_pipzap=True)

		elif self.LongButtonPressed:
			if not hasattr(self.session, 'pip') and not self.session.pipshown:
				self.session.open(MessageBox, _("Please open Picture in Picture first"), MessageBox.TYPE_ERROR)
				return

			from Screens.ChannelSelection import ChannelSelection
			ChannelSelectionInstance = ChannelSelection.instance
			ChannelSelectionInstance.dopipzap = True
			if self.servicelist2.inBouquet():
				prev = self.servicelist2.getCurrentSelection()
				if prev:
					prev = prev.toString()
					while True:
						if config.usage.quickzap_bouquet_change.value and self.servicelist2.atBegin():
							self.servicelist2.prevBouquet()
							self.servicelist2.moveEnd()
						else:
							self.servicelist2.moveUp()
						cur = self.servicelist2.getCurrentSelection()
						if cur:
							if ChannelSelectionInstance.dopipzap:
								isPlayable = self.session.pip.isPlayableForPipService(cur)
							else:
								isPlayable = isPlayableForCur(cur)
						if cur and (cur.toString() == prev or isPlayable):
							break
			else:
				self.servicelist2.moveUp()
			self.servicelist2.zap(enable_pipzap=True)
			ChannelSelectionInstance.dopipzap = False
		if self.timeshiftEnabled() and self.isSeekable():
			self["SeekActionsPTS"].setEnabled(True)

	def zapDown(self):
		if not hasattr(self, "LongButtonPressed"):
			self.LongButtonPressed = False
		if not self.LongButtonPressed or SystemInfo.get("NumVideoDecoders", 1) <= 1:
			if self.pts_blockZap_timer.isActive():
				return

			self["SeekActionsPTS"].setEnabled(False)
			if self.servicelist.inBouquet():
				prev = self.servicelist.getCurrentSelection()
				if prev:
					prev = prev.toString()
					while True:
						if config.usage.quickzap_bouquet_change.value and self.servicelist.atEnd():
							self.servicelist.nextBouquet()
							self.servicelist.moveTop()
						else:
							self.servicelist.moveDown()
						cur = self.servicelist.getCurrentSelection()
						if cur:
							if self.servicelist.dopipzap:
								isPlayable = self.session.pip.isPlayableForPipService(cur)
							else:
								isPlayable = isPlayableForCur(cur)
						if cur and (cur.toString() == prev or isPlayable):
							break
			else:
				self.servicelist.moveDown()
			self.servicelist.zap(enable_pipzap=True)
		elif self.LongButtonPressed:
			if not hasattr(self.session, 'pip') and not self.session.pipshown:
				self.session.open(MessageBox, _("Please open Picture in Picture first"), MessageBox.TYPE_ERROR)
				return

			from Screens.ChannelSelection import ChannelSelection
			ChannelSelectionInstance = ChannelSelection.instance
			ChannelSelectionInstance.dopipzap = True
			if self.servicelist2.inBouquet():
				prev = self.servicelist2.getCurrentSelection()
				if prev:
					prev = prev.toString()
					while True:
						if config.usage.quickzap_bouquet_change.value and self.servicelist2.atEnd():
							self.servicelist2.nextBouquet()
							self.servicelist2.moveTop()
						else:
							self.servicelist2.moveDown()
						cur = self.servicelist2.getCurrentSelection()
						if cur:
							if ChannelSelectionInstance.dopipzap:
								isPlayable = self.session.pip.isPlayableForPipService(cur)
							else:
								isPlayable = isPlayableForCur(cur)
						if cur and (cur.toString() == prev or isPlayable):
							break
			else:
				self.servicelist2.moveDown()
			self.servicelist2.zap(enable_pipzap=True)
			ChannelSelectionInstance.dopipzap = False
		if self.timeshiftEnabled() and self.isSeekable():
			self["SeekActionsPTS"].setEnabled(True)

	def volumeUp(self):
		VolumeControl.instance.volUp()

	def volumeDown(self):
		VolumeControl.instance.volDown()

class InfoBarMenu:
	""" Handles a menu action, to open the (main) menu """
	def __init__(self):
		self["MenuActions"] = HelpableActionMap(self, "InfobarMenuActions",
			{
				"mainMenu": (self.mainMenu, _("Enter main menu...")),
				"showNetworkSetup": (self.showNetworkMounts, _("Show network mounts ...")),
				"showSystemSetup": (self.showSystemMenu, _("Show network mounts ...")),
				"showRFmod": (self.showRFSetup, _("Show RFmod setup...")),
				"showHDMIRecord": (self.showHDMiRecordSetup, _("Show HDMIRecord setup...")),
				"toggleAspectRatio": (self.toggleAspectRatio, _("Toggle aspect ratio...")),
			})
		self.session.infobar = None

	def mainMenu(self):
		# print "loading mainmenu XML..."
		menu = mdom.getroot()
		assert menu.tag == "menu", "root element in menu must be 'menu'!"

		self.session.infobar = self
		# so we can access the currently active infobar from screens opened from within the mainmenu
		# at the moment used from the SubserviceSelection

		self.session.openWithCallback(self.mainMenuClosed, MainMenu, menu)

	def mainMenuClosed(self, *val):
		self.session.infobar = None

	def toggleAspectRatio(self):
		ASPECT = [ "auto", "16:9", "4:3" ]
		ASPECT_MSG = { "auto":"Auto", "16:9":"16:9", "4:3":"4:3" }
		if config.av.aspect.value in ASPECT:
			index = ASPECT.index(config.av.aspect.value)
			config.av.aspect.value = ASPECT[(index+1)%3]
		else:
			config.av.aspect.value = "auto"
		config.av.aspect.save()
		self.session.open(MessageBox, _("AV aspect is %s.") % ASPECT_MSG[config.av.aspect.value], MessageBox.TYPE_INFO, timeout=5)

	def showSystemMenu(self):
		menulist = mdom.getroot().findall('menu')
		for item in menulist:
			if item.attrib['entryID'] == 'setup_selection':
				menulist = item.findall('menu')
				for item in menulist:
					if item.attrib['entryID'] == 'system_selection':
						menu = item
		assert menu.tag == "menu", "root element in menu must be 'menu'!"
		self.session.openWithCallback(self.mainMenuClosed, Menu, menu)

	def showNetworkMounts(self):
		menulist = mdom.getroot().findall('menu')
		for item in menulist:
			if item.attrib['entryID'] == 'setup_selection':
				menulist = item.findall('menu')
				for item in menulist:
					if item.attrib['entryID'] == 'extended_selection':
						menulist = item.findall('menu')
						for item in menulist:
							if item.attrib['entryID'] == 'network_menu':
								menu = item
		assert menu.tag == "menu", "root element in menu must be 'menu'!"
		self.session.openWithCallback(self.mainMenuClosed, Menu, menu)

	def showRFSetup(self):
		if SystemInfo["RfModulator"]:
			self.session.openWithCallback(self.mainMenuClosed, Setup, 'RFmod')

	def showHDMiRecordSetup(self):
		if SystemInfo["HDMIin"]:
			self.session.openWithCallback(self.mainMenuClosed, Setup, 'HDMIRecord')

	def mainMenuClosed(self, *val):
		self.session.infobar = None

class InfoBarSimpleEventView:
	""" Opens the Eventview for now/next """
	def __init__(self):
		self["EventViewActions"] = HelpableActionMap(self, "InfobarEPGActions",
			{
				"showEventInfo": (self.openEventView, _("Show event details")),
				"showEventInfoSingleEPG": (self.openEventView, _("Show event details")),
				"showInfobarOrEpgWhenInfobarAlreadyVisible": self.showEventInfoWhenNotVisible,
			})

	def showEventInfoWhenNotVisible(self):
		if self.shown:
			self.openEventView()
		else:
			self.toggleShow()
			return 1

	def openEventView(self):
		epglist = [ ]
		self.epglist = epglist
		service = self.session.nav.getCurrentService()
		ref = self.session.nav.getCurrentlyPlayingServiceOrGroup()
		info = service.info()
		ptr=info.getEvent(0)
		if ptr:
			epglist.append(ptr)
		ptr=info.getEvent(1)
		if ptr:
			epglist.append(ptr)
		if epglist:
			self.session.open(EventViewSimple, epglist[0], ServiceReference(ref), self.eventViewCallback)

	def eventViewCallback(self, setEvent, setService, val): #used for now/next displaying
		epglist = self.epglist
		if len(epglist) > 1:
			tmp = epglist[0]
			epglist[0] = epglist[1]
			epglist[1] = tmp
			setEvent(epglist[0])

class SimpleServicelist:
	def __init__(self, services):
		self.setServices(services)

	def setServices(self, services):
		self.services = services
		self.length = len(services)
		self.current = 0

	def selectService(self, service):
		if not self.length:
			self.current = -1
			return False
		else:
			self.current = 0
			while self.services[self.current].ref != service:
				self.current += 1
				if self.current >= self.length:
					return False
		return True

	def nextService(self):
		if not self.length:
			return
		if self.current+1 < self.length:
			self.current += 1
		else:
			self.current = 0

	def prevService(self):
		if not self.length:
			return
		if self.current-1 > -1:
			self.current -= 1
		else:
			self.current = self.length - 1

	def currentService(self):
		if not self.length or self.current >= self.length:
			return None
		return self.services[self.current]

class InfoBarEPG:
	""" EPG - Opens an EPG list when the showEPGList action fires """
	def __init__(self):
		self.is_now_next = False
		self.dlg_stack = [ ]
		self.bouquetSel = None
		self.eventView = None
		self.epglist = []
		self.defaultEPGType = self.getDefaultEPGtype()
		self.defaultGuideType = self.getDefaultGuidetype()
		self.__event_tracker = ServiceEventTracker(screen=self, eventmap={
				iPlayableService.evUpdatedEventInfo: self.__evEventInfoChanged,
			})

		self["EPGActions"] = HelpableActionMap(self, "InfobarEPGActions",
			{
				"showEventInfo": (self.showDefaultEPG, _("Show EPG...")),
				"showEventInfoSingleEPG": (self.showSingleEPG, _("Show single service EPG")),
				"showEventInfoMultiEPG": (self.showMultiEPG, _("Show multi channel EPG")),
				"showEventInfoPlugin": (self.showEventInfoPlugins, _("List EPG functions...")),
				"showEventGuidePlugin": (self.showEventGuidePlugins, _("List EPG functions...")),
				"showInfobarOrEpgWhenInfobarAlreadyVisible": self.showEventInfoWhenNotVisible,
			})

	def getEPGPluginList(self, getAll=False):
		pluginlist = [(p.name, boundFunction(self.runPlugin, p), p.path) for p in plugins.getPlugins(where=PluginDescriptor.WHERE_EVENTINFO)
				if 'selectedevent' not in p.__call__.func_code.co_varnames] or []
		from Components.ServiceEventTracker import InfoBarCount
		if getAll or InfoBarCount == 1:
			pluginlist.append((_("Show EPG for current channel..."), self.openSingleServiceEPG, "current_channel"))
		pluginlist.append((_("Multi EPG"), self.openMultiServiceEPG, "multi_epg"))
		pluginlist.append((_("Current event EPG"), self.openEventView, "event_epg"))
		return pluginlist

	def getDefaultEPGtype(self):
		config.usage.defaultEPGType=ConfigText()
		for plugin in self.getEPGPluginList():
			if plugin[2] == config.usage.defaultEPGType.value:
				return plugin[1]
		return None

	def getDefaultGuidetype(self):
		config.usage.defaultGuideType=ConfigText(default="/usr/lib/enigma2/python/Plugins/Extensions/GraphMultiEPG")
		for plugin in self.getEPGPluginList():
			try:
				if plugin[2] == config.usage.defaultGuideType.value.split("@")[0] and plugin[0] == config.usage.defaultGuideType.value.split("@")[1]:
					return plugin[1]
			except:
					pass
		return None

	def showEventInfoWhenNotVisible(self):
		if self.shown:
			self.openEventView()
		else:
			self.toggleShow()
			return 1

	def zapToService(self, service, preview=False, zapback=False):
		if self.servicelist.startServiceRef is None:
			self.servicelist.startServiceRef = self.session.nav.getCurrentlyPlayingServiceOrGroup()
		if service is not None:
			if self.servicelist.getRoot() != self.epg_bouquet: #already in correct bouquet?
				self.servicelist.clearPath()
				if self.servicelist.bouquet_root != self.epg_bouquet:
					self.servicelist.enterPath(self.servicelist.bouquet_root)
				self.servicelist.enterPath(self.epg_bouquet)
			self.servicelist.setCurrentSelection(service) #select the service in servicelist
		if not zapback or preview:
			self.servicelist.zap(enable_pipzap=True)
		if (self.servicelist.dopipzap or zapback) and not preview:
			self.servicelist.zapBack()
		if not preview:
			self.servicelist.startServiceRef = None
			self.servicelist.startRoot = None

	def getBouquetServices(self, bouquet):
		services = [ ]
		servicelist = eServiceCenter.getInstance().list(bouquet)
		if not servicelist is None:
			while True:
				service = servicelist.getNext()
				if not service.valid(): #check if end of list
					break
				if service.flags & (eServiceReference.isDirectory | eServiceReference.isMarker): #ignore non playable services
					continue
				services.append(ServiceReference(service))
		return services

	def openBouquetEPG(self, bouquet, withCallback=True):
		services = self.getBouquetServices(bouquet)
		if services:
			self.epg_bouquet = bouquet
			if withCallback:
				self.dlg_stack.append(self.session.openWithCallback(self.closed, EPGSelection, services, self.zapToService, None, self.changeBouquetCB))
			else:
				self.session.open(EPGSelection, services, self.zapToService, None, self.changeBouquetCB)

	def changeBouquetCB(self, direction, epg):
		if self.bouquetSel:
			if direction > 0:
				self.bouquetSel.down()
			else:
				self.bouquetSel.up()
			bouquet = self.bouquetSel.getCurrent()
			services = self.getBouquetServices(bouquet)
			if services:
				self.epg_bouquet = bouquet
				epg.setServices(services)

	def selectBouquet(self, bouquetref, epg):
		services = self.getBouquetServices(bouquetref)
		if services:
			self.epg_bouquet = bouquetref
			self.serviceSel.setServices(services)
			epg.setServices(services)

	def setService(self, service):
		if service:
			self.serviceSel.selectService(service)

	def closed(self, ret=False):
		closedScreen = self.dlg_stack.pop()
		if self.bouquetSel and closedScreen == self.bouquetSel:
			self.bouquetSel = None
		elif self.eventView and closedScreen == self.eventView:
			self.eventView = None
		if ret:
			dlgs=len(self.dlg_stack)
			if dlgs > 0:
				self.dlg_stack[dlgs-1].close(dlgs > 1)

	def openMultiServiceEPG(self, withCallback=True):
		bouquets = self.servicelist.getBouquetList()
		if bouquets is None:
			cnt = 0
		else:
			cnt = len(bouquets)
		if config.usage.multiepg_ask_bouquet.value:
			self.openMultiServiceEPGAskBouquet(bouquets, cnt, withCallback)
		else:
			self.openMultiServiceEPGSilent(bouquets, cnt, withCallback)

	def openMultiServiceEPGAskBouquet(self, bouquets, cnt, withCallback):
		if cnt > 1: # show bouquet list
			if withCallback:
				self.bouquetSel = self.session.openWithCallback(self.closed, BouquetSelector, bouquets, self.openBouquetEPG, enableWrapAround=True)
				self.dlg_stack.append(self.bouquetSel)
			else:
				self.bouquetSel = self.session.open(BouquetSelector, bouquets, self.openBouquetEPG, enableWrapAround=True)
		elif cnt == 1:
			self.openBouquetEPG(bouquets[0][1], withCallback)

	def openMultiServiceEPGSilent(self, bouquets, cnt, withCallback):
		root = self.servicelist.getRoot()
		rootstr = root.toCompareString()
		current = 0
		for bouquet in bouquets:
			if bouquet[1].toCompareString() == rootstr:
				break
			current += 1
		if current >= cnt:
			current = 0
		if cnt > 1: # create bouquet list for bouq+/-
			self.bouquetSel = SilentBouquetSelector(bouquets, True, self.servicelist.getBouquetNumOffset(root))
		if cnt >= 1:
			self.openBouquetEPG(root, withCallback)

	def changeServiceCB(self, direction, epg):
		if self.serviceSel:
			if direction > 0:
				self.serviceSel.nextService()
			else:
				self.serviceSel.prevService()
			epg.setService(self.serviceSel.currentService())

	def SingleServiceEPGClosed(self, ret=False):
		self.serviceSel = None

	def openSingleServiceEPG(self):
		ref = self.servicelist.getCurrentSelection()
		if ref:
			if self.servicelist.getMutableList(): # bouquet in channellist
				current_path = self.servicelist.getRoot()
				services = self.getBouquetServices(current_path)
				self.serviceSel = SimpleServicelist(services)
				if self.serviceSel.selectService(ref):
					self.epg_bouquet = current_path
					self.session.openWithCallback(self.SingleServiceEPGClosed, EPGSelection, ref, self.zapToService, serviceChangeCB=self.changeServiceCB, parent=self)
				else:
					self.session.openWithCallback(self.SingleServiceEPGClosed, EPGSelection, ref)
			else:
				self.session.open(EPGSelection, ref)

	def runPlugin(self, plugin):
		plugin(session=self.session, servicelist=self.servicelist)

	def showEventInfoPlugins(self):
		pluginlist = self.getEPGPluginList()
		if pluginlist:
			pluginlist.append((_("Select default EPG type..."), self.SelectDefaultInfoPlugin))
			self.session.openWithCallback(self.EventInfoPluginChosen, ChoiceBox, title=_("Please choose an extension..."), list=pluginlist, skin_name="EPGExtensionsList")
		else:
			self.openSingleServiceEPG()

	def EventInfoPluginChosen(self, answer):
		if answer is not None:
			answer[1]()

	def SelectDefaultInfoPlugin(self):
		self.session.openWithCallback(self.DefaultInfoPluginChosen, ChoiceBox, title=_("Please select a default EPG type..."), list=self.getEPGPluginList(True), skin_name="EPGExtensionsList")

	def DefaultInfoPluginChosen(self, answer):
		if answer is not None:
			self.defaultEPGType = answer[1]
			config.usage.defaultEPGType.value = answer[2]
			config.usage.defaultEPGType.save()

	def showEventGuidePlugins(self):
		pluginlist = self.getEPGPluginList()
		if pluginlist:
			pluginlist.append((_("Select default EPG type..."), self.SelectDefaultGuidePlugin))
			self.session.openWithCallback(self.EventGuidePluginChosen, ChoiceBox, title=_("Please choose an extension..."), list=pluginlist, skin_name="EPGExtensionsList")
		else:
			self.openSingleServiceEPG()

	def EventGuidePluginChosen(self, answer):
		if answer is not None:
			answer[1]()

	def SelectDefaultGuidePlugin(self):
		self.session.openWithCallback(self.DefaultGuidePluginChosen, ChoiceBox, title=_("Please select a default EPG type..."), list=self.getEPGPluginList(True), skin_name="EPGExtensionsList")

	def DefaultGuidePluginChosen(self, answer):
		if answer is not None:
			self.defaultGuideType = answer[1]
			config.usage.defaultGuideType.value = answer[2] + "@" + answer[0]
			config.usage.defaultGuideType.save()

	def openSimilarList(self, eventid, refstr):
		self.session.open(EPGSelection, refstr, None, eventid)

	def getNowNext(self):
		epglist = [ ]
		service = self.session.nav.getCurrentService()
		info = service and service.info()
		ptr = info and info.getEvent(0)
		if ptr and ptr.getEventName() != "":
			epglist.append(ptr)
		ptr = info and info.getEvent(1)
		if ptr and ptr.getEventName() != "":
			epglist.append(ptr)
		self.epglist = epglist

	def __evEventInfoChanged(self):
		if self.is_now_next and len(self.dlg_stack) == 1:
			self.getNowNext()
			if self.eventView and self.epglist:
				self.eventView.setEvent(self.epglist[0])

	def showDefaultEPG(self):
		if self.defaultEPGType:
			self.defaultEPGType()
		else:
			self.openEventView()

	def showSingleEPG(self):
		if self.defaultGuideType:
			self.defaultGuideType()
		else:
			self.openSingleServiceEPG()

	def showMultiEPG(self):
		if self.defaultGuideType:
			self.defaultGuideType()
		else:
			self.openMultiServiceEPG()

	def openEventView(self):
		from Components.ServiceEventTracker import InfoBarCount
		if InfoBarCount > 1:
			epglist = [ ]
			self.epglist = epglist
			service = self.session.nav.getCurrentService()
			ref = self.session.nav.getCurrentlyPlayingServiceOrGroup()
			info = service.info()
			ptr=info.getEvent(0)
			if ptr:
				epglist.append(ptr)
			ptr=info.getEvent(1)
			if ptr:
				epglist.append(ptr)
			if epglist:
				self.session.open(EventViewEPGSelect, epglist[0], ServiceReference(ref), self.eventViewCallback, self.openSingleServiceEPG, self.openMultiServiceEPG, self.openSimilarList)
		else:
			ref = self.session.nav.getCurrentlyPlayingServiceOrGroup()
			self.getNowNext()
			epglist = self.epglist
			if not epglist:
				self.is_now_next = False
				epg = eEPGCache.getInstance()
				ptr = ref and ref.valid() and epg.lookupEventTime(ref, -1)
				if ptr:
					epglist.append(ptr)
					ptr = epg.lookupEventTime(ref, ptr.getBeginTime(), +1)
					if ptr:
						epglist.append(ptr)
			else:
				self.is_now_next = True
			if epglist:
				self.eventView = self.session.openWithCallback(self.closed, EventViewEPGSelect, epglist[0], ServiceReference(ref), self.eventViewCallback, self.openSingleServiceEPG, self.openMultiServiceEPG, self.openSimilarList)
				self.dlg_stack.append(self.eventView)
		if not epglist:
			print "no epg for the service avail.. so we show multiepg instead of eventinfo"
			self.openMultiServiceEPG(False)

	def eventViewCallback(self, setEvent, setService, val): #used for now/next displaying
		epglist = self.epglist
		if len(epglist) > 1:
			tmp = epglist[0]
			epglist[0]=epglist[1]
			epglist[1]=tmp
			setEvent(epglist[0])

class InfoBarRdsDecoder:
	"""provides RDS and Rass support/display"""
	def __init__(self):
		self.rds_display = self.session.instantiateDialog(RdsInfoDisplay)
		self.session.instantiateSummaryDialog(self.rds_display)
		self.rds_display.setAnimationMode(0)
		self.rass_interactive = None

		self.__event_tracker = ServiceEventTracker(screen=self, eventmap={
				iPlayableService.evEnd: self.__serviceStopped,
				iPlayableService.evUpdatedRassSlidePic: self.RassSlidePicChanged
			})

		self["RdsActions"] = ActionMap(["InfobarRdsActions"],
		{
			"startRassInteractive": self.startRassInteractive
		},-1)

		self["RdsActions"].setEnabled(False)

		self.onLayoutFinish.append(self.rds_display.show)
		self.rds_display.onRassInteractivePossibilityChanged.append(self.RassInteractivePossibilityChanged)

	def RassInteractivePossibilityChanged(self, state):
		self["RdsActions"].setEnabled(state)

	def RassSlidePicChanged(self):
		if not self.rass_interactive:
			service = self.session.nav.getCurrentService()
			decoder = service and service.rdsDecoder()
			if decoder:
				decoder.showRassSlidePicture()

	def __serviceStopped(self):
		if self.rass_interactive is not None:
			rass_interactive = self.rass_interactive
			self.rass_interactive = None
			rass_interactive.close()

	def startRassInteractive(self):
		self.rds_display.hide()
		self.rass_interactive = self.session.openWithCallback(self.RassInteractiveClosed, RassInteractive)

	def RassInteractiveClosed(self, *val):
		if self.rass_interactive is not None:
			self.rass_interactive = None
			self.RassSlidePicChanged()
		self.rds_display.show()

class Seekbar(Screen):
	def __init__(self, session, fwd):
		Screen.__init__(self, session)
		self.setTitle(_("Seek"))
		self.session = session
		self.fwd = fwd
		self.percent = 0.0
		self.length = None
		service = session.nav.getCurrentService()
		if service:
			self.seek = service.seek()
			if self.seek:
				self.length = self.seek.getLength()
				position = self.seek.getPlayPosition()
				if self.length and position and int(self.length[1]) > 0:
					if int(position[1]) > 0:
						self.percent = float(position[1]) * 100.0 / float(self.length[1])
				else:
					self.close()

		self["cursor"] = MovingPixmap()
		self["time"] = Label()

		self["actions"] = ActionMap(["WizardActions", "DirectionActions"], {"back": self.exit, "ok": self.keyOK, "left": self.keyLeft, "right": self.keyRight}, -1)

		self.cursorTimer = eTimer()
		self.cursorTimer.callback.append(self.updateCursor)
		self.cursorTimer.start(200, False)

	def updateCursor(self):
		if self.length:
			screenwidth = getDesktop(0).size().width()
			if screenwidth and screenwidth == 1920:
				x = 218 + int(4.05 * self.percent)
				self["cursor"].moveTo(x, 23, 1)
			else:
				x = 145 + int(2.7 * self.percent)
				self["cursor"].moveTo(x, 15, 1)
			self["cursor"].startMoving()
			pts = int(float(self.length[1]) / 100.0 * self.percent)
			self["time"].setText("%d:%02d" % ((pts/60/90000), ((pts/90000)%60)))

	def exit(self):
		self.cursorTimer.stop()
		self.close()

	def keyOK(self):
		if self.length:
			self.seek.seekTo(int(float(self.length[1]) / 100.0 * self.percent))
			self.exit()

	def keyLeft(self):
		self.percent -= float(config.seek.sensibility.value) / 10.0
		if self.percent < 0.0:
			self.percent = 0.0

	def keyRight(self):
		self.percent += float(config.seek.sensibility.value) / 10.0
		if self.percent > 100.0:
			self.percent = 100.0

	def keyNumberGlobal(self, number):
		sel = self["config"].getCurrent()[1]
		if sel == self.positionEntry:
			self.percent = float(number) * 10.0
		else:
			ConfigListScreen.keyNumberGlobal(self, number)

class InfoBarSeek:
	"""handles actions like seeking, pause"""

	SEEK_STATE_PLAY = (0, 0, 0, ">")
	SEEK_STATE_PAUSE = (1, 0, 0, "||")
	SEEK_STATE_EOF = (1, 0, 0, "END")

	def __init__(self, actionmap="InfobarSeekActions"):
		self.__event_tracker = ServiceEventTracker(screen=self, eventmap={
				iPlayableService.evSeekableStatusChanged: self.__seekableStatusChanged,
				iPlayableService.evStart: self.__serviceStarted,
				iPlayableService.evEOF: self.__evEOF,
				iPlayableService.evSOF: self.__evSOF,
			})
		self.fast_winding_hint_message_showed = False

		class InfoBarSeekActionMap(HelpableActionMap):
			def __init__(self, screen, *args, **kwargs):
				HelpableActionMap.__init__(self, screen, *args, **kwargs)
				self.screen = screen

			def action(self, contexts, action):
				# print "action:", action
				if action[:5] == "seek:":
					time = int(action[5:])
					self.screen.doSeekRelative(time * 90000)
					return 1
				elif action[:8] == "seekdef:":
					key = int(action[8:])
					time = (-config.seek.selfdefined_13.value, False, config.seek.selfdefined_13.value,
						-config.seek.selfdefined_46.value, False, config.seek.selfdefined_46.value,
						-config.seek.selfdefined_79.value, False, config.seek.selfdefined_79.value)[key-1]
					self.screen.doSeekRelative(time * 90000)
					return 1
				else:
					return HelpableActionMap.action(self, contexts, action)

		self["SeekActions"] = InfoBarSeekActionMap(self, actionmap,
			{
				"playpauseService": (self.playpauseService, _("Pause/Continue playback")),
				"pauseService": (self.pauseService, _("Pause playback")),
				"pauseServiceYellow": (self.pauseServiceYellow, _("Pause playback")),
				"unPauseService": (self.unPauseService, _("Continue playback")),
				"okButton": (self.okButton, _("Continue playback")),

				"seekFwd": (self.seekFwd, _("Seek forward")),
				"seekFwdManual": (self.seekFwdManual, _("Seek forward (enter time)")),
				"seekBack": (self.seekBack, _("Seek backward")),
				"seekBackManual": (self.seekBackManual, _("Seek backward (enter time)")),

				"SeekbarFwd": self.seekFwdSeekbar,
				"SeekbarBack": self.seekBackSeekbar
			}, prio=-1) # give them a little more priority to win over color buttons
		self["SeekActions"].setEnabled(False)

		self["SeekActionsPTS"] = InfoBarSeekActionMap(self, "InfobarSeekActionsPTS",
			{
				"playpauseService": self.playpauseService,
				"pauseService": (self.pauseService, _("Pause playback")),
				"pauseServiceYellow": (self.pauseServiceYellow, _("Pause playback")),
				"unPauseService": (self.unPauseService, _("Continue playback")),

				"seekFwd": (self.seekFwd, _("skip forward")),
				"seekFwdManual": (self.seekFwdManual, _("skip forward (enter time)")),
				"seekBack": (self.seekBack, _("skip backward")),
				"seekBackManual": (self.seekBackManual, _("skip backward (enter time)")),
			}, prio=-1) # give them a little more priority to win over color buttons
		self["SeekActionsPTS"].setEnabled(False)

		self.activity = 0
		self.activityTimer = eTimer()
		self.activityTimer.callback.append(self.doActivityTimer)
		self.seekstate = self.SEEK_STATE_PLAY
		self.lastseekstate = self.SEEK_STATE_PLAY
		self.seekAction = 0
		self.LastseekAction = False

		self.onPlayStateChanged = [ ]

		self.lockedBecauseOfSkipping = False

		self.__seekableStatusChanged()

	def makeStateForward(self, n):
		return (0, n, 0, ">> %dx" % n)

	def makeStateBackward(self, n):
		return (0, -n, 0, "<< %dx" % n)

	def makeStateSlowMotion(self, n):
		return (0, 0, n, "/%d" % n)

	def isStateForward(self, state):
		return state[1] > 1

	def isStateBackward(self, state):
		return state[1] < 0

	def isStateSlowMotion(self, state):
		return state[1] == 0 and state[2] > 1

	def getHigher(self, n, lst):
		for x in lst:
			if x > n:
				return x
		return False

	def getLower(self, n, lst):
		lst = lst[:]
		lst.reverse()
		for x in lst:
			if x < n:
				return x
		return False

	def showAfterSeek(self):
		if isinstance(self, InfoBarShowHide):
			self.doShow()

	def up(self):
		pass

	def down(self):
		pass

	def getSeek(self):
		service = self.session.nav.getCurrentService()
		if service is None:
			return None

		seek = service.seek()

		if seek is None or not seek.isCurrentlySeekable():
			return None

		return seek

	def isSeekable(self):
		if self.getSeek() is None or (isStandardInfoBar(self) and not self.timeshiftEnabled()):
			return False
		return True

	def __seekableStatusChanged(self):
		if isStandardInfoBar(self) and self.timeshiftEnabled():
			pass
		elif not self.isSeekable():
			SystemInfo["SeekStatePlay"] = False
			if os.path.exists("/proc/stb/lcd/symbol_hdd"):
				f = open("/proc/stb/lcd/symbol_hdd", "w")
				f.write("0")
				f.close()        
			if os.path.exists("/proc/stb/lcd/symbol_hddprogress"):  
				f = open("/proc/stb/lcd/symbol_hddprogress", "w")
				f.write("0")
				f.close()
#			print "not seekable, return to play"
			self["SeekActions"].setEnabled(False)
			self.setSeekState(self.SEEK_STATE_PLAY)
		else:
#			print "seekable"
			self["SeekActions"].setEnabled(True)
			self.activityTimer.start(int(config.seek.withjumps_repeat_ms.getValue()), False)
			for c in self.onPlayStateChanged:
				c(self.seekstate)

		global seek_withjumps_muted
		if seek_withjumps_muted and eDVBVolumecontrol.getInstance().isMuted():
			print "STILL MUTED AFTER FFWD/FBACK !!!!!!!! so we unMute"
			seek_withjumps_muted = False
			eDVBVolumecontrol.getInstance().volumeUnMute()

	def doActivityTimer(self):
		if self.isSeekable():
			self.activity += 16
			hdd = 1
			if self.activity >= 100:
				self.activity = 0
			SystemInfo["SeekStatePlay"] = True
			if os.path.exists("/proc/stb/lcd/symbol_hdd"):
				if config.lcd.hdd.value == "1":
					file = open("/proc/stb/lcd/symbol_hdd", "w")
					file.write('%d' % int(hdd))
					file.close()
			if os.path.exists("/proc/stb/lcd/symbol_hddprogress"):
				if config.lcd.hdd.value == "1":
					file = open("/proc/stb/lcd/symbol_hddprogress", "w")
					file.write('%d' % int(self.activity))
					file.close() 
		else:
			self.activityTimer.stop()
			self.activity = 0
			hdd = 0
			self.seekAction = 0

		SystemInfo["SeekStatePlay"] = True
		if os.path.exists("/proc/stb/lcd/symbol_hdd"):
			if config.lcd.hdd.value == "1":
				file = open("/proc/stb/lcd/symbol_hdd", "w")
				file.write('%d' % int(hdd))
				file.close()
		if os.path.exists("/proc/stb/lcd/symbol_hddprogress"):
			if config.lcd.hdd.value == "1":
				file = open("/proc/stb/lcd/symbol_hddprogress", "w")
				file.write('%d' % int(self.activity))
				file.close()
		if self.LastseekAction:
			self.DoSeekAction()

	def __serviceStarted(self):
		self.fast_winding_hint_message_showed = False
		self.setSeekState(self.SEEK_STATE_PLAY)
		self.__seekableStatusChanged()

	def setSeekState(self, state):
		service = self.session.nav.getCurrentService()

		if service is None:
			return False

		if not self.isSeekable():
			if state not in (self.SEEK_STATE_PLAY, self.SEEK_STATE_PAUSE):
				state = self.SEEK_STATE_PLAY

		pauseable = service.pause()

		if pauseable is None:
#			print "not pauseable."
			state = self.SEEK_STATE_PLAY

		self.seekstate = state

		if pauseable is not None:
			if self.seekstate[0] and self.seekstate[3] == '||':
#				print "resolved to PAUSE"
				self.activityTimer.stop()
				pauseable.pause()
			elif self.seekstate[0] and self.seekstate[3] == 'END':
#				print "resolved to STOP"
				self.activityTimer.stop()
			elif self.seekstate[1]:
				if not pauseable.setFastForward(self.seekstate[1]):
					pass
					# print "resolved to FAST FORWARD"
				else:
					self.seekstate = self.SEEK_STATE_PLAY
					# print "FAST FORWARD not possible: resolved to PLAY"
			elif self.seekstate[2]:
				if not pauseable.setSlowMotion(self.seekstate[2]):
					pass
					# print "resolved to SLOW MOTION"
				else:
					self.seekstate = self.SEEK_STATE_PAUSE
					# print "SLOW MOTION not possible: resolved to PAUSE"
			else:
#				print "resolved to PLAY"
				self.activityTimer.start(int(config.seek.withjumps_repeat_ms.getValue()), False)
				pauseable.unpause()

		for c in self.onPlayStateChanged:
			c(self.seekstate)

		self.checkSkipShowHideLock()

		if hasattr(self, "ScreenSaverTimerStart"):
			self.ScreenSaverTimerStart()

		return True

	def okButton(self):
		if self.seekstate == self.SEEK_STATE_PLAY:
			return 0
		elif self.seekstate == self.SEEK_STATE_PAUSE:
			self.pauseService()
		else:
			self.unPauseService()

	def playpauseService(self):
		if self.seekAction <> 0:
			self.seekAction = 0
			self.doPause(False)
			global seek_withjumps_muted
			seek_withjumps_muted = False
			return
		if self.seekstate == self.SEEK_STATE_PLAY:
			self.pauseService()
		else:
			if self.seekstate == self.SEEK_STATE_PAUSE:
				if config.seek.on_pause.value == "play":
					self.unPauseService()
				elif config.seek.on_pause.value == "step":
					self.doSeekRelative(1)
				elif config.seek.on_pause.value == "last":
					self.setSeekState(self.lastseekstate)
					self.lastseekstate = self.SEEK_STATE_PLAY
			else:
				self.unPauseService()

	def pauseService(self):
		SystemInfo["StatePlayPause"] = True
		if self.seekstate != self.SEEK_STATE_EOF:
			self.lastseekstate = self.seekstate
		self.setSeekState(self.SEEK_STATE_PAUSE)

	def pauseServiceYellow(self):
		if config.usage.on_short_yellow_key.value == '0':
			self.audioSelection()
		elif config.usage.on_short_yellow_key.value == '2':
			ToggleVideo()
		else:
			self.playpauseService()

	def unPauseService(self):
		SystemInfo["StatePlayPause"] = False
		if self.seekstate == self.SEEK_STATE_PLAY:
			if self.seekAction <> 0:
				self.playpauseService()
			#return 0 # if 'return 0', plays timeshift again from the beginning
			return
		self.doPause(False)
		self.setSeekState(self.SEEK_STATE_PLAY)
		if config.usage.show_infobar_on_skip.value and not config.usage.show_infobar_locked_on_pause.value:
			self.showAfterSeek()
		self.skipToggleShow = True # skip 'break' action (toggleShow) after 'make' action (unPauseService)

	def doPause(self, pause):
		if pause:
			if not eDVBVolumecontrol.getInstance().isMuted():
				eDVBVolumecontrol.getInstance().volumeMute()
		else:
			if eDVBVolumecontrol.getInstance().isMuted():
				eDVBVolumecontrol.getInstance().volumeUnMute()

	def doSeek(self, pts):
		seekable = self.getSeek()
		if seekable is None:
			return
		seekable.seekTo(pts)

	def doSeekRelativeAvoidStall(self, pts):
		global jump_pts_adder
		global jump_last_pts
		global jump_last_pos
		seekable = self.getSeek()
		#when config.seek.withjumps, avoid that jumps smaller than the time between I-frames result in hanging, by increasing pts when stalled
		if seekable and config.seek.withjumps_avoid_zero.getValue():
			position = seekable.getPlayPosition()
			if jump_last_pos and jump_last_pts:
				if (abs(position[1] - jump_last_pos[1]) < 100*90) and (pts == jump_last_pts): # stalled?
					jump_pts_adder += pts
					jump_last_pts = pts
					pts += jump_pts_adder
				else:
					jump_pts_adder = 0
					jump_last_pts = pts
			else:
				jump_last_pts = pts
			jump_last_pos = position
		self.doSeekRelative(pts)

	def doSeekRelative(self, pts):
		try:
			if "<class 'Screens.InfoBar.InfoBar'>" in `self`:
				if InfoBarTimeshift.timeshiftEnabled(self):
					length = InfoBarTimeshift.ptsGetLength(self)
					position = InfoBarTimeshift.ptsGetPosition(self)
					if length is None or position is None:
						return
					if position + pts >= length:
						InfoBarTimeshift.evEOF(self, position + pts - length)
						self.showAfterSeek()
						return
					elif position + pts < 0:
						InfoBarTimeshift.evSOF(self, position + pts)
						self.showAfterSeek()
						return
		except:
			from sys import exc_info
			print "[InfoBarGenerics] error in 'def doSeekRelative'", exc_info()[:2]

		seekable = self.getSeek()
		if seekable is None or int(seekable.getLength()[1]) < 1:
			return
		prevstate = self.seekstate

		if self.seekstate == self.SEEK_STATE_EOF:
			if prevstate == self.SEEK_STATE_PAUSE:
				self.setSeekState(self.SEEK_STATE_PAUSE)
			else:
				self.setSeekState(self.SEEK_STATE_PLAY)
		seekable.seekRelative(pts<0 and -1 or 1, abs(pts))
		if (abs(pts) > 100 or not config.usage.show_infobar_locked_on_pause.value) and config.usage.show_infobar_on_skip.value:
			self.showAfterSeek()

	def DoSeekAction(self):
		if self.seekAction > int(config.seek.withjumps_after_ff_speed.getValue()):
			self.doSeekRelativeAvoidStall(self.seekAction * long(config.seek.withjumps_forwards_ms.getValue()) * 90)
		elif self.seekAction < 0:
			self.doSeekRelativeAvoidStall(self.seekAction * long(config.seek.withjumps_backwards_ms.getValue()) * 90)

		for c in self.onPlayStateChanged:
			if self.seekAction > int(config.seek.withjumps_after_ff_speed.getValue()): # Forward
				c((0, self.seekAction, 0, ">> %dx" % self.seekAction))
			elif self.seekAction < 0: # Backward
				c((0, self.seekAction, 0, "<< %dx" % abs(self.seekAction)))

		if self.seekAction == 0:
			self.LastseekAction = False
			self.doPause(False)
			global seek_withjumps_muted
			seek_withjumps_muted = False
			self.setSeekState(self.SEEK_STATE_PLAY)

	def isServiceTypeTS(self):
		ref = self.session.nav.getCurrentlyPlayingServiceReference()
		isTS = False
		if ref is not None:
			servincetype = ServiceReference(ref).getType()
			if servincetype == 1:
				isTS = True
		return isTS

	def seekFwd(self):
		if config.seek.withjumps.value and not self.isServiceTypeTS():
			self.seekFwd_new()
		else:
			self.seekFwd_old()

	def seekBack(self):
		if config.seek.withjumps.value and not self.isServiceTypeTS():
			self.seekBack_new()
		else:
			self.seekBack_old()

	def seekFwd_new(self):
		self.LastseekAction = True
		self.doPause(True)
		global seek_withjumps_muted
		seek_withjumps_muted = True
		if self.seekAction >= 0:
			self.seekAction = self.getHigher(abs(self.seekAction), config.seek.speeds_forward.value) or config.seek.speeds_forward.value[-1]
		else:
			self.seekAction = -self.getLower(abs(self.seekAction), config.seek.speeds_backward.value)
		if (self.seekAction > 1) and (self.seekAction <= int(config.seek.withjumps_after_ff_speed.getValue())): # use fastforward for the configured speeds
			self.setSeekState(self.makeStateForward(self.seekAction))
		elif self.seekAction > int(config.seek.withjumps_after_ff_speed.getValue()): # we first need to go the play state, to stop fastforward
			self.setSeekState(self.SEEK_STATE_PLAY)

	def seekBack_new(self):
		self.LastseekAction = True
		self.doPause(True)
		global seek_withjumps_muted
		seek_withjumps_muted = True
		if self.seekAction <= 0:
			self.seekAction = -self.getHigher(abs(self.seekAction), config.seek.speeds_backward.value) or -config.seek.speeds_backward.value[-1]
		else:
			self.seekAction = self.getLower(abs(self.seekAction), config.seek.speeds_forward.value)
		if (self.seekAction > 1) and (self.seekAction <= int(config.seek.withjumps_after_ff_speed.getValue())): # use fastforward for the configured forwards speeds
			self.setSeekState(self.makeStateForward(self.seekAction))

	def seekFwd_old(self):
		seek = self.getSeek()
		if seek and not (seek.isCurrentlySeekable() & 2):
			if not self.fast_winding_hint_message_showed and (seek.isCurrentlySeekable() & 1):
				self.session.open(MessageBox, _("No fast winding possible yet.. but you can use the number buttons to skip forward/backward!"), MessageBox.TYPE_INFO, timeout=10)
				self.fast_winding_hint_message_showed = True
				return
			return 0 # trade as unhandled action
		if self.seekstate == self.SEEK_STATE_PLAY:
			self.setSeekState(self.makeStateForward(int(config.seek.enter_forward.value)))
		elif self.seekstate == self.SEEK_STATE_PAUSE:
			if len(config.seek.speeds_slowmotion.value):
				self.setSeekState(self.makeStateSlowMotion(config.seek.speeds_slowmotion.value[-1]))
			else:
				self.setSeekState(self.makeStateForward(int(config.seek.enter_forward.value)))
		elif self.seekstate == self.SEEK_STATE_EOF:
			pass
		elif self.isStateForward(self.seekstate):
			speed = self.seekstate[1]
			if self.seekstate[2]:
				speed /= self.seekstate[2]
			speed = self.getHigher(speed, config.seek.speeds_forward.value) or config.seek.speeds_forward.value[-1]
			self.setSeekState(self.makeStateForward(speed))
		elif self.isStateBackward(self.seekstate):
			speed = -self.seekstate[1]
			if self.seekstate[2]:
				speed /= self.seekstate[2]
			speed = self.getLower(speed, config.seek.speeds_backward.value)
			if speed:
				self.setSeekState(self.makeStateBackward(speed))
			else:
				self.setSeekState(self.SEEK_STATE_PLAY)
		elif self.isStateSlowMotion(self.seekstate):
			speed = self.getLower(self.seekstate[2], config.seek.speeds_slowmotion.value) or config.seek.speeds_slowmotion.value[0]
			self.setSeekState(self.makeStateSlowMotion(speed))

	def seekBack_old(self):
		seek = self.getSeek()
		if seek and not (seek.isCurrentlySeekable() & 2):
			if not self.fast_winding_hint_message_showed and (seek.isCurrentlySeekable() & 1):
				self.session.open(MessageBox, _("No fast winding possible yet.. but you can use the number buttons to skip forward/backward!"), MessageBox.TYPE_INFO, timeout=10)
				self.fast_winding_hint_message_showed = True
				return
			return 0 # trade as unhandled action
		seekstate = self.seekstate
		if seekstate == self.SEEK_STATE_PLAY:
			self.setSeekState(self.makeStateBackward(int(config.seek.enter_backward.value)))
		elif seekstate == self.SEEK_STATE_EOF:
			self.setSeekState(self.makeStateBackward(int(config.seek.enter_backward.value)))
			self.doSeekRelative(-6)
		elif seekstate == self.SEEK_STATE_PAUSE:
			self.doSeekRelative(-1)
		elif self.isStateForward(seekstate):
			speed = seekstate[1]
			if seekstate[2]:
				speed /= seekstate[2]
			speed = self.getLower(speed, config.seek.speeds_forward.value)
			if speed:
				self.setSeekState(self.makeStateForward(speed))
			else:
				self.setSeekState(self.SEEK_STATE_PLAY)
		elif self.isStateBackward(seekstate):
			speed = -seekstate[1]
			if seekstate[2]:
				speed /= seekstate[2]
			speed = self.getHigher(speed, config.seek.speeds_backward.value) or config.seek.speeds_backward.value[-1]
			self.setSeekState(self.makeStateBackward(speed))
		elif self.isStateSlowMotion(seekstate):
			speed = self.getHigher(seekstate[2], config.seek.speeds_slowmotion.value)
			if speed:
				self.setSeekState(self.makeStateSlowMotion(speed))
			else:
				self.setSeekState(self.SEEK_STATE_PAUSE)
		self.pts_lastseekspeed = self.seekstate[1]

	def seekFwdManual(self, fwd=True):
		if config.seek.baractivation.value == "leftright":
			self.session.open(Seekbar, fwd)
		else:
			self.session.openWithCallback(self.fwdSeekTo, MinuteInput)

	def seekBackManual(self, fwd=False):
		if config.seek.baractivation.value == "leftright":
			self.session.open(Seekbar, fwd)
		else:
			self.session.openWithCallback(self.rwdSeekTo, MinuteInput)

	def seekFwdVod(self, fwd=True):
		seekable = self.getSeek()
		if seekable is None:
			return
		else:
			if config.seek.baractivation.value == "leftright":
				self.session.open(Seekbar, fwd)
			else:
				self.session.openWithCallback(self.fwdSeekTo, MinuteInput)

	def seekFwdSeekbar(self, fwd=True):
		if not config.seek.baractivation.value == "leftright":
			self.session.open(Seekbar, fwd)
		else:
			self.session.openWithCallback(self.fwdSeekTo, MinuteInput)

	def fwdSeekTo(self, minutes):
		self.doSeekRelative(minutes * 60 * 90000)

	def seekBackSeekbar(self, fwd=False):
		if not config.seek.baractivation.value == "leftright":
			self.session.open(Seekbar, fwd)
		else:
			self.session.openWithCallback(self.rwdSeekTo, MinuteInput)

	def rwdSeekTo(self, minutes):
#		print "rwdSeekTo"
		self.doSeekRelative(-minutes * 60 * 90000)

	def checkSkipShowHideLock(self):
		if self.seekstate == self.SEEK_STATE_PLAY or self.seekstate == self.SEEK_STATE_EOF:
			self.lockedBecauseOfSkipping = False
			self.unlockShow()
		elif self.seekstate == self.SEEK_STATE_PAUSE and not config.usage.show_infobar_locked_on_pause.value:
			if config.usage.show_infobar_on_skip.value:
				self.lockedBecauseOfSkipping = False
				self.unlockShow()
				self.showAfterSeek()
		else:
			wantlock = self.seekstate != self.SEEK_STATE_PLAY
			if config.usage.show_infobar_on_skip.value:
				if self.lockedBecauseOfSkipping and not wantlock:
					self.unlockShow()
					self.lockedBecauseOfSkipping = False

				if wantlock and not self.lockedBecauseOfSkipping:
					self.lockShow()
					self.lockedBecauseOfSkipping = True

	def calcRemainingTime(self):
		seekable = self.getSeek()
		if seekable is not None:
			len = seekable.getLength()
			try:
				tmp = self.cueGetEndCutPosition()
				if tmp:
					len = (False, tmp)
			except:
				pass
			pos = seekable.getPlayPosition()
			speednom = self.seekstate[1] or 1
			speedden = self.seekstate[2] or 1
			if not len[0] and not pos[0]:
				if len[1] <= pos[1]:
					return 0
				time = (len[1] - pos[1])*speedden/(90*speednom)
				return time
		return False

	def __evEOF(self):
		if self.seekstate == self.SEEK_STATE_EOF:
			return

		global seek_withjumps_muted
		if seek_withjumps_muted and eDVBVolumecontrol.getInstance().isMuted():
			print "STILL MUTED AFTER FFWD/FBACK !!!!!!!! so we unMute"
			seek_withjumps_muted = False
			eDVBVolumecontrol.getInstance().volumeUnMute()

		# if we are seeking forward, we try to end up ~1s before the end, and pause there.
		seekstate = self.seekstate
		if self.seekstate != self.SEEK_STATE_PAUSE:
			self.setSeekState(self.SEEK_STATE_EOF)

		if seekstate not in (self.SEEK_STATE_PLAY, self.SEEK_STATE_PAUSE): # if we are seeking
			seekable = self.getSeek()
			if seekable is not None:
				seekable.seekTo(-1)
				self.doEofInternal(True)
		if seekstate == self.SEEK_STATE_PLAY: # regular EOF
			self.doEofInternal(True)
		else:
			self.doEofInternal(False)

	def doEofInternal(self, playing):
		pass		# Defined in subclasses

	def __evSOF(self):
		self.setSeekState(self.SEEK_STATE_PLAY)
		self.doSeek(0)

class InfoBarPVRState:
	def __init__(self, screen=PVRState, force_show=False):
		self.onChangedEntry = [ ]
		self.onPlayStateChanged.append(self.__playStateChanged)
		self.pvrStateDialog = self.session.instantiateDialog(screen)
		self.pvrStateDialog.setAnimationMode(0)
		self.onShow.append(self._mayShow)
		self.onHide.append(self.pvrStateDialog.hide)
		self.force_show = force_show

	def createSummary(self):
		return InfoBarMoviePlayerSummary

	def _mayShow(self):
		if self.has_key("state") and not config.usage.movieplayer_pvrstate.value:
			self["state"].setText("")
			self["statusicon"].setPixmapNum(6)
			self["speed"].setText("")
		if self.shown and self.seekstate != self.SEEK_STATE_EOF and not config.usage.movieplayer_pvrstate.value:
			self.DimmingTimer.stop()
			self.doWriteAlpha(config.av.osd_alpha.value)
			self.pvrStateDialog.show()
			self.startHideTimer()

	def __playStateChanged(self, state):
		playstateString = state[3]
		state_summary = playstateString
		if self.pvrStateDialog.has_key("statusicon"):
			self.pvrStateDialog["state"].setText(playstateString)
			if playstateString == '>':
				self.pvrStateDialog["statusicon"].setPixmapNum(0)
				self.pvrStateDialog["speed"].setText("")
				speed_summary = self.pvrStateDialog["speed"].text
				statusicon_summary = 0
				if self.has_key("state") and config.usage.movieplayer_pvrstate.value:
					self["state"].setText(playstateString)
					self["statusicon"].setPixmapNum(0)
					self["speed"].setText("")
			elif playstateString == '||':
				self.pvrStateDialog["statusicon"].setPixmapNum(1)
				self.pvrStateDialog["speed"].setText("")
				speed_summary = self.pvrStateDialog["speed"].text
				statusicon_summary = 1
				if self.has_key("state") and config.usage.movieplayer_pvrstate.value:
					self["state"].setText(playstateString)
					self["statusicon"].setPixmapNum(1)
					self["speed"].setText("")
			elif playstateString == 'END':
				self.pvrStateDialog["statusicon"].setPixmapNum(2)
				self.pvrStateDialog["speed"].setText("")
				speed_summary = self.pvrStateDialog["speed"].text
				statusicon_summary = 2
				if self.has_key("state") and config.usage.movieplayer_pvrstate.value:
					self["state"].setText(playstateString)
					self["statusicon"].setPixmapNum(2)
					self["speed"].setText("")
			elif playstateString.startswith('>>'):
				speed = state[3].split()
				self.pvrStateDialog["statusicon"].setPixmapNum(3)
				self.pvrStateDialog["speed"].setText(speed[1])
				speed_summary = self.pvrStateDialog["speed"].text
				statusicon_summary = 3
				if self.has_key("state") and config.usage.movieplayer_pvrstate.value:
					self["state"].setText(playstateString)
					self["statusicon"].setPixmapNum(3)
					self["speed"].setText(speed[1])
			elif playstateString.startswith('<<'):
				speed = state[3].split()
				self.pvrStateDialog["statusicon"].setPixmapNum(4)
				self.pvrStateDialog["speed"].setText(speed[1])
				speed_summary = self.pvrStateDialog["speed"].text
				statusicon_summary = 4
				if self.has_key("state") and config.usage.movieplayer_pvrstate.value:
					self["state"].setText(playstateString)
					self["statusicon"].setPixmapNum(4)
					self["speed"].setText(speed[1])
			elif playstateString.startswith('/'):
				self.pvrStateDialog["statusicon"].setPixmapNum(5)
				self.pvrStateDialog["speed"].setText(playstateString)
				speed_summary = self.pvrStateDialog["speed"].text
				statusicon_summary = 5
				if self.has_key("state") and config.usage.movieplayer_pvrstate.value:
					self["state"].setText(playstateString)
					self["statusicon"].setPixmapNum(5)
					self["speed"].setText(playstateString)

			for cb in self.onChangedEntry:
				cb(state_summary, speed_summary, statusicon_summary)

		# if we return into "PLAY" state, ensure that the dialog gets hidden if there will be no infobar displayed
		if not config.usage.show_infobar_on_skip.value and self.seekstate == self.SEEK_STATE_PLAY and not self.force_show:
			self.pvrStateDialog.hide()
		else:
			self._mayShow()

class InfoBarTimeshiftState(InfoBarPVRState):
	def __init__(self):
		InfoBarPVRState.__init__(self, screen=TimeshiftState, force_show=True)
		self.onPlayStateChanged.append(self.__timeshiftEventName)
		self.onHide.append(self.__hideTimeshiftState)

	def _mayShow(self):
		if self.shown and self.timeshiftEnabled() and self.isSeekable():
			InfoBarTimeshift.ptsSeekPointerSetCurrentPos(self)
			if config.timeshift.showinfobar.value:
				self["TimeshiftSeekPointerActions"].setEnabled(True)
			self.pvrStateDialog.show()
		if not self.isSeekable():
			self.startHideTimer()

	def __hideTimeshiftState(self):
		self["TimeshiftSeekPointerActions"].setEnabled(False)
		self.pvrStateDialog.hide()

	def __timeshiftEventName(self,state):
		if self.timeshiftEnabled() and os.path.exists("%spts_livebuffer_%s.meta" % (config.usage.timeshift_path.value,self.pts_currplaying)):
			readmetafile = open("%spts_livebuffer_%s.meta" % (config.usage.timeshift_path.value,self.pts_currplaying), "r")
			servicerefname = readmetafile.readline()[0:-1]
			eventname = readmetafile.readline()[0:-1]
			readmetafile.close()
			self.pvrStateDialog["eventname"].setText(eventname)
		else:
			self.pvrStateDialog["eventname"].setText("")

class InfoBarShowMovies:
	# i don't really like this class.
	# it calls a not further specified "movie list" on up/down/movieList,
	# so this is not more than an action map
	def __init__(self):
		self["MovieListActions"] = HelpableActionMap(self, "InfobarMovieListActions",
			{
				"movieList": (self.showMovies, _("Open the movie list")),
				"up": (self.up, _("Open the movie list")),
				"down": (self.down, _("Open the movie list"))
			})

from Screens.PiPSetup import PiPSetup
class InfoBarExtensions:
	EXTENSION_SINGLE = 0
	EXTENSION_LIST = 1

	def __init__(self):
		self.list = []

		if config.plisettings.ColouredButtons.value:
			self["InstantExtensionsActions"] = HelpableActionMap(self, "InfobarExtensions",
				{
					"extensions": (self.bluekey_ex, _("Show extensions...")),
					"showPluginBrowser": (self.showPluginBrowser, _("Show the plugin browser..")),
					"showEventInfo": (self.SelectopenEventView, _("Show the infomation on current event.")),
					"openTimerList": (self.showTimerList, _("Show the list of timers.")),
					"openAutoTimerList": (self.showAutoTimerList, _("Show the list of AutoTimers.")),
					"openEPGSearch": (self.showEPGSearch, _("Search the epg for current event.")),
					"openIMDB": (self.showIMDB, _("Search IMDb for information about current event.")),
					"showMediaPlayer": (self.showMediaPlayer, _("Show the media player...")),
					"openDreamPlex": (self.showDreamPlex, _("Show the DreamPlex player...")),
				}, 1) # lower priority
		else:
			self["InstantExtensionsActions"] = HelpableActionMap(self, "InfobarExtensions",
				{
					"extensions": (self.bluekey_ex, _("view extensions...")),
					"showPluginBrowser": (self.showPluginBrowser, _("Show the plugin browser..")),
					"showDreamPlex": (self.showDreamPlex, _("Show the DreamPlex player...")),
					"showEventInfo": (self.SelectopenEventView, _("Show the infomation on current event.")),
					"showMediaPlayer": (self.showMediaPlayer, _("Show the media player...")),
				}, 1) # lower priority

		self.addExtension(extension=self.getOsd3DSetup, type=InfoBarExtensions.EXTENSION_LIST)
		self.addExtension(extension=self.getCCcamInfo, type=InfoBarExtensions.EXTENSION_LIST)
		self.addExtension(extension=self.getOScamInfo, type=InfoBarExtensions.EXTENSION_LIST)
		self.addExtension(extension=self.getNcamInfo, type=InfoBarExtensions.EXTENSION_LIST)
		self.addExtension(extension=self.getIpkUninstall, type=InfoBarExtensions.EXTENSION_LIST)

		for p in plugins.getPlugins(PluginDescriptor.WHERE_EXTENSIONSINGLE):
			p(self)

	def bluekey_ex(self):
		self.showExtensionSelection()

	def SelectopenEventView(self):
		try:
			self.openEventView()
		except:
			pass

	def get3DSetupname(self):
		return _("OSD 3D Setup")

	def getOsd3DSetup(self):
		if config.osd.show3dextensions.value:
			return [((boundFunction(self.get3DSetupname), boundFunction(self.open3DSetup), lambda: True), None)]
		else:
			return []

	def getCCname(self):
		return _("CCcam Info")

	def getCCcamInfo(self):
		if pathExists('/usr/bin/'):
			softcams = os.listdir('/usr/bin/')
		for softcam in softcams:
			if softcam.lower().startswith('cccam') and config.cccaminfo.showInExtensions.value:
				return [((boundFunction(self.getCCname), boundFunction(self.openCCcamInfo), lambda: True), None)] or []
		else:
			return []

	def getOSname(self):
		return _("OScam Info")

	def getOScamInfo(self):
		if pathExists('/usr/bin/'):
			softcams = os.listdir('/usr/bin/')
		for softcam in softcams:
			if softcam.lower().startswith('oscam') and config.oscaminfo.showInExtensions.value:
				return [((boundFunction(self.getOSname), boundFunction(self.openOScamInfo), lambda: True), None)] or []
		else:
			return []

	def getNname(self):
		return _("Ncam Info")

	def getNcamInfo(self):
		if pathExists('/usr/bin/'):
			softcams = os.listdir('/usr/bin/')
		for softcam in softcams:
			if softcam.lower().startswith('ncam') and config.ncaminfo.showInExtensions.value:
				return [((boundFunction(self.getNname), boundFunction(self.openNcamInfo), lambda: True), None)] or []
		else:
			return []

	def getIpkUninstallname(self):
		return _("Ipk Uninstall Tool")

	def getIpkUninstall(self):
		return [((boundFunction(self.getIpkUninstallname), boundFunction(self.openIpkUninstall), lambda: True), None)]

	def addExtension(self, extension, key=None, type=EXTENSION_SINGLE):
		self.list.append((type, extension, key))
		if config.usage.sort_extensionslist.value:
			self.list.sort()

	def updateExtension(self, extension, key=None):
		self.extensionsList.append(extension)
		if key is not None:
			if self.extensionKeys.has_key(key):
				key = None

		if key is None:
			for x in self.availableKeys:
				if not self.extensionKeys.has_key(x):
					key = x
					break

		if key is not None:
			self.extensionKeys[key] = len(self.extensionsList) - 1

	def updateExtensions(self):
		self.extensionsList = []
		self.availableKeys = [ "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "red", "green", "yellow", "blue" ]
		self.extensionKeys = {}
		for x in self.list:
			if x[0] == self.EXTENSION_SINGLE:
				self.updateExtension(x[1], x[2])
			else:
				for y in x[1]():
					self.updateExtension(y[0], y[1])

	def showExtensionSelection(self):
		self.updateExtensions()
		extensionsList = self.extensionsList[:]
		keys = []
		list = []
		colorlist = []
		for x in self.availableKeys:
			if self.extensionKeys.has_key(x):
				entry = self.extensionKeys[x]
				extension = self.extensionsList[entry]
				if extension[2]():
					name = str(extension[0]())
					if self.availableKeys.index(x) < 10:
						list.append((extension[0](), extension))
					else:
						colorlist.append((extension[0](), extension))
					keys.append(x)
					extensionsList.remove(extension)
				else:
					extensionsList.remove(extension)
		if config.usage.sort_extensionslist.value:
			list.sort()
		for x in colorlist:
			list.append(x)
		list.extend([(x[0](), x) for x in extensionsList])

		keys += [""] * len(extensionsList)
		self.session.openWithCallback(self.extensionCallback, ChoiceBox, title=_("Please choose an extension..."), list=list, keys=keys, skin_name="ExtensionsList")

	def extensionCallback(self, answer):
		if answer is not None:
			answer[1][1]()

	def showPluginBrowser(self):
		from Screens.PluginBrowser import PluginBrowser
		self.session.open(PluginBrowser)

	def openCCcamInfo(self):
		from Screens.CCcamInfo import CCcamInfoMain
		self.session.open(CCcamInfoMain)

	def openOScamInfo(self):
		from Screens.OScamInfo import OscamInfoMenu
		self.session.open(OscamInfoMenu)

	def openNcamInfo(self):
		from Screens.NcamInfo import NcamInfoMenu
		self.session.open(NcamInfoMenu)

	def openIpkUninstall(self):
		from Screens.Ipkuninstall import Ipkuninstall
		self.session.open(Ipkuninstall)

	def showTimerList(self):
		self.session.open(TimerEditList)

	def open3DSetup(self):
		from Screens.UserInterfacePositioner import OSD3DSetupScreen
		self.session.open(OSD3DSetupScreen)

	def showAutoTimerList(self):
		if os.path.exists("/usr/lib/enigma2/python/Plugins/Extensions/AutoTimer/plugin.pyo"):
			from Plugins.Extensions.AutoTimer.plugin import main, autostart
			from Plugins.Extensions.AutoTimer.AutoTimer import AutoTimer
			from Plugins.Extensions.AutoTimer.AutoPoller import AutoPoller
			self.autopoller = AutoPoller()
			self.autotimer = AutoTimer()
			try:
				self.autotimer.readXml()
			except SyntaxError as se:
				self.session.open(
					MessageBox,
					_("Your config file is not well-formed:\n%s") % (str(se)),
					type=MessageBox.TYPE_ERROR,
					timeout=10
				)
				return

			# Do not run in background while editing, this might screw things up
			if self.autopoller is not None:
				self.autopoller.stop()

			from Plugins.Extensions.AutoTimer.AutoTimerOverview import AutoTimerOverview
			self.session.openWithCallback(
				self.editCallback,
				AutoTimerOverview,
				self.autotimer
			)
		else:
			self.session.open(MessageBox, _("The AutoTimer plugin is not installed!\nPlease install it."), type=MessageBox.TYPE_INFO,timeout=10 )

	def editCallback(self, session):
		# XXX: canceling of GUI (Overview) won't affect config values which might have been changed - is this intended?
		# Don't parse EPG if editing was canceled
		if session is not None:
			# Save xml
			self.autotimer.writeXml()
			# Poll EPGCache
			self.autotimer.parseEPG()

		# Start autopoller again if wanted
		if config.plugins.autotimer.autopoll.value:
			if self.autopoller is None:
				from Plugins.Extensions.AutoTimer.AutoPoller import AutoPoller
				self.autopoller = AutoPoller()
			self.autopoller.start()
		# Remove instance if not running in background
		else:
			self.autopoller = None
			self.autotimer = None

	def showEPGSearch(self):
		from Plugins.Extensions.EPGSearch.EPGSearch import EPGSearch
		s = self.session.nav.getCurrentService()
		if s:
			info = s.info()
			event = info.getEvent(0) # 0 = now, 1 = next
			if event:
				name = event and event.getEventName() or ''
			else:
				name = self.session.nav.getCurrentlyPlayingServiceOrGroup().toString()
				name = name.split('/')
				name = name[-1]
				name = name.replace('.',' ')
				name = name.split('-')
				name = name[0]
				if name.endswith(' '):
					name = name[:-1]
			if name:
				self.session.open(EPGSearch, name, False)
			else:
				self.session.open(EPGSearch)
		else:
			self.session.open(EPGSearch)

	def showIMDB(self):
		if os.path.exists("/usr/lib/enigma2/python/Plugins/Extensions/IMDb/plugin.pyo"):
			from Plugins.Extensions.IMDb.plugin import IMDB
			s = self.session.nav.getCurrentService()
			if s:
				info = s.info()
				event = info.getEvent(0) # 0 = now, 1 = next
				name = event and event.getEventName() or ''
				self.session.open(IMDB, name)
		else:
			self.session.open(MessageBox, _("The IMDb plugin is not installed!\nPlease install it."), type=MessageBox.TYPE_INFO,timeout=10 )

	def showMediaPlayer(self):
		if isinstance(self, InfoBarExtensions):
			if isinstance(self, InfoBar):
				try: # falls es nicht installiert ist
					from Plugins.Extensions.MediaPlayer.plugin import MediaPlayer
					self.session.open(MediaPlayer)
					no_plugin = False
				except Exception, e:
					self.session.open(MessageBox, _("The MediaPlayer plugin is not installed!\nPlease install it."), type=MessageBox.TYPE_INFO,timeout=10 )

	def showDreamPlex(self):
		if os.path.exists("/usr/lib/enigma2/python/Plugins/Extensions/DreamPlex/plugin.pyo"):
			from Plugins.Extensions.DreamPlex.plugin import DPS_MainMenu
			self.session.open(DPS_MainMenu)
		else:
			self.session.open(MessageBox, _("The DreamPlex plugin is not installed!\nPlease install it."), type=MessageBox.TYPE_INFO,timeout=10 )

from Tools.BoundFunction import boundFunction
import inspect

# depends on InfoBarExtensions
class InfoBarPlugins:
	def __init__(self):
		self.addExtension(extension=self.getPluginList, type=InfoBarExtensions.EXTENSION_LIST)

	def getPluginName(self, name):
		return name

	def getPluginList(self):
		l = []
		for p in plugins.getPlugins(where=PluginDescriptor.WHERE_EXTENSIONSMENU):
			args = inspect.getargspec(p.__call__)[0]
			if len(args) == 1 or len(args) == 2 and isinstance(self, InfoBarChannelSelection):
				l.append(((boundFunction(self.getPluginName, p.name), boundFunction(self.runPlugin, p), lambda: True), None, p.name))
		l.sort(key=lambda e: e[2]) # sort by name
		return l

	def runPlugin(self, plugin):
		if isinstance(self, InfoBarChannelSelection):
			plugin(session=self.session, servicelist=self.servicelist)
		else:
			try:
				plugin(session=self.session)
			except Exception, err:
				print '[InfoBarGenerics] Error: ', err

from Components.Task import job_manager
class InfoBarJobman:
	def __init__(self):
		self.addExtension(extension=self.getJobList, type=InfoBarExtensions.EXTENSION_LIST)

	def getJobList(self):
		if config.usage.jobtaksextensions.value:
			return [((boundFunction(self.getJobName, job), boundFunction(self.showJobView, job), lambda: True), None) for job in job_manager.getPendingJobs()]
		else:
			return []

	def getJobName(self, job):
		return "%s: %s (%d%%)" % (job.getStatustext(), job.name, int(100*job.progress/float(job.end)))

	def showJobView(self, job):
		from Screens.TaskView import JobView
		job_manager.in_background = False
		self.session.openWithCallback(self.JobViewCB, JobView, job)

	def JobViewCB(self, in_background):
		job_manager.in_background = in_background

# depends on InfoBarExtensions
class InfoBarPiP:
	def __init__(self):
		try:
			self.session.pipshown
		except:
			self.session.pipshown = False

		self.lastPiPService = None

		if SystemInfo["PIPAvailable"]:
			self["PiPActions"] = HelpableActionMap(self, "InfobarPiPActions",
				{
					"activatePiP": (self.activePiP, self.activePiPName),
				})
			if self.allowPiP:
				self.addExtension((self.getShowHideName, self.showPiP, lambda: True), "blue")
				self.addExtension((self.getMoveName, self.movePiP, self.pipShown), "green")
				self.addExtension((self.getSwapName, self.swapPiP, self.pipShown), "yellow")
				self.addExtension((self.getTogglePipzapName, self.togglePipzap, self.pipShown), "red")
			else:
				self.addExtension((self.getShowHideName, self.showPiP, self.pipShown), "blue")
				self.addExtension((self.getMoveName, self.movePiP, self.pipShown), "green")

		self.lastPiPServiceTimeoutTimer = eTimer()
		self.lastPiPServiceTimeoutTimer.callback.append(self.clearLastPiPService)

	def pipShown(self):
		return self.session.pipshown

	def pipHandles0Action(self):
		return self.pipShown() and config.usage.pip_zero_button.value != "standard"

	def getShowHideName(self):
		if self.session.pipshown:
			return _("Disable Picture in Picture")
		else:
			return _("Activate Picture in Picture")

	def getSwapName(self):
		return _("Swap services")

	def getMoveName(self):
		return _("Picture in Picture Setup")

	def getTogglePipzapName(self):
		slist = self.servicelist
		if slist and slist.dopipzap:
			return _("Zap focus to main screen")
		return _("Zap focus to Picture in Picture")

	def togglePipzap(self):
		if not self.session.pipshown:
			self.showPiP()
		slist = self.servicelist
		if slist and self.session.pipshown:
			slist.togglePipzap()
			if slist.dopipzap:
				currentServicePath = slist.getCurrentServicePath()
				self.servicelist.setCurrentServicePath(self.session.pip.servicePath, doZap=False)
				self.session.pip.servicePath = currentServicePath

	def showPiP(self):
		self.lastPiPServiceTimeoutTimer.stop()
		slist = self.servicelist
		if self.session.pipshown:
			if slist and slist.dopipzap:
				self.togglePipzap()
			if self.session.pipshown:
				lastPiPServiceTimeout = int(config.usage.pip_last_service_timeout.value)
				if lastPiPServiceTimeout >= 0:
					self.lastPiPService = self.session.pip.getCurrentServiceReference()
					if lastPiPServiceTimeout:
						self.lastPiPServiceTimeoutTimer.startLongTimer(lastPiPServiceTimeout)
				del self.session.pip
				if SystemInfo["LCDMiniTV"]:
					if config.lcd.modepip.value >= "1":
						print '[LCDMiniTV] disable PIP'
						f = open("/proc/stb/lcd/mode", "w")
						f.write(config.lcd.modeminitv.value)
						f.close()
				self.session.pipshown = False
			if hasattr(self, "ScreenSaverTimerStart"):
				self.ScreenSaverTimerStart()
		else:
			service = self.session.nav.getCurrentService()
			info = service and service.info()
			if info:
				xres = str(info.getInfo(iServiceInformation.sVideoWidth))
			if info and int(xres) <= 720 or getMachineBuild() != 'blackbox7405':
				self.session.pip = self.session.instantiateDialog(PictureInPicture)
				self.session.pip.setAnimationMode(0)
				self.session.pip.show()
				newservice = self.lastPiPService or self.session.nav.getCurrentlyPlayingServiceReference() or self.servicelist.servicelist.getCurrent()
				if self.session.pip.playService(newservice):
					self.session.pipshown = True
					self.session.pip.servicePath = self.servicelist.getCurrentServicePath()
					if SystemInfo["LCDMiniTVPiP"] and int(config.lcd.modepip.value) >= 1:
						print '[LCDMiniTV] enable PIP'
						f = open("/proc/stb/lcd/mode", "w")
						f.write(config.lcd.modepip.value)
						f.close()
						f = open("/proc/stb/vmpeg/1/dst_width", "w")
						f.write("0")
						f.close()
						f = open("/proc/stb/vmpeg/1/dst_height", "w")
						f.write("0")
						f.close()
						f = open("/proc/stb/vmpeg/1/dst_apply", "w")
						f.write("1")
						f.close()
				else:
					newservice = self.session.nav.getCurrentlyPlayingServiceReference() or self.servicelist.servicelist.getCurrent()
					if self.session.pip.playService(newservice):
						self.session.pipshown = True
						self.session.pip.servicePath = self.servicelist.getCurrentServicePath()
						if SystemInfo["LCDMiniTVPiP"] and int(config.lcd.modepip.value) >= 1:
							print '[LCDMiniTV] enable PIP'
							f = open("/proc/stb/lcd/mode", "w")
							f.write(config.lcd.modepip.value)
							f.close()
							f = open("/proc/stb/vmpeg/1/dst_width", "w")
							f.write("0")
							f.close()
							f = open("/proc/stb/vmpeg/1/dst_height", "w")
							f.write("0")
							f.close()
							f = open("/proc/stb/vmpeg/1/dst_apply", "w")
							f.write("1")
							f.close()
					else:
						self.lastPiPService = None
						self.session.pipshown = False
						del self.session.pip
			elif info:
				self.session.open(MessageBox, _("Your %s %s does not support PiP HD") % (getMachineBrand(), getMachineName()), type=MessageBox.TYPE_INFO,timeout=5 )
			else:
				self.session.open(MessageBox, _("No active channel found."), type=MessageBox.TYPE_INFO,timeout=5 )
		if self.session.pipshown and hasattr(self, "screenSaverTimer"):
			self.screenSaverTimer.stop()

	def clearLastPiPService(self):
		self.lastPiPService = None

	def activePiP(self):
		if self.servicelist and self.servicelist.dopipzap or not self.session.pipshown:
			self.showPiP()
		else:
			self.togglePipzap()

	def activePiPName(self):
		if self.servicelist and self.servicelist.dopipzap:
			return _("Disable Picture in Picture")
		if self.session.pipshown:
			return _("Zap focus to Picture in Picture")
		else:
			return _("Activate Picture in Picture")

	def swapPiP(self):
		if self.pipShown():
			swapservice = self.session.nav.getCurrentlyPlayingServiceOrGroup()
			pipref = self.session.pip.getCurrentService()
			if swapservice and pipref and pipref.toString() != swapservice.toString():
				currentServicePath = self.servicelist.getCurrentServicePath()
				currentBouquet = self.servicelist and self.servicelist.getRoot()
				self.servicelist.setCurrentServicePath(self.session.pip.servicePath, doZap=False)
				self.session.pip.playService(swapservice)
				self.session.nav.stopService() # stop portal
				self.session.nav.playService(pipref, checkParentalControl=False, adjust=False)
				self.session.pip.servicePath = currentServicePath
				self.session.pip.servicePath[1] = currentBouquet
				if self.servicelist.dopipzap:
					# This unfortunately won't work with subservices
					self.servicelist.setCurrentSelection(self.session.pip.getCurrentService())

	def movePiP(self):
		if self.pipShown():
			self.session.open(PiPSetup, pip=self.session.pip)

	def pipDoHandle0Action(self):
		use = config.usage.pip_zero_button.value
		if "swap" == use:
			self.swapPiP()
		elif "swapstop" == use:
			self.swapPiP()
			self.showPiP()
		elif "stop" == use:
			self.showPiP()

class InfoBarInstantRecord:
	"""Instant Record - handles the instantRecord action in order to
	start/stop instant records"""
	def __init__(self):
		self["InstantRecordActions"] = HelpableActionMap(self, "InfobarInstantRecord",
			{
				"instantRecord": (self.instantRecord, _("Instant recording...")),
			})
		self.SelectedInstantServiceRef = None
		if isStandardInfoBar(self):
			self.recording = []
		else:
			from Screens.InfoBar import InfoBar
			InfoBarInstance = InfoBar.instance
			if InfoBarInstance:
				self.recording = InfoBarInstance.recording
		self.saveTimeshiftEventPopupActive = False

	def stopCurrentRecording(self, entry=-1):
		if entry is not None and entry != -1:
			self.session.nav.RecordTimer.removeEntry(self.recording[entry])
			self.recording.remove(self.recording[entry])

	def getProgramInfoAndEvent(self, info, name):
		info["serviceref"] = hasattr(self, "SelectedInstantServiceRef") and self.SelectedInstantServiceRef or self.session.nav.getCurrentlyPlayingServiceOrGroup()

		# try to get event info
		event = None
		try:
			epg = eEPGCache.getInstance()
			event = epg.lookupEventTime(info["serviceref"], -1, 0)
			if event is None:
				if hasattr(self, "SelectedInstantServiceRef") and self.SelectedInstantServiceRef:
					service_info = eServiceCenter.getInstance().info(self.SelectedInstantServiceRef)
					event = service_info and service_info.getEvent(self.SelectedInstantServiceRef)
				else:
					service = self.session.nav.getCurrentService()
					event = service and service.info().getEvent(0)
		except:
			pass

		info["event"] = event
		info["name"]  = name
		info["description"] = ""
		info["eventid"] = None

		if event is not None:
			curEvent = parseEvent(event)
			info["name"] = curEvent[2]
			info["description"] = curEvent[3]
			info["eventid"] = curEvent[4]
			info["end"] = curEvent[1]

	def startInstantRecording(self, limitEvent=False):
		begin = int(time())
		end = begin + 3600 # dummy
		name = "instant record"
		info = { }

		self.getProgramInfoAndEvent(info, name)
		serviceref = info["serviceref"]
		event = info["event"]

		if event is not None:
			if limitEvent:
				end = info["end"]
		else:
			if limitEvent:
				self.session.open(MessageBox, _("No event info found, recording indefinitely."), MessageBox.TYPE_INFO)

		if isinstance(serviceref, eServiceReference):
			serviceref = ServiceReference(serviceref)

		recording = RecordTimerEntry(serviceref, begin, end, info["name"], info["description"], info["eventid"], afterEvent=AFTEREVENT.AUTO, justplay=False, always_zap=False, dirname=preferredInstantRecordPath())
		recording.dontSave = True

		if event is None or limitEvent == False:
			recording.autoincrease = True
			recording.setAutoincreaseEnd()

		simulTimerList = self.session.nav.RecordTimer.record(recording)

		if simulTimerList is None:	# no conflict
			recording.autoincrease = False
			self.recording.append(recording)
		else:
			if len(simulTimerList) > 1: # with other recording
				name = simulTimerList[1].name
				name_date = ' '.join((name, strftime('%F %T', localtime(simulTimerList[1].begin))))
				# print "[TIMER] conflicts with", name_date
				recording.autoincrease = True	# start with max available length, then increment
				if recording.setAutoincreaseEnd():
					self.session.nav.RecordTimer.record(recording)
					self.recording.append(recording)
					self.session.open(MessageBox, _("Record time limited due to conflicting timer %s") % name_date, MessageBox.TYPE_INFO)
				else:
					self.session.open(MessageBox, _("Could not record due to conflicting timer %s") % name, MessageBox.TYPE_INFO)
			else:
				self.session.open(MessageBox, _("Could not record due to invalid service %s") % serviceref, MessageBox.TYPE_INFO)
			recording.autoincrease = False

	def isInstantRecordRunning(self):
#		print "self.recording:", self.recording
		if self.recording:
			for x in self.recording:
				if x.isRunning():
					return True
		return False

	def recordQuestionCallback(self, answer):
		# print 'recordQuestionCallback'
#		print "pre:\n", self.recording

		# print 'test1'
		if answer is None or answer[1] == "no":
			# print 'test2'
			self.saveTimeshiftEventPopupActive = False
			return
		list = []
		recording = self.recording[:]
		for x in recording:
			if not x in self.session.nav.RecordTimer.timer_list:
				self.recording.remove(x)
			elif x.dontSave and x.isRunning():
				list.append((x, False))

		if answer[1] == "changeduration":
			if len(self.recording) == 1:
				self.changeDuration(0)
			else:
				self.session.openWithCallback(self.changeDuration, TimerSelection, list)
		elif answer[1] == "changeendtime":
			if len(self.recording) == 1:
				self.setEndtime(0)
			else:
				self.session.openWithCallback(self.setEndtime, TimerSelection, list)
		elif answer[1] == "timer":
			import TimerEdit
			self.session.open(TimerEdit.TimerEditList)
		elif answer[1] == "stop":
			self.session.openWithCallback(self.stopCurrentRecording, TimerSelection, list)
		elif answer[1] in ( "indefinitely" , "manualduration", "manualendtime", "event"):
			from Components.About import about
			if len(list) >= 2 and about.getChipSetString() in ('meson-6', 'meson-64'):
				Notifications.AddNotification(MessageBox,_("Sorry only possible to record 2 channels at once"), MessageBox.TYPE_ERROR, timeout=5)
				return
			self.startInstantRecording(limitEvent=answer[1] in ("event", "manualendtime") or False)
			if answer[1] == "manualduration":
				self.changeDuration(len(self.recording)-1)
			elif answer[1] == "manualendtime":
				self.setEndtime(len(self.recording)-1)
		elif answer[1] == "savetimeshift":
			# print 'test1'
			if self.isSeekable() and self.pts_eventcount != self.pts_currplaying:
				# print 'test2'
				InfoBarTimeshift.SaveTimeshift(self, timeshiftfile="pts_livebuffer_%s" % self.pts_currplaying)
			else:
				# print 'test3'
				Notifications.AddNotification(MessageBox,_("Timeshift will get saved at end of event!"), MessageBox.TYPE_INFO, timeout=5)
				self.save_current_timeshift = True
				config.timeshift.isRecording.value = True
		elif answer[1] == "savetimeshiftEvent":
			# print 'test4'
			InfoBarTimeshift.saveTimeshiftEventPopup(self)

		elif answer[1].startswith("pts_livebuffer") is True:
			# print 'test2'
			InfoBarTimeshift.SaveTimeshift(self, timeshiftfile=answer[1])

		if answer[1] != "savetimeshiftEvent":
			self.saveTimeshiftEventPopupActive = False

	def setEndtime(self, entry):
		if entry is not None and entry >= 0:
			self.selectedEntry = entry
			self.endtime=ConfigClock(default=self.recording[self.selectedEntry].end)
			dlg = self.session.openWithCallback(self.TimeDateInputClosed, TimeDateInput, self.endtime)
			dlg.setTitle(_("Please change recording endtime"))

	def TimeDateInputClosed(self, ret):
		if len(ret) > 1:
			if ret[0]:
#				print "stopping recording at", strftime("%F %T", localtime(ret[1]))
				if self.recording[self.selectedEntry].end != ret[1]:
					self.recording[self.selectedEntry].autoincrease = False
				self.recording[self.selectedEntry].end = ret[1]
		#else:
		#	if self.recording[self.selectedEntry].end != int(time()):
		#		self.recording[self.selectedEntry].autoincrease = False
		#	self.recording[self.selectedEntry].end = int(time())
				self.session.nav.RecordTimer.timeChanged(self.recording[self.selectedEntry])

	def changeDuration(self, entry):
		if entry is not None and entry >= 0:
			self.selectedEntry = entry
			self.session.openWithCallback(self.inputCallback, InputBox, title=_("How many minutes do you want to record?"), text="5  ", maxSize=True, type=Input.NUMBER)

	def inputCallback(self, value):
#		print "stopping recording after", int(value), "minutes."
		entry = self.recording[self.selectedEntry]
		if value is not None:
			value = value.replace(" ", "")
			if value == "":
				value = "0"
			if int(value) != 0:
				entry.autoincrease = False
			entry.end = int(time()) + 60 * int(value)
		#else:
		#	if entry.end != int(time()):
		#		entry.autoincrease = False
		#	entry.end = int(time())
			self.session.nav.RecordTimer.timeChanged(entry)

	def isTimerRecordRunning(self):
		identical = timers = 0
		for timer in self.session.nav.RecordTimer.timer_list:
			if timer.isRunning() and not timer.justplay:
				timers += 1
				if self.recording:
					for x in self.recording:
						if x.isRunning() and x == timer:
							identical += 1
		return timers > identical

	def instantRecord(self, serviceRef=None):
		self.SelectedInstantServiceRef = serviceRef
		pirr = preferredInstantRecordPath()
		if not findSafeRecordPath(pirr) and not findSafeRecordPath(defaultMoviePath()):
			if not pirr:
				pirr = ""
			self.session.open(MessageBox, _("Missing ") + "\n" + pirr +
						 "\n" + _("No HDD found or HDD not initialized!"), MessageBox.TYPE_ERROR)
			return

		if isStandardInfoBar(self):
			common = ((_("Add recording (stop after current event)"), "event"),
				(_("Add recording (indefinitely)"), "indefinitely"),
				(_("Add recording (enter recording duration)"), "manualduration"),
				(_("Add recording (enter recording endtime)"), "manualendtime"),)

			timeshiftcommon = ((_("Timeshift save recording (stop after current event)"), "savetimeshift"),
				(_("Timeshift save recording (Select event)"), "savetimeshiftEvent"),)
		else:
			common = ()
			timeshiftcommon = ()

		if self.isInstantRecordRunning():
			title =_("A recording is currently running.\nWhat do you want to do?")
			list = ((_("Stop recording"), "stop"),) + common + \
				((_("Change recording (duration)"), "changeduration"),
				(_("Change recording (endtime)"), "changeendtime"),)
			if self.isTimerRecordRunning():
				list += ((_("Stop timer recording"), "timer"),)
		else:
			title=_("Start recording?")
			list = common

			if self.isTimerRecordRunning():
				list += ((_("Stop timer recording"), "timer"),)
		if isStandardInfoBar(self) and self.timeshiftEnabled():
			list = list + timeshiftcommon

		if isStandardInfoBar(self):
			list = list + ((_("Do not record"), "no"),)

		if list:
			self.session.openWithCallback(self.recordQuestionCallback, ChoiceBox,title=title,list=list)
		else:
			return 0

class InfoBarAudioSelection:
	def __init__(self):
		self["AudioSelectionAction"] = HelpableActionMap(self, "InfobarAudioSelectionActions",
			{
				"audioSelection": (self.audioSelection, _("Audio options...")),
				"yellow_key": (self.yellow_key, _("Audio options...")),
				"audioSelectionLong": (self.audioDownmixToggle, _("Toggle Digital downmix...")),
			})

	def yellow_key(self):
		if not hasattr(self, "LongButtonPressed"):
			self.LongButtonPressed = False
		if not self.LongButtonPressed:
			if config.usage.on_short_yellow_key.value == '0':
				self.audioSelection()
			elif config.usage.on_short_yellow_key.value == '2':
				global AUDIO
				AUDIO = True
				ToggleVideo()
			elif config.usage.on_short_yellow_key.value == '3':
				self.startTeletext()
			else:
				try:
					self.startTimeshift()
				except:
					pass
		else:
			if config.usage.on_long_yellow_key.value == '0':
				self.audioSelection()
			elif config.usage.on_long_yellow_key.value == '2':
				global AUDIO
				AUDIO = True
				ToggleVideo()
			elif config.usage.on_long_yellow_key.value == '3':
				self.startTeletext()
			else:
				try:
					self.startTimeshift()
				except:
					pass

	def audioSelection(self):
		from Screens.AudioSelection import AudioSelection
		self.session.openWithCallback(self.audioSelected, AudioSelection, infobar=self)

	def audioSelected(self, ret=None):
		print "[infobar::audioSelected]", ret

	def audioDownmixToggle(self, popup=True):
		if SystemInfo["CanDownmixAC3"]:
			if config.av.downmix_ac3.value:
				message = _("Dolby Digital downmix is now") + " " + _("disabled")
				print '[Audio] Dolby Digital downmix is now disabled'
				config.av.downmix_ac3.setValue(False)
			else:
				config.av.downmix_ac3.setValue(True)
				message = _("Dolby Digital downmix is now") + " " + _("enabled")
				print '[Audio] Dolby Digital downmix is now enabled'
			if popup:
				Notifications.AddPopup(text=message, type=MessageBox.TYPE_INFO, timeout=5, id="DDdownmixToggle")

	def audioDownmixOn(self):
		if not config.av.downmix_ac3.value:
			self.audioDownmixToggle(False)

	def audioDownmixOff(self):
		if config.av.downmix_ac3.value:
			self.audioDownmixToggle(False)

class InfoBarSubserviceSelection:
	def __init__(self):
		self["SubserviceSelectionAction"] = HelpableActionMap(self, "InfobarSubserviceSelectionActions",
			{
				"GreenPressed": (self.GreenPressed),
				"subserviceSelection": (self.subserviceSelection, _("Subservice list...")),
			})

		self["SubserviceQuickzapAction"] = HelpableActionMap(self, "InfobarSubserviceQuickzapActions",
			{
				"nextSubservice": (self.nextSubservice, _("Switch to next sub service")),
				"prevSubservice": (self.prevSubservice, _("Switch to previous sub service"))
			}, -1)
		self["SubserviceQuickzapAction"].setEnabled(False)

		self.__event_tracker = ServiceEventTracker(screen=self, eventmap={
				iPlayableService.evUpdatedEventInfo: self.checkSubservicesAvail
			})
		self.onClose.append(self.__removeNotifications)

		self.bouquets = self.bsel = self.selectedSubservice = None

	def __removeNotifications(self):
		self.session.nav.event.remove(self.checkSubservicesAvail)

	def checkSubservicesAvail(self):
		serviceRef = self.session.nav.getCurrentlyPlayingServiceReference()
		if not serviceRef or not hasActiveSubservicesForCurrentChannel(serviceRef.toString()):
			self["SubserviceQuickzapAction"].setEnabled(False)
			self.bouquets = self.bsel = self.selectedSubservice = None

	def nextSubservice(self):
		self.changeSubservice(+1)

	def prevSubservice(self):
		self.changeSubservice(-1)

	def playSubservice(self, ref):
		if ref.getUnsignedData(6) == 0:
			ref.setName("")
		self.session.nav.playService(ref, checkParentalControl=False, adjust=False)

	def changeSubservice(self, direction):
		serviceRef = self.session.nav.getCurrentlyPlayingServiceReference()
		if serviceRef:
			subservices = getActiveSubservicesForCurrentChannel(serviceRef.toString())
			if subservices and len(subservices) > 1 and serviceRef.toString() in [x[1] for x in subservices]:
				selection = [x[1] for x in subservices].index(serviceRef.toString())
				selection += direction % len(subservices)
				try:
					newservice = eServiceReference(subservices[selection][0])
				except:
					newservice = None
				if newservice and newservice.valid():
					self.playSubservice(newservice)

	def subserviceSelection(self):
		serviceRef = self.session.nav.getCurrentlyPlayingServiceReference()
		if serviceRef:
			subservices = getActiveSubservicesForCurrentChannel(serviceRef.toString())
			if subservices and len(subservices) > 1 and serviceRef.toString() in [x[1] for x in subservices]:
				selection = [x[1] for x in subservices].index(serviceRef.toString())
				self.bouquets = self.servicelist and self.servicelist.getBouquetList()
				#if self.bouquets and len(self.bouquets):
				#	keys = ["red", "blue", "", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
				#	call_func_title = _("Add to favourites")
				#	if config.usage.multibouquet.value:
				#		call_func_title = _("Add to bouquet")
				#		tlist = [(_("Quick zap"), "quickzap", subservices), (call_func_title, "CALLFUNC", self.addSubserviceToBouquetCallback), ("--", "")] + subservices
				#	selection += 3
				#else:
				tlist = [(_("Quick zap"), "quickzap", subservices), ("--", "")] + subservices
				keys = ["red", "", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
				selection += 2
				self.session.openWithCallback(self.subserviceSelected, ChoiceBox, title=_("Please select a sub service..."), list=tlist, selection=selection, keys=keys, skin_name="SubserviceSelection")

	def subserviceSelected(self, service):
		if service and len(service) > 1:
			if service[1] == "quickzap":
				from Screens.SubservicesQuickzap import SubservicesQuickzap
				self.session.open(SubservicesQuickzap, service[2])
			else:
				try:
					ref = eServiceReference(service[1])
				except:
					ref = None
				if ref and ref.valid():
					self["SubserviceQuickzapAction"].setEnabled(True)
					self.playSubservice(ref)

	def addSubserviceToBouquetCallback(self, service):
		if service and len(service) > 1:
			try:
				self.selectedSubservice = eServiceReference(service[1])
			except:
				self.selectedSubservice = None
			if self.selectedSubservice is None or not self.selectedSubservice.valid() or self.bouquets is None:
				self.bouquets = self.bsel = self.selectedSubservice = None
				return
			cnt = len(self.bouquets)
			if cnt > 1:
				self.bsel = self.session.openWithCallback(self.bouquetSelClosed, BouquetSelector, self.bouquets, self.addSubserviceToBouquet)
			elif cnt == 1:
				self.addSubserviceToBouquet(self.bouquets[0][1])
				self.session.open(MessageBox, _("Service has been added to the favourites."), MessageBox.TYPE_INFO, timeout=5)
		else:
			self.session.open(MessageBox, _("Service cant been added to the favourites."), MessageBox.TYPE_INFO, timeout=5)

	def bouquetSelClosed(self, confirmed):
		self.bouquets = self.bsel = self.selectedSubservice = None
		if confirmed:
			self.session.open(MessageBox, _("Service has been added to the selected bouquet."), MessageBox.TYPE_INFO, timeout=5)

	def addSubserviceToBouquet(self, dest):
		self.servicelist.addServiceToBouquet(dest, self.selectedSubservice)
		if self.bsel:
			self.bsel.close(True)
			self.bouquets = self.bsel = self.selectedSubservice = None

	def GreenPressed(self):
		if config.plisettings.Subservice.value == "0":
			self.openTimerList()
		elif config.plisettings.Subservice.value == "1":
			self.openPluginBrowser()
		else:
			serviceRef = self.session.nav.getCurrentlyPlayingServiceReference()
			if serviceRef:
				subservices = getActiveSubservicesForCurrentChannel(serviceRef.toString())
				if subservices and len(subservices) > 1 and serviceRef.toString() in [x[1] for x in subservices]:
					self.subserviceSelection()
				else:
					if config.plisettings.Subservice.value == "2":
						self.openTimerList()
					else:
						self.openPluginBrowser()
			else:
				if config.plisettings.Subservice.value == "2":
					self.openTimerList()
				else:
					self.openPluginBrowser()

	def openPluginBrowser(self):
		try:
			from Screens.PluginBrowser import PluginBrowser
			self.session.open(PluginBrowser)
		except:
			pass

	def openTimerList(self):
		self.session.open(TimerEditList)

from Components.Sources.HbbtvApplication import HbbtvApplication
gHbbtvApplication = HbbtvApplication()
class InfoBarRedButton:
	def __init__(self):
		self["RedButtonActions"] = HelpableActionMap(self, "InfobarRedButtonActions",
			{
				"activateRedButton": (self.activateRedButton, _("Red button...")),
			})
		self["HbbtvApplication"] = gHbbtvApplication
		self.onHBBTVActivation = [ ]
		self.onRedButtonActivation = [ ]
		self.onReadyForAIT = [ ]
		self.__et = ServiceEventTracker(screen=self, eventmap={
				iPlayableService.evHBBTVInfo: self.detectedHbbtvApplication,
				iPlayableService.evUpdatedInfo: self.updateInfomation
			})

	def updateAIT(self, orgId=0):
		for x in self.onReadyForAIT:
			try:
				x(orgId)
			except Exception, ErrMsg:
				print ErrMsg
				#self.onReadyForAIT.remove(x)

	def updateInfomation(self):
		try:
			self["HbbtvApplication"].setApplicationName("")
			self.updateAIT()
		except Exception, ErrMsg:
			pass

	def detectedHbbtvApplication(self):
		service = self.session.nav.getCurrentService()
		info = service and service.info()
		try:
			for x in info.getInfoObject(iServiceInformation.sHBBTVUrl):
				print x
				if x[0] in (-1, 1):
					self.updateAIT(x[3])
					self["HbbtvApplication"].setApplicationName(x[1])
					break
		except Exception, ErrMsg:
			pass

	def activateRedButton(self):
		service = self.session.nav.getCurrentService()
		info = service and service.info()
		if info and info.getInfoString(iServiceInformation.sHBBTVUrl) != "":
			for x in self.onHBBTVActivation:
				x()
		elif False: # TODO: other red button services
			for x in self.onRedButtonActivation:
				x()

class InfoBarTimerButton:
	def __init__(self):
		self["TimerButtonActions"] = HelpableActionMap(self, "InfobarTimerButtonActions",
			{
				"timerSelection": (self.timerSelection, _("Timer selection...")),
			})

	def timerSelection(self):
		from Screens.TimerEdit import TimerEditList
		self.session.open(TimerEditList)

class InfoBarAspectSelection: 
	STATE_HIDDEN = 0 
	STATE_ASPECT = 1 
	STATE_RESOLUTION = 2
	def __init__(self): 
		self["AspectSelectionAction"] = HelpableActionMap(self, "InfobarAspectSelectionActions", 
			{ 
				"aspectSelection": (self.ExGreen_toggleGreen, _("Aspect list...")), 
			}) 

		self.__ExGreen_state = self.STATE_HIDDEN

	def ExGreen_doAspect(self):
		print "do self.STATE_ASPECT"
		self.__ExGreen_state = self.STATE_ASPECT
		self.aspectSelection()

	def ExGreen_doResolution(self):
		print "do self.STATE_RESOLUTION"
		self.__ExGreen_state = self.STATE_RESOLUTION
		self.resolutionSelection()
		
	def ExGreen_doHide(self):
		print "do self.STATE_HIDDEN"
		self.__ExGreen_state = self.STATE_HIDDEN 

	def ExGreen_toggleGreen(self, arg=""):
		print self.__ExGreen_state
		if self.__ExGreen_state == self.STATE_HIDDEN:
			print "self.STATE_HIDDEN"
			self.ExGreen_doAspect()
		elif self.__ExGreen_state == self.STATE_ASPECT:
			print "self.STATE_ASPECT"
			self.ExGreen_doResolution()
		elif self.__ExGreen_state == self.STATE_RESOLUTION:
			print "self.STATE_RESOLUTION"
			self.ExGreen_doHide()

	def aspectSelection(self):
		selection = 0
		tlist= [(_("Resolution"), "resolution"),("--", ""),(_("4_3_letterbox"), "0"), (_("4_3_panscan"), "1"), (_("16_9"), "2"), (_("16_9_always"), "3"), (_("16_10_letterbox"), "4"), (_("16_10_panscan"), "5"), (_("16_9_letterbox"), "6")]
		for x in range(len(tlist)):
			selection = x
		keys = ["green", "",  "0", "1", "2", "3", "4", "5", "6", "7", "8", "9" ]
		self.session.openWithCallback(self.aspectSelected, ChoiceBox, title=_("Please select an aspect ratio..."), list=tlist, selection=selection, keys=keys)

	def aspectSelected(self, aspect):
		if not aspect is None:
			if isinstance(aspect[1], str):
				if aspect[1] == "":
					self.ExGreen_doHide()
				elif aspect[1] == "resolution":
					self.ExGreen_toggleGreen()
				else:
					from Components.AVSwitch import AVSwitch
					iAVSwitch = AVSwitch()
					iAVSwitch.setAspectRatio(int(aspect[1]))
					self.ExGreen_doHide()
		else:
			self.ExGreen_doHide()
		return

class InfoBarResolutionSelection:
	def __init__(self):
		return

	def resolutionSelection(self):
		f = open("/proc/stb/vmpeg/0/xres", "r")
		xresString = f.read()
		f.close()
		f = open("/proc/stb/vmpeg/0/yres", "r")
		yresString = f.read()
		f.close()
		if getBoxType().startswith('azbox'):
			fpsString = '50000'
		else:	
			try:
				f = open("/proc/stb/vmpeg/0/framerate", "r")
				fpsString = f.read()
				f.close()
			except:
				print"[InfoBarResolutionSelection] Error open /proc/stb/vmpeg/0/framerate !!"
				fpsString = '50000'
		
		xres = int(xresString, 16)
		yres = int(yresString, 16)
		fps = int(fpsString)
		fpsFloat = float(fps)
		fpsFloat = fpsFloat/1000

		# do we need a new sorting with this way here?
		# or should we disable some choices?
		choices = []
		if os.path.exists("/proc/stb/video/videomode_choices"):
			f = open("/proc/stb/video/videomode_choices")
			values = f.readline().replace("\n", "").replace("pal ", "").replace("ntsc ", "").split(" ", -1)
			for x in values:
				entry = x.replace('i50', 'i@50hz').replace('i60', 'i@60hz').replace('p23', 'p@23.976hz').replace('p24', 'p@24hz').replace('p25', 'p@25hz').replace('p29', 'p@29hz').replace('p30', 'p@30hz').replace('p50', 'p@50hz'), x
				choices.append(entry)
			f.close()

		selection = 0
		tlist = []
		tlist.append((_("Exit"), "exit")) 
		tlist.append((_("Auto(not available)"), "auto"))
		tlist.append((_("Video: ") + str(xres) + "x" + str(yres) + "@" + str(fpsFloat) + "hz", ""))
		tlist.append(("--", ""))
		if choices != []:
			for x in choices:
				tlist.append(x)

		keys = ["green", "yellow", "blue", "", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9" ]

		mode = open("/proc/stb/video/videomode").read()[:-1]
		print mode
		for x in range(len(tlist)):
			if tlist[x][1] == mode:
				selection = x

		self.session.openWithCallback(self.ResolutionSelected, ChoiceBox, title=_("Please select a resolution..."), list=tlist, selection=selection, keys=keys)

	def ResolutionSelected(self, Resolution):
		if not Resolution is None:
			if isinstance(Resolution[1], str):
				if Resolution[1] == "exit" or Resolution[1] == "" or Resolution[1] == "auto":
					self.ExGreen_toggleGreen()
				if Resolution[1] != "auto":
					f = open("/proc/stb/video/videomode", "w")
					f.write(Resolution[1])
					f.close()
					#from enigma import gMainDC
					#gMainDC.getInstance().setResolution(-1, -1)
					self.ExGreen_doHide()
		else:
			self.ExGreen_doHide()
		return

class InfoBarVmodeButton:
	def __init__(self):
		self["VmodeButtonActions"] = HelpableActionMap(self, "InfobarVmodeButtonActions",
			{
				"vmodeSelection": (self.vmodeSelection, _("Letterbox zoom")),
			})

	def vmodeSelection(self):
		self.session.open(VideoMode)

class VideoMode(Screen):
	def __init__(self,session):
		Screen.__init__(self, session)
		self["videomode"] = Label()

		self["actions"] = NumberActionMap( [ "InfobarVmodeButtonActions" ],
			{
				"vmodeSelection": self.selectVMode
			})

		self.Timer = eTimer()
		self.Timer.callback.append(self.quit)
		self.selectVMode()

	def selectVMode(self):
		policy = config.av.policy_43
		if self.isWideScreen():
			policy = config.av.policy_169
		idx = policy.choices.index(policy.value)
		idx = (idx + 1) % len(policy.choices)
		policy.value = policy.choices[idx]
		self["videomode"].setText(policy.value)
		self.Timer.start(1000, True)

	def isWideScreen(self):
		from Components.Converter.ServiceInfo import WIDESCREEN
		service = self.session.nav.getCurrentService()
		info = service and service.info()
		return info.getInfo(iServiceInformation.sAspect) in WIDESCREEN

	def quit(self):
		self.Timer.stop()
		self.close()

class InfoBarAdditionalInfo:
	def __init__(self):
		self["RecordingPossible"] = Boolean(fixed=harddiskmanager.HDDCount() > 0)
		self["TimeshiftPossible"] = self["RecordingPossible"]
		self["ExtensionsAvailable"] = Boolean(fixed=1)
		# TODO: these properties should be queried from the input device keymap
		self["ShowTimeshiftOnYellow"] = Boolean(fixed=0)
		self["ShowAudioOnYellow"] = Boolean(fixed=0)
		self["ShowRecordOnRed"] = Boolean(fixed=0)

class InfoBarNotifications:
	def __init__(self):
		self.onExecBegin.append(self.checkNotifications)
		Notifications.notificationAdded.append(self.checkNotificationsIfExecing)
		self.onClose.append(self.__removeNotification)

	def __removeNotification(self):
		Notifications.notificationAdded.remove(self.checkNotificationsIfExecing)

	def checkNotificationsIfExecing(self):
		if self.execing:
			self.checkNotifications()

	def checkNotifications(self):
		notifications = Notifications.notifications
		if notifications:
			n = notifications[0]

			del notifications[0]
			cb = n[0]

			if n[3].has_key("onSessionOpenCallback"):
				n[3]["onSessionOpenCallback"]()
				del n[3]["onSessionOpenCallback"]

			if cb:
				dlg = self.session.openWithCallback(cb, n[1], *n[2], **n[3])
			elif not Notifications.current_notifications and n[4] == "ZapError":
				if n[3].has_key("timeout"):
					del n[3]["timeout"]
				n[3]["enable_input"] = False
				dlg = self.session.instantiateDialog(n[1], *n[2], **n[3])
				self.hide()
				dlg.show()
				self.notificationDialog = dlg
				eActionMap.getInstance().bindAction('', -maxint - 1, self.keypressNotification)
			else:
				dlg = self.session.open(n[1], *n[2], **n[3])

			# remember that this notification is currently active
			d = (n[4], dlg)
			Notifications.current_notifications.append(d)
			dlg.onClose.append(boundFunction(self.__notificationClosed, d))

	def closeNotificationInstantiateDialog(self):
		if hasattr(self, "notificationDialog"):
			self.session.deleteDialog(self.notificationDialog)
			del self.notificationDialog
			eActionMap.getInstance().unbindAction('', self.keypressNotification)

	def keypressNotification(self, key, flag):
		if flag:
			self.closeNotificationInstantiateDialog()

	def __notificationClosed(self, d):
		Notifications.current_notifications.remove(d)

class InfoBarServiceNotifications:
	def __init__(self):
		self.__event_tracker = ServiceEventTracker(screen=self, eventmap={
				iPlayableService.evEnd: self.serviceHasEnded
			})

	def serviceHasEnded(self):
#		print "service end!"
		try:
			self.setSeekState(self.SEEK_STATE_PLAY)
		except:
			pass

class InfoBarCueSheetSupport:
	CUT_TYPE_IN = 0
	CUT_TYPE_OUT = 1
	CUT_TYPE_MARK = 2
	CUT_TYPE_LAST = 3

	ENABLE_RESUME_SUPPORT = False

	def __init__(self, actionmap="InfobarCueSheetActions"):
		self["CueSheetActions"] = HelpableActionMap(self, actionmap,
			{
				"jumpPreviousMark": (self.jumpPreviousMark, _("Jump to previous marked position")),
				"jumpNextMark": (self.jumpNextMark, _("Jump to next marked position")),
				"toggleMark": (self.toggleMark, _("Toggle a cut mark at the current position"))
			}, prio=1)

		self.cut_list = [ ]
		self.is_closing = False
		self.__event_tracker = ServiceEventTracker(screen=self, eventmap={
				iPlayableService.evStart: self.__serviceStarted,
				iPlayableService.evCuesheetChanged: self.downloadCuesheet,
			})

	def __serviceStarted(self):
		if self.is_closing:
			return
#		print "new service started! trying to download cuts!"
		self.downloadCuesheet()

		self.resume_point = None
		if self.ENABLE_RESUME_SUPPORT:
			for (pts, what) in self.cut_list:
				if what == self.CUT_TYPE_LAST:
					last = pts
					break
			else:
				last = getResumePoint(self.session)
			if last is None:
				return
			# only resume if at least 10 seconds ahead, or <10 seconds before the end.
			seekable = self.__getSeekable()
			if seekable is None:
				return # Should not happen?
			length = seekable.getLength() or (None,0)
#			print "seekable.getLength() returns:", length
			# Hmm, this implies we don't resume if the length is unknown...
			if (last > 900000) and (not length[1]  or (last < length[1] - 900000)):
				self.resume_point = last
				l = last / 90000
				if "ask" in config.usage.on_movie_start.value or not length[1]:
					Notifications.AddNotificationWithCallback(self.playLastCB, MessageBox, _("Do you want to resume this playback?") + "\n" + (_("Resume position at %s") % ("%d:%02d:%02d" % (l/3600, l%3600/60, l%60))), timeout=30, default="yes" in config.usage.on_movie_start.value)
				elif config.usage.on_movie_start.value == "resume":
					Notifications.AddNotificationWithCallback(self.playLastCB, MessageBox, _("Resuming playback"), timeout=2, type=MessageBox.TYPE_INFO)

	def playLastCB(self, answer):
		if answer == True and self.resume_point:
			self.doSeek(self.resume_point)
		self.hideAfterResume()

	def hideAfterResume(self):
		if isinstance(self, InfoBarShowHide):
			self.hide()

	def __getSeekable(self):
		service = self.session.nav.getCurrentService()
		if service is None:
			return None
		return service.seek()

	def cueGetCurrentPosition(self):
		seek = self.__getSeekable()
		if seek is None:
			return None
		r = seek.getPlayPosition()
		if r[0]:
			return None
		return long(r[1])

	def cueGetEndCutPosition(self):
		ret = False
		isin = True
		for cp in self.cut_list:
			if cp[1] == self.CUT_TYPE_OUT:
				if isin:
					isin = False
					ret = cp[0]
			elif cp[1] == self.CUT_TYPE_IN:
				isin = True
		return ret

	def jumpPreviousNextMark(self, cmp, start=False):
		current_pos = self.cueGetCurrentPosition()
		if current_pos is None:
			return False
		mark = self.getNearestCutPoint(current_pos, cmp=cmp, start=start)
		if mark is not None:
			pts = mark[0]
		else:
			return False

		self.doSeek(pts)
		return True

	def jumpPreviousMark(self):
		# we add 5 seconds, so if the play position is <5s after
		# the mark, the mark before will be used
		self.jumpPreviousNextMark(lambda x: -x-5*90000, start=True)

	def jumpNextMark(self):
		if not self.jumpPreviousNextMark(lambda x: x-90000):
			self.doSeek(-1)

	def getNearestCutPoint(self, pts, cmp=abs, start=False):
		# can be optimized
		beforecut = True
		nearest = None
		bestdiff = -1
		instate = True
		if start:
			bestdiff = cmp(0 - pts)
			if bestdiff >= 0:
				nearest = [0, False]
		for cp in self.cut_list:
			if beforecut and cp[1] in (self.CUT_TYPE_IN, self.CUT_TYPE_OUT):
				beforecut = False
				if cp[1] == self.CUT_TYPE_IN:  # Start is here, disregard previous marks
					diff = cmp(cp[0] - pts)
					if start and diff >= 0:
						nearest = cp
						bestdiff = diff
					else:
						nearest = None
						bestdiff = -1
			if cp[1] == self.CUT_TYPE_IN:
				instate = True
			elif cp[1] == self.CUT_TYPE_OUT:
				instate = False
			elif cp[1] in (self.CUT_TYPE_MARK, self.CUT_TYPE_LAST):
				diff = cmp(cp[0] - pts)
				if instate and diff >= 0 and (nearest is None or bestdiff > diff):
					nearest = cp
					bestdiff = diff
		return nearest

	def toggleMark(self, onlyremove=False, onlyadd=False, tolerance=5*90000, onlyreturn=False):
		current_pos = self.cueGetCurrentPosition()
		if current_pos is None:
#			print "not seekable"
			return

		nearest_cutpoint = self.getNearestCutPoint(current_pos)

		if nearest_cutpoint is not None and abs(nearest_cutpoint[0] - current_pos) < tolerance:
			if onlyreturn:
				return nearest_cutpoint
			if not onlyadd:
				self.removeMark(nearest_cutpoint)
		elif not onlyremove and not onlyreturn:
			self.addMark((current_pos, self.CUT_TYPE_MARK))

		if onlyreturn:
			return None

	def addMark(self, point):
		insort(self.cut_list, point)
		self.uploadCuesheet()
		self.showAfterCuesheetOperation()

	def removeMark(self, point):
		self.cut_list.remove(point)
		self.uploadCuesheet()
		self.showAfterCuesheetOperation()

	def showAfterCuesheetOperation(self):
		if isinstance(self, InfoBarShowHide):
			self.doShow()

	def __getCuesheet(self):
		service = self.session.nav.getCurrentService()
		if service is None:
			return None
		return service.cueSheet()

	def uploadCuesheet(self):
		cue = self.__getCuesheet()

		if cue is None:
#			print "upload failed, no cuesheet interface"
			return
		cue.setCutList(self.cut_list)

	def downloadCuesheet(self):
		cue = self.__getCuesheet()

		if cue is None:
#			print "download failed, no cuesheet interface"
			self.cut_list = [ ]
		else:
			self.cut_list = cue.getCutList()

class InfoBarSummary(Screen):
	skin = """
	<screen position="0,0" size="132,64">
		<widget source="global.CurrentTime" render="Label" position="62,46" size="82,18" font="Regular;16" >
			<convert type="ClockToText">WithSeconds</convert>
		</widget>
		<widget source="session.RecordState" render="FixedLabel" text=" " position="62,46" size="82,18" zPosition="1" >
			<convert type="ConfigEntryTest">config.usage.blinking_display_clock_during_recording,True,CheckSourceBoolean</convert>
			<convert type="ConditionalShowHide">Blink</convert>
		</widget>
		<widget source="session.CurrentService" render="Label" position="6,4" size="120,42" font="Regular;18" >
			<convert type="ServiceName">Name</convert>
		</widget>
		<widget source="session.Event_Now" render="Progress" position="6,46" size="46,18" borderWidth="1" >
			<convert type="EventTime">Progress</convert>
		</widget>
	</screen>"""

# for picon:  (path="piconlcd" will use LCD picons)
#		<widget source="session.CurrentService" render="Picon" position="6,0" size="120,64" path="piconlcd" >
#			<convert type="ServiceName">Reference</convert>
#		</widget>

class InfoBarSummarySupport:
	def __init__(self):
		pass

	def createSummary(self):
		return InfoBarSummary

class InfoBarMoviePlayerSummary(Screen):
	skin = """
	<screen position="0,0" size="132,64">
		<widget source="global.CurrentTime" render="Label" position="62,46" size="64,18" font="Regular;16" halign="right" >
			<convert type="ClockToText">WithSeconds</convert>
		</widget>
		<widget source="session.RecordState" render="FixedLabel" text=" " position="62,46" size="64,18" zPosition="1" >
			<convert type="ConfigEntryTest">config.usage.blinking_display_clock_during_recording,True,CheckSourceBoolean</convert>
			<convert type="ConditionalShowHide">Blink</convert>
		</widget>
		<widget source="session.CurrentService" render="Label" position="6,4" size="120,42" font="Regular;18" >
			<convert type="ServiceName">Name</convert>
		</widget>
		<widget source="session.CurrentService" render="Progress" position="6,46" size="56,18" borderWidth="1" >
			<convert type="ServicePosition">Position</convert>
		</widget>
	</screen>"""
	def __init__(self, session, parent):
		Screen.__init__(self, session, parent=parent)
		self["state_summary"] = StaticText("")
		self["speed_summary"] = StaticText("")
		self["statusicon_summary"] = MultiPixmap()
		self.onShow.append(self.addWatcher)
		self.onHide.append(self.removeWatcher)

	def addWatcher(self):
		self.parent.onChangedEntry.append(self.selectionChanged)

	def removeWatcher(self):
		self.parent.onChangedEntry.remove(self.selectionChanged)

	def selectionChanged(self, state_summary, speed_summary, statusicon_summary):
		self["state_summary"].setText(state_summary)
		self["speed_summary"].setText(speed_summary)
		self["statusicon_summary"].setPixmapNum(int(statusicon_summary))

class InfoBarMoviePlayerSummarySupport:
	def __init__(self):
		pass

	def createSummary(self):
		return InfoBarMoviePlayerSummary

class InfoBarTeletextPlugin:
	def __init__(self):
		self.teletext_plugin = None
		for p in plugins.getPlugins(PluginDescriptor.WHERE_TELETEXT):
			self.teletext_plugin = p

		if self.teletext_plugin is not None:
			self["TeletextActions"] = HelpableActionMap(self, "InfobarTeletextActions",
				{
					"startTeletext": (self.startTeletext, _("View teletext..."))
				})
		else:
			print "no teletext plugin found!"

	def startTeletext(self):
		self.teletext_plugin and self.teletext_plugin(session=self.session, service=self.session.nav.getCurrentService())

class InfoBarSubtitleSupport(object):
	def __init__(self):
		object.__init__(self)
		self["SubtitleSelectionAction"] = HelpableActionMap(self, "InfobarSubtitleSelectionActions",
			{
				"subtitleSelection": (self.subtitleSelection, _("Subtitle selection...")),
			})

		self.selected_subtitle = None

		if isStandardInfoBar(self):
			self.subtitle_window = self.session.instantiateDialog(SubtitleDisplay)
			self.subtitle_window.setAnimationMode(0)
		else:
			from Screens.InfoBar import InfoBar
			self.subtitle_window = InfoBar.instance.subtitle_window

		self.subtitle_window.hide()

		self.__event_tracker = ServiceEventTracker(screen=self, eventmap={
				iPlayableService.evStart: self.__serviceChanged,
				iPlayableService.evEnd: self.__serviceChanged,
				iPlayableService.evUpdatedInfo: self.__updatedInfo
			})

	def getCurrentServiceSubtitle(self):
		service = self.session.nav.getCurrentService()
		return service and service.subtitle()

	def subtitleSelection(self):
		service = self.session.nav.getCurrentService()
		subtitle = service and service.subtitle()
		subtitlelist = subtitle and subtitle.getSubtitleList()
		if self.selected_subtitle or subtitlelist and len(subtitlelist)>0:
			from Screens.AudioSelection import SubtitleSelection
			self.session.open(SubtitleSelection, self)
		else:
			return 0

	def doCenterDVBSubs(self):
		service = self.session.nav.getCurrentlyPlayingServiceReference()
		servicepath = service and service.getPath()
		if servicepath and servicepath.startswith("/"):
			if service.toString().startswith("1:"):
				info = eServiceCenter.getInstance().info(service)
				service = info and info.getInfoString(service, iServiceInformation.sServiceref)
				config.subtitles.dvb_subtitles_centered.value = service and eDVBDB.getInstance().getFlag(eServiceReference(service)) & self.FLAG_CENTER_DVB_SUBS and True
				return
		service = self.session.nav.getCurrentService()
		info = service and service.info()
		config.subtitles.dvb_subtitles_centered.value = info and info.getInfo(iServiceInformation.sCenterDVBSubs) and True

	def subtitleQuickMenu(self):
		service = self.session.nav.getCurrentService()
		subtitle = service and service.subtitle()
		subtitlelist = subtitle and subtitle.getSubtitleList()
		if self.selected_subtitle and self.selected_subtitle != (0,0,0,0):
			from Screens.AudioSelection import QuickSubtitlesConfigMenu
			self.session.open(QuickSubtitlesConfigMenu, self)
		else:
			self.subtitleSelection()

	def __serviceChanged(self):
		if self.selected_subtitle:
			self.selected_subtitle = None
			self.subtitle_window.hide()

	def __updatedInfo(self):
		if not self.selected_subtitle:
			subtitle = self.getCurrentServiceSubtitle()
			cachedsubtitle = subtitle.getCachedSubtitle()
			if cachedsubtitle:
				self.enableSubtitle(cachedsubtitle)
				self.doCenterDVBSubs()

	def enableSubtitle(self, selectedSubtitle):
		subtitle = self.getCurrentServiceSubtitle()
		self.selected_subtitle = selectedSubtitle
		if subtitle and self.selected_subtitle:
			subtitle.enableSubtitles(self.subtitle_window.instance, self.selected_subtitle)
			self.subtitle_window.show()
			self.doCenterDVBSubs()
		else:
			if subtitle:
				subtitle.disableSubtitles(self.subtitle_window.instance)
			self.subtitle_window.hide()

	def restartSubtitle(self):
		if self.selected_subtitle:
			self.enableSubtitle(self.selected_subtitle)

class InfoBarServiceErrorPopupSupport:
	def __init__(self):
		self.__event_tracker = ServiceEventTracker(screen=self, eventmap={
				iPlayableService.evTuneFailed: self.__tuneFailed,
				iPlayableService.evTunedIn: self.__serviceStarted,
				iPlayableService.evStart: self.__serviceStarted
			})
		self.__serviceStarted()

	def __serviceStarted(self):
		self.closeNotificationInstantiateDialog()
		self.last_error = None
		Notifications.RemovePopup(id="ZapError")

	def __tuneFailed(self):
		if not config.usage.hide_zap_errors.value or not config.usage.remote_fallback_enabled.value:
			service = self.session.nav.getCurrentService()
			info = service and service.info()
			error = info and info.getInfo(iServiceInformation.sDVBState)
			if not config.usage.remote_fallback_enabled.value and (error == eDVBServicePMTHandler.eventMisconfiguration or error == eDVBServicePMTHandler.eventNoResources):
				self.session.nav.currentlyPlayingServiceReference = None
				self.session.nav.currentlyPlayingServiceOrGroup = None
			if error == self.last_error:
				error = None
			else:
				self.last_error = error

			error = {
				eDVBServicePMTHandler.eventNoResources: _("No free tuner!"),
				eDVBServicePMTHandler.eventTuneFailed: _("Tune failed!"),
				eDVBServicePMTHandler.eventNoPAT: _("No data on transponder!\n(Timeout reading PAT)"),
				eDVBServicePMTHandler.eventNoPATEntry: _("Service not found!\n(SID not found in PAT)"),
				eDVBServicePMTHandler.eventNoPMT: _("Service invalid!\n(Timeout reading PMT)"),
				eDVBServicePMTHandler.eventNewProgramInfo: None,
				eDVBServicePMTHandler.eventTuned: None,
				eDVBServicePMTHandler.eventSOF: None,
				eDVBServicePMTHandler.eventEOF: None,
				eDVBServicePMTHandler.eventMisconfiguration: _("Service unavailable!\nCheck tuner configuration!"),
			}.get(error) #this returns None when the key not exist in the dict

			if error and not config.usage.hide_zap_errors.value:
				self.closeNotificationInstantiateDialog()
				if hasattr(self, "dishDialog") and not self.dishDialog.dishState():
					Notifications.AddPopup(text=error, type=MessageBox.TYPE_ERROR, timeout=5, id="ZapError")

class InfoBarZoom:
	def __init__(self):
		self.zoomrate=0
		self.zoomin=1

		self["ZoomActions"] = HelpableActionMap(self, "InfobarZoomActions",
			{
				"ZoomInOut":(self.ZoomInOut, _("Zoom In/Out TV...")),
				"ZoomOff":(self.ZoomOff, _("Zoom Off...")),
			}, prio=2)

	def ZoomInOut(self):
		zoomval=0
		if self.zoomrate > 3:
			self.zoomin = 0
		elif self.zoomrate < -9:
			self.zoomin = 1

		if self.zoomin == 1:
			self.zoomrate += 1
		else:
			self.zoomrate -= 1

		if self.zoomrate < 0:
			zoomval=abs(self.zoomrate)+10
		else:
			zoomval=self.zoomrate
		# print "zoomRate:", self.zoomrate
		# print "zoomval:", zoomval
		file = open("/proc/stb/vmpeg/0/zoomrate", "w")
		file.write('%d' % int(zoomval))
		file.close()

	def ZoomOff(self):
		self.zoomrate = 0
		self.zoomin = 1
		f = open("/proc/stb/vmpeg/0/zoomrate", "w")
		f.write(str(0))
		f.close()

class InfoBarHdmi:
	def __init__(self):
		self.hdmi_enabled = False
		self.hdmi_enabled_full = False
		self.hdmi_enabled_pip = False

		if SystemInfo["HDMIin"]:
			if not self.hdmi_enabled_full:
				self.addExtension((self.getHDMIInFullScreen, self.HDMIInFull, lambda: True), "blue")
			if not self.hdmi_enabled_pip:
				self.addExtension((self.getHDMIInPiPScreen, self.HDMIInPiP, lambda: True), "green")
		self["HDMIActions"] = HelpableActionMap(self, "InfobarHDMIActions",
			{
				"HDMIin":(self.HDMIIn, _("Switch to HDMI in mode")),
				"HDMIinLong":(self.HDMIInLong, _("Switch to HDMI in mode")),
			}, prio=2)

	def HDMIInLong(self):
		if self.LongButtonPressed:
			if not hasattr(self.session, 'pip') and not self.session.pipshown:
				self.session.pip = self.session.instantiateDialog(PictureInPicture)
				self.session.pip.playService(hdmiInServiceRef())
				self.session.pip.show()
				self.session.pipshown = True
				self.session.pip.servicePath = self.servicelist.getCurrentServicePath()
			else:
				curref = self.session.pip.getCurrentService()
				if curref and curref.type != eServiceReference.idServiceHDMIIn:
					self.session.pip.playService(hdmiInServiceRef())
					self.session.pip.servicePath = self.servicelist.getCurrentServicePath()
				else:
					self.session.pipshown = False
					del self.session.pip

	def HDMIIn(self):
		if not self.LongButtonPressed:
			slist = self.servicelist
			curref = self.session.nav.getCurrentlyPlayingServiceOrGroup()
			if curref and curref.type != eServiceReference.idServiceHDMIIn:
				self.session.nav.playService(hdmiInServiceRef())
			else:
				self.session.nav.playService(slist.servicelist.getCurrent())

	def getHDMIInFullScreen(self):
		if not self.hdmi_enabled_full:
			return _("Turn on HDMI-IN Full screen mode")
		else:
			return _("Turn off HDMI-IN Full screen mode")

	def getHDMIInPiPScreen(self):
		if not self.hdmi_enabled_pip:
			return _("Turn on HDMI-IN PiP mode")
		else:
			return _("Turn off HDMI-IN PiP mode")

	def HDMIInPiP(self):
		if getMachineBuild() in ('dm7080', 'dm820', 'dm900', 'dm920'):
			f=open("/proc/stb/hdmi-rx/0/hdmi_rx_monitor","r")
			check=f.read()
			f.close()
			if check.startswith("off"):
				f=open("/proc/stb/audio/hdmi_rx_monitor","w")
				f.write("on")
				f.close()
				f=open("/proc/stb/hdmi-rx/0/hdmi_rx_monitor","w")
				f.write("on")
				f.close()
			else:
				f=open("/proc/stb/audio/hdmi_rx_monitor","w")
				f.write("off")
				f.close()
				f=open("/proc/stb/hdmi-rx/0/hdmi_rx_monitor","w")
				f.write("off")
				f.close()
		else:
			if not hasattr(self.session, 'pip') and not self.session.pipshown:
				self.hdmi_enabled_pip = True
				self.session.pip = self.session.instantiateDialog(PictureInPicture)
				self.session.pip.playService(hdmiInServiceRef())
				self.session.pip.show()
				self.session.pipshown = True
				self.session.pip.servicePath = self.servicelist.getCurrentServicePath()
			else:
				curref = self.session.pip.getCurrentService()
				if curref and curref.type != eServiceReference.idServiceHDMIIn:
					self.hdmi_enabled_pip = True
					self.session.pip.playService(hdmiInServiceRef())
					self.session.pip.servicePath = self.servicelist.getCurrentServicePath()
				else:
					self.hdmi_enabled_pip = False
					self.session.pipshown = False
					del self.session.pip

	def HDMIInFull(self):
		if getMachineBuild() in ('dm7080', 'dm820', 'dm900', 'dm920'):
			f=open("/proc/stb/hdmi-rx/0/hdmi_rx_monitor","r")
			check=f.read()
			f.close()
			if check.startswith("off"):
				f=open("/proc/stb/video/videomode","r")
				self.oldvideomode=f.read()
				f.close()
				f=open("/proc/stb/video/videomode_50hz","r")
				self.oldvideomode_50hz=f.read()
				f.close()
				f=open("/proc/stb/video/videomode_60hz","r")
				self.oldvideomode_60hz=f.read()
				f.close()
				f=open("/proc/stb/video/videomode","w")
				if getMachineBuild() in ('dm900', 'dm920'):
					f.write("1080p")
				else:
					f.write("720p")
				f.close()
				f=open("/proc/stb/audio/hdmi_rx_monitor","w")
				f.write("on")
				f.close()
				f=open("/proc/stb/hdmi-rx/0/hdmi_rx_monitor","w")
				f.write("on")
				f.close()
			else:
				f=open("/proc/stb/audio/hdmi_rx_monitor","w")
				f.write("off")
				f.close()
				f=open("/proc/stb/hdmi-rx/0/hdmi_rx_monitor","w")
				f.write("off")
				f.close()
				f=open("/proc/stb/video/videomode","w")
				f.write(self.oldvideomode)
				f.close()
				f=open("/proc/stb/video/videomode_50hz","w")
				f.write(self.oldvideomode_50hz)
				f.close()
				f=open("/proc/stb/video/videomode_60hz","w")
				f.write(self.oldvideomode_60hz)
				f.close()
		else:
			slist = self.servicelist
			curref = self.session.nav.getCurrentlyPlayingServiceOrGroup()
			if curref and curref.type != eServiceReference.idServiceHDMIIn:
				self.hdmi_enabled_full = True
				self.session.nav.playService(hdmiInServiceRef())
			else:
				self.hdmi_enabled_full = False
				self.session.nav.playService(slist.servicelist.getCurrent())

class InfoBarSleepTimer:
	def __init__(self):
		self.sleepTimer = eTimer()
		self.sleepStartTime = 0
		self.sleepTimer.callback.append(self.sleepTimerTimeout)

	def sleepTimerState(self):
		if self.sleepTimer.isActive():
			return (self.sleepStartTime - time()) / 60
		return 0

	def setSleepTimer(self, sleepTime, showMessage=True):
		print "[InfoBarSleepTimer] set sleeptimer", sleepTime
		if sleepTime:
			m = abs(sleepTime / 60)
			message = _("The sleep timer has been activated.") + "\n" + _("Delay:") + " " + _("%d minutes") % m
			self.sleepTimer.startLongTimer(sleepTime)
			self.sleepStartTime = time() + sleepTime
		else:
			message = _("The sleep timer has been disabled.")
			self.sleepTimer.stop()
		if showMessage:
			Notifications.AddPopup(message, type=MessageBox.TYPE_INFO, timeout=5)

	def sleepTimerTimeout(self):
		if config.usage.sleep_timer_action.value != "standby":
			isRecordTime = abs(self.session.nav.RecordTimer.getNextRecordingTime() - time()) <= 900 or self.session.nav.RecordTimer.getStillRecording() or abs(self.session.nav.RecordTimer.getNextZapTime() - time()) <= 900
			isPowerTime = abs(self.session.nav.PowerTimer.getNextPowerManagerTime() - time()) <= 900 or self.session.nav.PowerTimer.isProcessing(exceptTimer=0)
			if isRecordTime or isPowerTime:
				self.setSleepTimer(1800, False)
				if not Screens.Standby.inStandby:
					message = _("A Recording, RecordTimer or PowerTimer is running or begins in 15 minutes.\nExtend sleep timer 30 minutes. Your %s %s\nwill shut down after Recording or Powertimer event. Get in Standby now?") % (getMachineBrand(), getMachineName())
					self.session.openWithCallback(self.goStandby, MessageBox, message, MessageBox.TYPE_YESNO, timeout=int(config.usage.shutdown_msgbox_timeout.value), default=True)
				return
		if not Screens.Standby.inStandby:
			list = [ (_("Yes"), True),
					(_("No"), False),
					(_("Extend"), "extend") ]
			if config.usage.sleep_timer_action.value == "standby":
				message = _("A sleep timer wants to set your %s %s to standby.\nDo that now or set extend additional minutes?") % (getMachineBrand(), getMachineName())
			else:
				message = _("A sleep timer wants to shut down your %s %s.\nDo that now or set extend additional minutes?") % (getMachineBrand(), getMachineName())
			self.session.openWithCallback(self.sleepTimerTimeoutCallback, MessageBox, message, timeout=int(config.usage.shutdown_msgbox_timeout.value), simple=True, list=list, default=True)
		else:
			self.goStandby()

	def sleepTimerTimeoutCallback(self, answer):
		if answer == "extend":
			from Screens.SleepTimerEdit import SleepTimerEdit
			self.session.open(SleepTimerEdit)
		elif answer:
			self.goStandby()
		else:
			self.setSleepTimer(0)

	def goStandby(self, answer=None):
		if config.usage.sleep_timer_action.value == "standby" or answer:
			if not Screens.Standby.inStandby:
				print "[InfoBarSleepTimer] goto standby"
				self.session.open(Screens.Standby.Standby)
		elif answer is None:
			if not Screens.Standby.inStandby:
				if not Screens.Standby.inTryQuitMainloop:
					print "[InfoBarSleepTimer] goto deep standby"
					self.session.open(Screens.Standby.TryQuitMainloop, 1)
			else:
				print "[InfoBarSleepTimer] goto deep standby"
				quitMainloop(1)

#########################################################################################
# for displayed power or record timer messages in foreground and for callback execution #
#########################################################################################
class InfoBarOpenOnTopHelper:
	def __init__(self):
		pass

	def openInfoBarMessage(self, message, messageboxtyp, timeout=-1):
		try:
			self.session.open(MessageBox, message, messageboxtyp, timeout=timeout)
		except Exception, e:
			print "[InfoBarOpenMessage] Exception:", e

	def openInfoBarMessageWithCallback(self, callback, message, messageboxtyp, timeout=-1, default=True):
		try:
			self.session.openWithCallback(callback, MessageBox, message, messageboxtyp, timeout=timeout, default=default)
		except Exception, e:
			print "[openInfoBarMessageWithCallback] Exception:", e

	def openInfoBarSession(self, session, option=None):
		try:
			if option is None:
				self.session.open(session)
			else:
				self.session.open(session, option)
		except Exception, e:
			print "[openInfoBarSession] Exception:", e

#########################################################################################
# handle bsod (python crashes) and show information after crash                         #
#########################################################################################

from enigma import getBsodCounter, resetBsodCounter
class InfoBarHandleBsod:
	def __init__(self):
		self.lastBsod = 0
		self.infoBsodIsShown = False
		self.lastestBsodWarning = False
		self.checkBsodTimer = eTimer()
		self.checkBsodTimer.callback.append(self.checkBsodCallback)
		self.checkBsodTimer.start(1000, True)
		config.crash.bsodpython_ready.setValue(True)

	def checkBsodCallback(self):
		self.checkBsodTimer.start(1000, True)
		if Screens.Standby.inStandby or self.infoBsodIsShown:
			return
		bsodcnt = getBsodCounter()
		if config.crash.bsodpython.value and self.lastBsod < bsodcnt:
			maxbs = int(config.crash.bsodmax.value) or 100
			writelog = bsodcnt == 1 or not bsodcnt > int(config.crash.bsodhide.value) or bsodcnt >= maxbs
			txt = _("Your Receiver has a Software problem detected. Since the last reboot it has occured %d times.\n") %bsodcnt
			txt += _("(Attention: There will be a restart after %d crashes.)") %maxbs
			if writelog:
				txt += "\n" + "-"*80 + "\n"
				txt += _("A crashlog was %s created in '%s'") %((_('not'),'')[int(writelog)], config.crash.debug_path.value)
			#if not writelog:
			#	txt += "\n" + "-"*80 + "\n"
			#	txt += _("(It is set that '%s' crash logs are displayed and written.\nInfo: It will always write the first, last but one and lastest crash log.)") % str(int(config.crash.bsodhide.value) or _('never'))
			if bsodcnt >= maxbs:
				txt += "\n" + "-"*80 + "\n"
				txt += _("Warning: This is the last crash before an automatic restart is performed.\n")
				txt += _("Should the crash counter be reset to prevent a restart?")
				self.lastestBsodWarning = True
			try:
				self.session.openWithCallback(self.infoBsodCallback, MessageBox, txt, type=MessageBox.TYPE_ERROR, default=False, close_on_any_key=not self.lastestBsodWarning, showYESNO=self.lastestBsodWarning)
				self.infoBsodIsShown = True
			except Exception, e:
				#print "[InfoBarHandleBsod] Exception:", e
				self.checkBsodTimer.stop()
				self.checkBsodTimer.start(5000, True)
				self.infoBsodCallback(False)
				raise
		self.lastBsod = bsodcnt

	def infoBsodCallback(self, ret):
		if ret and self.lastestBsodWarning:
			resetBsodCounter()
		self.infoBsodIsShown = False
		self.lastestBsodWarning = False

#########################################################################################
