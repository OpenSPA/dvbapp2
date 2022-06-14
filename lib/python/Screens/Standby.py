from __future__ import print_function
import os
import struct
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.config import config
from Components.AVSwitch import AVSwitch
from Components.Console import Console
from Components.SystemInfo import SystemInfo
from Components.Harddisk import harddiskmanager
from GlobalActions import globalActionMap
from enigma import eDVBVolumecontrol, eTimer, eDVBLocalTimeHandler, eServiceReference
from boxbranding import getMachineBrand, getMachineName, getBoxType, getBrandOEM, getMachineBuild
import Tools.Notifications
from time import localtime, time
import Screens.InfoBar
from gettext import dgettext
import Components.RecordingConfig

inStandby = None
TVinStandby = None
StartWithPower = False

QUIT_SHUTDOWN = 1
QUIT_REBOOT = 2
QUIT_RESTART = 3
QUIT_UPGRADE_FP = 4
QUIT_ERROR_RESTART = 5
QUIT_DEBUG_RESTART = 6
QUIT_MAINT = 16
QUIT_UPGRADE_PROGRAM = 42
QUIT_IMAGE_RESTORE = 43
QUIT_UPGRADE_FRONTPANEL = 44
QUIT_WOLSHUTDOWN = 45

class TVstate: #load in Navigation
	def __init__(self):
		global TVinStandby
		if TVinStandby is not None:
			print("[Standby] only one TVstate instance is allowed!")
		TVinStandby = self

		try:
			import Components.HdmiCec
			self.hdmicec_instance = Components.HdmiCec.hdmi_cec.instance
			self.hdmicec_ok = self.hdmicec_instance and config.hdmicec.enabled.value
		except:
			self.hdmicec_ok = False

		if not self.hdmicec_ok:
			print('[Standby] HDMI-CEC is not enabled or unavailable !!!')

	def skipHdmiCecNow(self, value):
		if self.hdmicec_ok:
			if value is True or value is False:
				self.hdmicec_instance.tv_skip_messages = value
			elif 'zaptimer' in value:
				self.hdmicec_instance.tv_skip_messages = config.hdmicec.control_tv_wakeup.value and not config.hdmicec.tv_wakeup_zaptimer.value and inStandby
			elif 'zapandrecordtimer' in value:
				self.hdmicec_instance.tv_skip_messages = config.hdmicec.control_tv_wakeup.value and not config.hdmicec.tv_wakeup_zapandrecordtimer.value and inStandby
			elif 'wakeuppowertimer' in value:
				self.hdmicec_instance.tv_skip_messages = config.hdmicec.control_tv_wakeup.value and not config.hdmicec.tv_wakeup_wakeuppowertimer.value and inStandby

	def getTVstandby(self, value):
		if self.hdmicec_ok:
			if 'zaptimer' in value:
				return config.hdmicec.control_tv_wakeup.value and not config.hdmicec.tv_wakeup_zaptimer.value
			elif 'zapandrecordtimer' in value:
				return config.hdmicec.control_tv_wakeup.value and not config.hdmicec.tv_wakeup_zapandrecordtimer.value
			elif 'wakeuppowertimer' in value:
				return config.hdmicec.control_tv_wakeup.value and not config.hdmicec.tv_wakeup_wakeuppowertimer.value
			elif 'waitfortimesync' in value:
				return config.hdmicec.control_tv_wakeup.value and not (config.hdmicec.deepstandby_waitfortimesync.value and config.workaround.deeprecord.value)
		return False

	def getTVstate(self, value):
		if self.hdmicec_ok:
			if not config.hdmicec.check_tv_state.value or self.hdmicec_instance.sendMessagesIsActive():
				return False
			elif value == 'on':
				return value in self.hdmicec_instance.tv_powerstate and config.hdmicec.control_tv_standby.value
			elif value == 'standby':
				return value in self.hdmicec_instance.tv_powerstate and config.hdmicec.control_tv_wakeup.value
			elif value == 'active':
				return 'on' in self.hdmicec_instance.tv_powerstate and self.hdmicec_instance.activesource
			elif value == 'notactive':
				return 'standby' in self.hdmicec_instance.tv_powerstate or not self.hdmicec_instance.activesource
		return False

	def setTVstate(self, value):
		if self.hdmicec_ok:
			if value == 'on' or (value == 'power' and config.hdmicec.handle_deepstandby_events.value and not self.hdmicec_instance.handleTimer.isActive()):
				self.hdmicec_instance.wakeupMessages()
			elif value == 'standby':
				self.hdmicec_instance.standbyMessages()

