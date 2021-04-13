#!/usr/bin/python

from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.config import config, ConfigInteger, ConfigNumber, ConfigSelection, ConfigSubsection, ConfigYesNo, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Language import language
from Components.Pixmap import MovingPixmap
from Screens.InfoBar import MoviePlayer
from Screens.Screen import Screen
from Tools.Directories import fileExists, resolveFilename, SCOPE_PLUGINS
from enigma import eTimer

time_options = [("-180", _("-3 h.")), ("-150", _("-2 h. 30 " + _("min."))), ("-120", _("-2 h.")), ("-110", _("-1 h. 50 " + _("min."))), ("-100", _("-1 h. 40 " + _("min."))), ("-90", _("-1 h. 30 " + _("min."))), ("-85", _("-1 h. 25 " + _("min."))), ("-80", _("-1 h. 20 " + _("min."))), ("-75", _("-1 h. 15 " + _("min."))), ("-70", _("-1 h. 10 " + _("min."))), ("-65", _("-1 h. 5 " + _("min."))), ("-60", _("-1 h.")), ("-55", _("-55 " + _("min."))), ("-50", _("-50 " + _("min."))), ("-45", _("-45 " + _("min."))), ("-40", _("-40 " + _("min."))), ("-35", _("-35 " + _("min."))), ("-30", _("-30 " + _("min."))), ("-25", _("-25 " + _("min."))), ("-20", _("-20 " + _("min."))), ("-15", _("-15 " + _("min."))), ("-10", _("-10 " + _("min."))), ("-9", _("-9 " + _("min."))), ("-8", _("-8 " + _("min."))), ("-7", _("-7 " + _("min."))), ("-6", _("-6 " + _("min."))), ("-5", _("-5 " + _("min."))), ("-4", _("-4 " + _("min."))), ("-3", _("-3 " + _("min."))), ("-2", _("-2 " + _("min."))), ("-1", _("-1 " + _("min."))), ("-0.5", _("-30 " + _("sec."))), ("-0.25", _("-15 " + _("sec."))), ("-0.083", _("-5 " + _("sec."))), ("0.083", _("+5 " + _("sec."))), ("0.25", _("+15 " + _("sec."))), ("0.5", _("+30 " + _("sec."))), ("1", _("+1 " + _("min."))), ("1.5", _("+1 " + _("min.") + " 30 " + _("sec."))), ("2", _("+2 " + _("min."))), ("3", _("+3 " + _("min."))), ("4", _("+4 " + _("min."))), ("5", _("+5 " + _("min."))), ("6", _("+6 " + _("min."))), ("7", _("+7 " + _("min."))), ("8", _("+8 " + _("min."))), ("9", _("+9 " + _("min."))), ("10", _("+10 " + _("min."))), ("15", _("+15 " + _("min."))), ("20", _("+20 " + _("min."))), ("25", _("+25 " + _("min."))), ("30", _("+30 " + _("min."))), ("35", _("+35 " + _("min."))), ("40", _("+40 " + _("min."))), ("45", _("+45 " + _("min."))), ("50", _("+50 " + _("min."))), ("55", _("+55 " + _("min."))), ("60", _("+1 h.")), ("65", _("+1 h. 5 " + _("min."))), ("70", _("+1 h. 10 " + _("min."))), ("75", _("+1 h. 15 " + _("min."))), ("80", _("+1 h. 20 " + _("min."))), ("85", _("+1 h. 25 " + _("min."))), ("90", _("+1 h. 30 " + _("min."))), ("100", _("+1 h. 40 " + _("min."))), ("110", _("+1 h. 50 " + _("min."))), ("120", _("+2 h.")), ("150", _("+2 h. 30 " + _("min."))), ("180", _("+3 h."))]

config.plugins.timejump = ConfigSubsection()
config.plugins.timejump.activate = ConfigYesNo(default=True)
config.plugins.timejump.defaulttime = ConfigSelection(default="0.5", choices=time_options)
config.plugins.timejump.sensibility = ConfigInteger(default=10, limits=(1, 30))


