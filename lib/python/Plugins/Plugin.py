from os.path import join as pathjoin

from Components.config import ConfigSubsection, config
from Tools.LoadPixmap import LoadPixmap


class PluginDescriptor(object):
	"""An object to describe a plugin."""

	# Where to list the plugin. Note that there are different call arguments,
	# so you might not be able to combine them.
	# Common arguments are:
	# 	session
	# 	servicereference
	# 	reason
	# You have to ignore unknown kwargs!
	#
	# Argument: session
	WHERE_EXTENSIONSMENU = 1
	WHERE_MAINMENU = 2
	WHERE_PLUGINMENU = 3
	# Argument: session, serviceref (currently selected).
	WHERE_MOVIELIST = 4
	# Argument: menuid. Fnc must return list with menuitems (4-tuple of name, fnc to call, entryid or None, weight or None).
	WHERE_MENU = 5
	# Argument: reason (0=start, 1=end).
	WHERE_AUTOSTART = 6
	# Start as wizard. In that case, fnc must be tuple (priority, class) with class being a screen class!
	WHERE_WIZARD = 7
	# Like autostart, but for a session. Currently, only session starts are
	# delivered, and only on pre-loaded plugins.
	WHERE_SESSIONSTART = 8
	# Arguments: session, serviceref. Start as teletext plugin.
	WHERE_TELETEXT = 9
	# File-scanner, fnc must return a list of Scanners.
	WHERE_FILESCAN = 10
	# Fnc must take an interface name as parameter and return None if the plugin supports an extended setup
	# or return a function which is called with session and the interface name for extended setup of this interface.
	WHERE_NETWORKSETUP = 11
	# Show this plugin (or a choicebox with all of them) for long INFO keypress or return a function which is
	# called with session and the interface name for extended setup of this interface.
	WHERE_EVENTINFO = 12
	# Arguments: reason (True=Networkconfig read finished, False=Networkconfig reload initiated)
	WHERE_NETWORKCONFIG_READ = 13
	WHERE_AUDIOMENU = 14
	# If fnc is 'SoftwareSupported' or 'AdvancedSoftwareSupported' must take a parameter and return None if the
	# plugin should not be displayed inside Softwaremanger or return a function which is called with session
	# and 'None' as parameter to call the plugin from the Softwaremanager menus. "menuEntryName" and
	# "menuEntryDescription" should be provided to name and describe the new menu entry.
	WHERE_SOFTWAREMANAGER = 15
	# Arguments: session, serviceref (currently selected). Start as channellist context menu plugin.
	WHERE_CHANNEL_CONTEXT_MENU = 16
	# The fnc must take an interface name as parameter and return None if the plugin supports an extended setup
	# or return a function which is called with session and the interface name for extended setup of this interface.
	WHERE_NETWORKMOUNTS = 17
	WHERE_VIXMENU = 18
	# Override internal RecordTimer navigation instance fnc must return the custom instance or None to skip it.
	WHERE_RECORDTIMER = 19
	WHERE_SATCONFIGCHANGED = 20
	WHERE_SERVICESCAN = 21
	WHERE_EXTENSIONSINGLE = 22
	# Support zap hook to modify the service ref.
	WHERE_CHANNEL_ZAP = 23
	# Arguments: reason, session, instance, type.
	WHERE_INFOBARLOADED = 24

	# Argument: session
	WHERE_BUTTONSETUP = 25

	def __init__(self, name="Plugin", where=None, description="", icon=None, fnc=None, wakeupfnc=None, needsRestart=None, internal=False, weight=0):
		self.name = name
		if not where:
			where = []
		self.where = where if isinstance(where, list) else [where]
		self.description = description
		if icon is None or isinstance(icon, str):
			self.iconstr = icon
			self._icon = None
		else:
			self.iconstr = None
			self._icon = icon
		self._fnc = fnc
		self.wakeupfnc = wakeupfnc
		self.needsRestart = needsRestart
		self.internal = internal
		self.weight = weight
		self.path = None

	def __call__(self, *args, **kwargs):
		if callable(self._fnc):
			return self._fnc(*args, **kwargs)
		else:
			print("[Plugin] Error: PluginDescriptor called without a function!")
			return []

	def __getattribute__(self, name):
		if name == '__call__':
			return self._fnc is not None and self._fnc or {}
		return object.__getattribute__(self, name)

	def updateIcon(self, path):
		self.path = path

	def getWakeupTime(self):
		return self.wakeupfnc and self.wakeupfnc() or -1

	@property
	def icon(self):
		return LoadPixmap(pathjoin(self.path, self.iconstr)) if self.iconstr and self.path else self._icon

	def __eq__(self, other):
		return self._fnc == other._fnc

	def __ne__(self, other):
		return self._fnc != other._fnc

	def __lt__(self, other):
		if self.weight < other.weight:
			return True
		elif self.weight == other.weight:
			return self.name < other.name
		else:
			return False

	def __gt__(self, other):
		return other < self

	def __ge__(self, other):
		return not self < other

	def __le__(self, other):
		return not other < self