def setLCDModeMinitTV(value):
	try:
		f = open("/proc/stb/lcd/mode", "w")
		f.write(value)
		f.close()
	except:
		pass

class Standby2(Screen):
	################################################
	# openspa: added StartWithPower variable 
	# to detect when starting with the power button
	################################################
	def Powerb(self):
		global StartWithPower
		StartWithPower = True
		self.Power()

	def Power(self):
		print("[Standby] leave standby")
		SystemInfo["StandbyState"] = False

		if os.path.exists("/usr/script/StandbyLeave.sh"):
			Console().ePopen("/usr/script/StandbyLeave.sh &")

		if (getBrandOEM() in ('fulan', 'clap', 'dinobot') or getMachineBuild() in ('gbmv200', 'sf8008', 'sf8008m', 'ustym4kpro', 'beyonwizv2', 'viper4k')):
			try:
				open("/proc/stb/hdmi/output", "w").write("on")
			except:
				pass
		#set input to encoder
		self.avswitch.setInput("ENCODER")
		#restart last played service
		#unmute adc
		self.leaveMute()
		# set LCDminiTV
		if SystemInfo["Display"] and SystemInfo["LCDMiniTV"]:
			setLCDModeMinitTV(config.lcd.modeminitv.value)
		#kill me
		self.close(True)

	# normally handle only key's 'make' event
	def Power_make(self):
		if (config.usage.on_short_powerpress.value != "standby_noTVshutdown"):
			self.Power()

	# with the option "standby_noTVshutdown", use 'break' event / allow turning off the TV by a 'long' key press in standby
	# avoid waking from standby by ignoring the key's 'break' event after the 'long' and subsequent 'repeat' events.
	def Power_long(self):
		if (config.usage.on_short_powerpress.value == "standby_noTVshutdown"):
			self.TVoff()
			self.ignoreKeyBreakTimer.start(250, 1)

	def Power_repeat(self):
		if (config.usage.on_short_powerpress.value == "standby_noTVshutdown") and self.ignoreKeyBreakTimer.isActive():
			self.ignoreKeyBreakTimer.start(250, 1)

	def Power_break(self):
		if (config.usage.on_short_powerpress.value == "standby_noTVshutdown") and not self.ignoreKeyBreakTimer.isActive():
			self.Power()

	def TVoff(self):
		print("[Standby] TVoff")
		TVinStandby.skipHdmiCecNow(False)
		TVinStandby.setTVstate('standby')

	def setMute(self):
		if eDVBVolumecontrol.getInstance().isMuted():
			self.wasMuted = 1
			print("[Standby] mute already active")
		else:
			self.wasMuted = 0
			eDVBVolumecontrol.getInstance().volumeToggleMute()

	def leaveMute(self):
		if self.wasMuted == 0:
			eDVBVolumecontrol.getInstance().volumeToggleMute()

	def __init__(self, session):
		Screen.__init__(self, session)
		self.skinName = "Standby"
		self.avswitch = AVSwitch()

		print("[Standby] enter standby")
		SystemInfo["StandbyState"] = True

		if os.path.exists("/usr/script/StandbyEnter.sh"):
			Console().ePopen("/usr/script/StandbyEnter.sh &")

		self["actions"] = ActionMap(["StandbyActions"],
		{
			"power": self.Powerb,
			"power_make": self.Power_make,
			"power_break": self.Power_break,
			"power_long": self.Power_long,
			"power_repeat": self.Power_repeat,
			"discrete_on": self.Powerb
		}, -1)

		globalActionMap.setEnabled(False)

		self.ignoreKeyBreakTimer = eTimer()
		self.standbyStopServiceTimer = eTimer()
		self.standbyStopServiceTimer.callback.append(self.stopService)
		self.timeHandler = None

		#mute adc
		self.setMute()

		if SystemInfo["Display"] and SystemInfo["LCDMiniTV"]:
			# set LCDminiTV off
			setLCDModeMinitTV("0")

		self.paused_service = None
		self.prev_running_service = None

		self.prev_running_service = self.session.nav.getCurrentlyPlayingServiceOrGroup()
		service = self.prev_running_service and self.prev_running_service.toString()
		if service:
			if service.startswith("1:") and service.rsplit(":", 1)[1].startswith("/"):
				self.paused_service = self.session.current_dialog
				self.paused_service.pauseService()
		if not self.paused_service:
			self.timeHandler = eDVBLocalTimeHandler.getInstance()
			if self.timeHandler.ready():
				if self.session.nav.getCurrentlyPlayingServiceOrGroup():
					self.stopService()
				else:
					self.standbyStopServiceTimer.startLongTimer(5)
				self.timeHandler = None
			else:
				if config.misc.SyncTimeUsing.value == 0:
					self.timeHandler.m_timeUpdated.get().append(self.stopService)
				else:
					self.standbyStopServiceTimer.startLongTimer(5)
					self.timeHandler = None


		if self.session.pipshown:
			from Screens.InfoBar import InfoBar
			InfoBar.instance and hasattr(InfoBar.instance, "showPiP") and InfoBar.instance.showPiP()

		#set input to vcr scart
		if SystemInfo["ScartSwitch"]:
			self.avswitch.setInput("SCART")
		else:
			self.avswitch.setInput("AUX")
		if (getBrandOEM() in ('fulan', 'clap', 'dinobot') or getMachineBuild() in ('gbmv200', 'sf8008', 'sf8008m', 'ustym4kpro', 'beyonwizv2', 'viper4k')):
			try:
				open("/proc/stb/hdmi/output", "w").write("off")
			except:
				pass

		if int(config.usage.hdd_standby_in_standby.value) != -1: # HDD standby timer value (box in standby) / -1 = same as when box is active
			for hdd in harddiskmanager.HDDList():
				hdd[1].setIdleTime(int(config.usage.hdd_standby_in_standby.value))

		self.onFirstExecBegin.append(self.__onFirstExecBegin)
		self.onClose.append(self.__onClose)

	def __onClose(self):
		global inStandby
		inStandby = None
		self.standbyStopServiceTimer.stop()
		self.timeHandler and self.timeHandler.m_timeUpdated.get().remove(self.stopService)
		if self.paused_service:
			self.paused_service.unPauseService()
		elif self.prev_running_service:
			service = self.prev_running_service.toString()
			if config.servicelist.startupservice_onstandby.value:
				self.session.nav.playService(eServiceReference(config.servicelist.startupservice.value))
				from Screens.InfoBar import InfoBar
				InfoBar.instance and InfoBar.instance.servicelist.correctChannelNumber()
			else:
				self.session.nav.playService(self.prev_running_service)
		self.session.screen["Standby"].boolean = False
		globalActionMap.setEnabled(True)
		for hdd in harddiskmanager.HDDList():
			hdd[1].setIdleTime(int(config.usage.hdd_standby.value)) # HDD standby timer value (box active)

	def __onFirstExecBegin(self):
		global inStandby
		global StartWithPower
		StartWithPower = False
		inStandby = self
		self.session.screen["Standby"].boolean = True
		config.misc.standbyCounter.value += 1

	def createSummary(self):
		return StandbySummary

	def stopService(self):
		self.prev_running_service = self.session.nav.getCurrentlyPlayingServiceOrGroup()
		self.session.nav.stopService()