class TimeJump(ConfigListScreen, Screen):
	skin = """
	<screen name="TimeJump" position="49,68" size="501,92" title="%s">
		<widget name="config" position="35,3" size="436,75" scrollbarMode="showOnDemand" transparent="1" />
		<widget name="cursor" position="115,51" size="20,21" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/spaTeam/icons/position_arrow.png" zPosition="5" alphatest="blend" />
		<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/spaTeam/icons/position_base.png" position="118,64" size="272,10" alphatest="blend" zPosition="4" />
		<widget source="session.CurrentService" render="PositionGauge" position="121,64" size="266,10" zPosition="3" pointer="/usr/lib/enigma2/python/Plugins/Extensions/spaTeam/icons/position_pointer.png:540,0" transparent="1">
			<convert type="ServicePosition">Gauge</convert>
		</widget>
		<widget name="time" position="38,58" size="75,17" font="Regular; 15" halign="center" transparent="0" zPosition="5" />
		<widget source="session.CurrentService" render="Label" position="394,58" size="75,17" font="Regular; 15" halign="center" transparent="0" zPosition="5">
			<convert type="ServicePosition">Length</convert>
		</widget>
		<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/spaTeam/icons/clock.png" position="7,8" size="22,21" alphatest="blend" zPosition="4" />
		<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/spaTeam/icons/arrow_left.png" position="9,54" size="19,23" alphatest="blend" zPosition="4" />
		<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/spaTeam/icons/arrow_right.png" position="477,54" size="19,23" alphatest="blend" zPosition="4" />
	</screen>""" % _("TimeJump")

	def __init__(self, session, instance, fwd):
		self.session = session
		Screen.__init__(self, session)
		self.infobarInstance = instance
		self.fwd = fwd
		if isinstance(session.current_dialog, MoviePlayer):
			self.dvd = False
			self.vdb = False
		elif DVDPlayer is not None and isinstance(session.current_dialog, DVDPlayer):
			self.dvd = True
			self.vdb = False
		else:
			self.dvd = False
			self.vdb = True
		self.percent = 0.0
		self.length = None
		service = session.nav.getCurrentService()
		if service:
			self.seek = service.seek()
			if self.seek:
				self.length = self.seek.getLength()
				position = self.seek.getPlayPosition()
				if self.length and position:
					if int(position[1]) > 0:
						self.percent = float(position[1]) * 100.0 / float(self.length[1])

		self.minuteInput = ConfigSelection(default=config.plugins.timejump.defaulttime.value, choices=time_options)
		self.positionEntry = ConfigSelection(choices=["<>"], default="<>")
		txt = _("Jump video time:")
		ConfigListScreen.__init__(self, [
			getConfigListEntry(txt, self.minuteInput),
			getConfigListEntry(_("Go to position:"), self.positionEntry)])

		self["cursor"] = MovingPixmap()
		self["time"] = Label()

		self["actions"] = ActionMap(["WizardActions"], {"back": self.exit}, -1)

		self.cursorTimer = eTimer()
		self.cursorTimer.callback.append(self.updateCursor)
		self.cursorTimer.start(200, False)

		self.onLayoutFinish.append(self.firstStart)

	def firstStart(self):
		self["config"].setCurrentIndex(1)

	def updateCursor(self):
		if self.length:
			if self.percent > 100.0:
				self.percent = 100.0
			elif self.percent < 0.0:
				self.percent = 0.0

			x = 119 + int(2.66 * self.percent)
			posy = self["cursor"].instance.position().y()
			self["cursor"].moveTo(x - 8, posy, 1)
			self["cursor"].startMoving()
			pts = int(float(self.length[1]) / 100.0 * self.percent)
			self["time"].setText("%d:%02d" % ((pts / 60 / 90000), ((pts / 90000) % 60)))

	def exit(self):
		self.cursorTimer.stop()
		ConfigListScreen.saveAll(self)
		self.close()

	def keyOK(self):
		sel = self["config"].getCurrent()[1]
		if sel == self.positionEntry:
			if self.length:
				if self.dvd: # seekTo() doesn't work for DVD Player
					oldPosition = self.seek.getPlayPosition()[1]
					newPosition = int(float(self.length[1]) / 100.0 * self.percent)
					if newPosition > oldPosition:
						pts = newPosition - oldPosition
					else:
						pts = -1 * (oldPosition - newPosition)
					DVDPlayer.doSeekRelative(self.infobarInstance, pts)
				else:
					self.seek.seekTo(int(float(self.length[1]) / 100.0 * self.percent))
				self.exit()
		elif sel == self.minuteInput:
			pts = int(float(self.minuteInput.value) * 60 * 90000)
			if self.dvd:
				global DVDPlayer
				DVDPlayer.doSeekRelative(self.infobarInstance, pts)
			elif self.vdb:
				global VideoDBPlayer
				VideoDBPlayer.doSeekRelative(self.infobarInstance, pts)
			else:
				self.seek.seekTo(self.seek.getPlayPosition()[1] + pts)
			self.exit()

	def keyLeft(self):
		sel = self["config"].getCurrent()[1]
		if sel == self.positionEntry:
			self.percent -= float(config.plugins.timejump.sensibility.value) / 10.0
			if self.percent < 0.0:
				self.percent = 0.0
		else:
			ConfigListScreen.keyLeft(self)
			if sel == self.minuteInput:
				pts = int(float(self.minuteInput.value) * 60 * 90000)
				length = float(self.length[1])
				if length <= 0:
					length = 1
				self.percent = float(self.seek.getPlayPosition()[1] + pts) * 100.0 / length
				if self.percent < 0.0:
					self.percent = 0.0
				if self.percent > 100.0:
					self.percent = 100.0

	def keyRight(self):
		sel = self["config"].getCurrent()[1]
		if sel == self.positionEntry:
			self.percent += float(config.plugins.timejump.sensibility.value) / 10.0
			if self.percent > 100.0:
				self.percent = 100.0
		else:
			ConfigListScreen.keyRight(self)
			if sel == self.minuteInput:
				pts = int(float(self.minuteInput.value) * 60 * 90000)
				length = float(self.length[1])
				if length <= 0:
					length = 1
				self.percent = float(self.seek.getPlayPosition()[1] + pts) * 100.0 / length
				if self.percent < 0.0:
					self.percent = 0.0
				if self.percent > 100.0:
					self.percent = 100.0

	def keyNumberGlobal(self, number):
		sel = self["config"].getCurrent()[1]
		if sel == self.positionEntry:
			self.percent = float(number) * 10.0
		else:
			ConfigListScreen.keyNumberGlobal(self, number)