class Standby(Standby2):
	def __init__(self, session):
		if Screens.InfoBar.InfoBar and Screens.InfoBar.InfoBar.instance and Screens.InfoBar.InfoBar.ptsGetTimeshiftStatus(Screens.InfoBar.InfoBar.instance):
			self.skin = """<screen position="0,0" size="0,0"/>"""
			Screen.__init__(self, session)
			self.onFirstExecBegin.append(self.showMessageBox)
			self.onHide.append(self.close)
		else:
			Standby2.__init__(self, session)
			self.skinName = "Standby"

	def showMessageBox(self):
		Screens.InfoBar.InfoBar.checkTimeshiftRunning(Screens.InfoBar.InfoBar.instance, self.showMessageBoxcallback)

	def showMessageBoxcallback(self, answer):
		if answer:
			self.onClose.append(self.doStandby)

	def doStandby(self):
		Tools.Notifications.AddNotification(Screens.Standby.Standby2)


class StandbySummary(Screen):
	if getBoxType() in ('gb800ue', 'gb800ueplus', 'gbquad', 'gbquad4k', 'gbquadplus', 'gbue4k', 'gbultraue', 'gbultraueh', 'sf208', 'sf228', 'vusolo4k', 'vuuno4kse', 'vuultimo4k', 'vuduo4k'):
		def __init__(self, session, what = None):
			root = "/usr/share/enigma2/display/clock_skin/"
			try:
				what = open(root+"active").read()
			except:
				what = "clock_lcd_analog.xml"
			tmpskin = root+what
			self.skin = open(tmpskin,'r').read()
			Screen.__init__(self, session)
	else:
		skin = """
		<screen position="0,0" size="132,64">
			<widget source="global.CurrentTime" render="Label" position="0,0" size="132,64" font="Regular;40" halign="center">
				<convert type="ClockToText" />
			</widget>
			<widget source="session.RecordState" render="FixedLabel" text=" " position="0,0" size="132,64" zPosition="1" >
				<convert type="ConfigEntryTest">config.usage.blinking_display_clock_during_recording,True,CheckSourceBoolean</convert>
				<convert type="ConditionalShowHide">Blink</convert>
			</widget>
		</screen>"""

from enigma import quitMainloop, iRecordableService
from Screens.MessageBox import MessageBox
from time import time
from Components.Task import job_manager

class QuitMainloopScreen(Screen):
	def __init__(self, session, retvalue=QUIT_SHUTDOWN):
		self.skin = """<screen name="QuitMainloopScreen" position="fill" flags="wfNoBorder">
			<ePixmap pixmap="icons/input_info.png" position="c-27,c-60" size="53,53" alphatest="on" />
			<widget name="text" position="center,c+5" size="720,100" font="Regular;22" halign="center" />
		</screen>"""
		Screen.__init__(self, session)
		from Components.Label import Label
		text = {
			QUIT_SHUTDOWN: _("Your %s %s is shutting down") % (getMachineBrand(), getMachineName()),
			QUIT_REBOOT: _("Your %s %s is rebooting") % (getMachineBrand(), getMachineName()),
			QUIT_RESTART: _("The user interface of your %s %s is restarting") % (getMachineBrand(), getMachineName()),
			QUIT_UPGRADE_FP: _("Your frontprocessor will be upgraded\nPlease wait until your %s %s reboots\nThis may take a few minutes") % (getMachineBrand(), getMachineName()),
			QUIT_ERROR_RESTART: _("The user interface of your %s %s is restarting\ndue to an error in StartEnigma.py") % (getMachineBrand(), getMachineName()),
			QUIT_MAINT: _("Your %s %s is rebooting into Recovery Mode") % (getMachineBrand(), getMachineName()),
			QUIT_UPGRADE_PROGRAM: _("Upgrade in progress\nPlease wait until your %s %s reboots\nThis may take a few minutes") % (getMachineBrand(), getMachineName()),
			QUIT_IMAGE_RESTORE: _("Reflash in progress\nPlease wait until your %s %s reboots\nThis may take a few minutes") % (getMachineBrand(), getMachineName()),
			QUIT_UPGRADE_FRONTPANEL: _("Your front panel will be upgraded\nThis may take a few minutes"),
			QUIT_WOLSHUTDOWN: _("Your %s %s goes to WOL") % (getMachineBrand(), getMachineName())
			}.get(retvalue)
		self["text"] = Label(text)

inTryQuitMainloop = False
quitMainloopCode = 1

class TryQuitMainloop(MessageBox):
	def __init__(self, session, retvalue=QUIT_SHUTDOWN, timeout=-1, default_yes = True):
		self.retval = retvalue
		self.ptsmainloopvalue = retvalue
		recordings = session.nav.getRecordings(False, Components.RecordingConfig.recType(config.recording.warn_box_restart_rec_types.getValue()))
		jobs = len(job_manager.getPendingJobs())
		inTimeshift = Screens.InfoBar.InfoBar and Screens.InfoBar.InfoBar.instance and Screens.InfoBar.InfoBar.ptsGetTimeshiftStatus(Screens.InfoBar.InfoBar.instance)
		self.connected = False
		reason = ""
		next_rec_time = -1
		if not recordings:
			next_rec_time = session.nav.RecordTimer.getNextRecordingTime()