class TimeJumpSetup(ConfigListScreen, Screen):
	skin = """
		<screen name="TimeJumpSetup" position="center,center" size="574,165" title="%s">
			<widget name="config" position="10,10" size="554,100" scrollbarMode="showOnDemand" transparent="1" />
			<widget name="key_red" position="157,121" size="140,40" valign="center" halign="center" zPosition="4" foregroundColor="white" font="Regular;18" transparent="1" /> 
			<widget name="key_green" position="317,121" size="140,40" valign="center" halign="center" zPosition="4" foregroundColor="white" font="Regular;18" transparent="1" /> 
			<ePixmap name="red" position="156,121" zPosition="2" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap name="green" position="317,121" zPosition="2" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
		</screen>""" % _("TimeJump Setup")

	def __init__(self, session, args=0):
		self.session = session
		Screen.__init__(self, session)

		self.list = []
		self.list.append(getConfigListEntry(_("Enable TimeJump (need restart):"), config.plugins.timejump.activate))
		self.list.append(getConfigListEntry(_("Default skip time:"), config.plugins.timejump.defaulttime))
		self.list.append(getConfigListEntry(_("Cursor Sensibility in slider (1-30):"), config.plugins.timejump.sensibility))

		ConfigListScreen.__init__(self, self.list)

		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("Ok"))

		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"red": self.exit,
			"green": self.save,
			"save": self.save,
			"cancel": self.exit,
			"ok": self.save,
		}, -2)

	def save(self):
		for x in self["config"].list:
			x[1].save()
		self.close(True, self.session)

	def exit(self):
		for x in self["config"].list:
			x[1].cancel()
		self.close()
##############################################
# This hack overwrites the functions seekFwdManual and seekBackManual of the InfoBarSeek class (MoviePlayer and DVDPlayer)


def timejump(instance, fwd=True):
	if instance and instance.session:
		instance.session.open(TimeJump, instance, fwd)


def timejumpBack(instance):
	timejump(instance, False)


def init_timejump():
	global DVDPlayer
	MoviePlayer.seekFwdManual = timejump
	MoviePlayer.seekBackManual = timejumpBack

	dvdPlayer = "%s%s" % (resolveFilename(SCOPE_PLUGINS), "Extensions/DVDPlayer/plugin.pyo")
	if fileExists(dvdPlayer) or fileExists("%sc" % dvdPlayer):
		from Plugins.Extensions.DVDPlayer.plugin import DVDPlayer
		DVDPlayer.seekFwdManual = timejump
		DVDPlayer.seekBackManual = timejumpBack
	else:
		DVDPlayer = None

	videodb = "%s%s" % (resolveFilename(SCOPE_PLUGINS), "Extensions/VideoDB/plugin.pyo")
	if fileExists(videodb):
		from Plugins.Extensions.VideoDB.Player import VideoDBPlayer
		VideoDBPlayer.seekFwdManual = timejump
		VideoDBPlayer.seekBackManual = timejumpBack

	youtube = "%s%s" % (resolveFilename(SCOPE_PLUGINS), "Extensions/YouTube/plugin.pyo")
	if fileExists(youtube):
		from Plugins.Extensions.YouTube.YouTubeUi import YouTubePlayer
		YouTubePlayer.left = timejumpBack
		YouTubePlayer.right = timejump

	mediaportal = "%s%s" % (resolveFilename(SCOPE_PLUGINS), "Extensions/MediaPortal/resources/simpleplayer.pyo")
	if fileExists(mediaportal):
		from Plugins.Extensions.MediaPortal.resources.simpleplayer import SimplePlayer
		SimplePlayer.seekBack = timejumpBack
		SimplePlayer.seekFwd = timejump


def TimeJumpAutostart(reason, **kwargs):
	if config.plugins.timejump.activate.value:
		if reason == 0: # startup
			init_timejump()


def TimeJumpMain(session, **kwargs):
	session.open(TimeJumpSetup)