#		if jobs:
#			reason = (ngettext("%d job is running in the background!", "%d jobs are running in the background!", jobs) % jobs) + '\n'
#			if jobs == 1:
#				job = job_manager.getPendingJobs()[0]
#				if job.name == "VFD Checker":
#					reason = ""
#				else:
#					reason += "%s: %s (%d%%)\n" % (job.getStatustext(), job.name, int(100*job.progress/float(job.end)))
#			else:
#				reason += (_("%d jobs are running in the background!") % jobs) + '\n'
		if inTimeshift:
			reason = _("You seem to be in timeshift!") + '\n'
			default_yes = True
			timeout = 30
		if recordings or (next_rec_time > 0 and (next_rec_time - time()) < 360):
			reason = _("Recording(s) are in progress or coming up in few seconds!") + '\n'
			default_yes = False
			timeout = 30

		if reason and inStandby:
			session.nav.record_event.append(self.getRecordEvent)
			self.skinName = ""
		elif reason and not inStandby:
			text = {
				QUIT_SHUTDOWN: _("Really shutdown now?"),
				QUIT_REBOOT: _("Really reboot now?"),
				QUIT_RESTART: _("Really restart now?"),
				QUIT_UPGRADE_FP: _("Really upgrade the frontprocessor and reboot now?"),
				QUIT_MAINT: _("Really reboot into Recovery Mode?"),
				QUIT_UPGRADE_PROGRAM: _("Really upgrade your %s %s and reboot now?") % (getMachineBrand(), getMachineName()),
				QUIT_IMAGE_RESTORE: _("Really reflash your %s %s and reboot now?") % (getMachineBrand(), getMachineName()),
				QUIT_UPGRADE_FRONTPANEL: _("Really upgrade the front panel and reboot now?"),
				QUIT_WOLSHUTDOWN: _("Really WOL now?")
				}.get(retvalue)
			if text:
				MessageBox.__init__(self, session, reason + text, type = MessageBox.TYPE_YESNO, timeout = timeout, default = default_yes)
				self.skinName = "MessageBoxSimple"
				session.nav.record_event.append(self.getRecordEvent)
				self.connected = True
				self.onShow.append(self.__onShow)
				self.onHide.append(self.__onHide)
				return
		self.skin = """<screen position="1310,0" size="0,0"/>"""
		Screen.__init__(self, session)
		self.close(True)

	def getRecordEvent(self, recservice, event):
		if event == iRecordableService.evEnd and config.timeshift.isRecording.value:
			return
		else:
			if event == iRecordableService.evEnd:
				recordings = self.session.nav.getRecordings(False, Components.RecordingConfig.recType(config.recording.warn_box_restart_rec_types.getValue()))
				if not recordings: # no more recordings exist
					rec_time = self.session.nav.RecordTimer.getNextRecordingTime()
					if rec_time > 0 and (rec_time - time()) < 360:
						self.initTimeout(360) # wait for next starting timer
						self.startTimer()
					else:
						self.close(True) # immediate shutdown
			elif event == iRecordableService.evStart:
				self.stopTimer()

	def close(self, value):
		global quitMainloopCode
		if self.connected:
			self.connected = False
			self.session.nav.record_event.remove(self.getRecordEvent)
		if value:
			self.hide()
			if self.retval == QUIT_SHUTDOWN:
				config.misc.DeepStandby.value = True
			config.misc.StartMode.value = self.retval
			config.misc.StartMode.save()
			self.session.nav.stopService()
			self.quitScreen = self.session.instantiateDialog(QuitMainloopScreen, retvalue=self.retval)
			self.quitScreen.show()
			print("[Standby] quitMainloop #1")
			quitMainloopCode = self.retval
			if SystemInfo["Display"] and SystemInfo["LCDMiniTV"]:
				# set LCDminiTV off / fix a deep-standby-crash on some boxes / gb4k
				print("[Standby] LCDminiTV off")
				setLCDModeMinitTV("0")
			if getBoxType() == "vusolo4k":  #workaround for white display flash
				open("/proc/stb/fp/oled_brightness", "w").write("0")
			quitMainloop(self.retval)
		else:
			MessageBox.close(self, True)

	def __onShow(self):
		global inTryQuitMainloop
		inTryQuitMainloop = True

	def __onHide(self):
		global inTryQuitMainloop
		inTryQuitMainloop = False

class DualMode(Screen):
	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		self["myActionMap"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"ok": self.goAndroid,
			"cancel": self.close,
		}, -1)
		self.onShown.append(self.switchAndroid)

	def goAndroid(self, answer):
		if answer is True:
			with open('/dev/block/by-name/flag', 'wb') as f:
				f.write(struct.pack("B", 0))
			self.session.open(TryQuitMainloop, 2)
		else:
			self.close()

	def switchAndroid(self):
		self.onShown.remove(self.switchAndroid)
		self.session.openWithCallback(self.goAndroid, MessageBox, _("\n Do you want to switch Enigma2 with Android...?"))
