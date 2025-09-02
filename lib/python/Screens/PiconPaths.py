from Screens.Screen import Screen
from Screens.Setup import setupdom
from Screens.LocationBox import PiconLocationBox
from Screens.MessageBox import MessageBox
from Components.Label import Label
from Components.config import config, ConfigSelection, getConfigListEntry, configfile, ConfigText, ConfigYesNo, ConfigNothing
from Components.ConfigList import ConfigListScreen
from Components.ActionMap import ActionMap
from Components.Pixmap import Pixmap
from Tools.Directories import fileExists
from Components.UsageConfig import preferredPath
from Components.Sources.Boolean import Boolean
from Components.Sources.StaticText import StaticText
from Components.SystemInfo import SystemInfo
from Components.Harddisk import harddiskmanager
from boxbranding import getMachineBrand, getMachineName
import os
import six

hddchoises = []
for p in harddiskmanager.getMountedPartitions():
	if os.path.exists(p.mountpoint):
		d = os.path.normpath(p.mountpoint)
		if p.mountpoint != '/':
			hddchoises.append((p.mountpoint, d + '/picon/'))

class SetupSummary(Screen):
	def __init__(self, session, parent):
		Screen.__init__(self, session, parent = parent)
		self["SetupTitle"] = StaticText(_(parent.setup_title))
		self["entry"] = StaticText("")
		self["value"] = StaticText("")
		self.onShow.append(self.addWatcher)
		self.onHide.append(self.removeWatcher)

	def addWatcher(self):
		self.parent.onChangedEntry.append(self.selectionChanged)
		self.parent["config"].onSelectionChanged.append(self.selectionChanged)
		self.selectionChanged()

	def removeWatcher(self):
		self.parent.onChangedEntry.remove(self.selectionChanged)
		self.parent["config"].onSelectionChanged.remove(self.selectionChanged)

	def selectionChanged(self):
		self["entry"].text = self.parent.getCurrentEntry()
		self["value"].text = self.parent.getCurrentValue()
		if hasattr(self.parent,"getCurrentDescription"):
			self.parent["description"].text = self.parent.getCurrentDescription()
		if 'footnote' in self.parent:
			if self.parent.getCurrentEntry().endswith('*'):
				self.parent['footnote'].text = (_("* = Restart Required"))
			else:
				self.parent['footnote'].text = (_(" "))

class PiconPathsSetup(Screen,ConfigListScreen):
	def removeNotifier(self):
		if config.usage.setup_level.notifiers:
			config.usage.setup_level.notifiers.remove(self.levelChanged)

	def levelChanged(self, configElement):
		list = []
		self.refill(list)
		self["config"].setList(list)

	def refill(self, list):
		xmldata = setupdom()
		for x in xmldata.findall("setup"):
			if x.get("key") != self.setup:
				continue
			self.addItems(list, x)
			self.setup_title = six.ensure_str(x.get("title", ""))
			self.seperation = int(x.get('separation', '0'))

	def __init__(self, session):
		Screen.__init__(self, session)
		self.skinName = "Setup"
		self['footnote'] = Label()
		self["HelpWindow"] = Pixmap()
		self["HelpWindow"].hide()
		self["VKeyIcon"] = Boolean(False)

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Save"))
		self["description"] = Label(_(""))

		self.onChangedEntry = [ ]
		self.setup = "UserInterface"
		list = []
		ConfigListScreen.__init__(self, list, session = session, on_change = self.changedEntry)
		self.createSetup()

		self["setupActions"] = ActionMap(["SetupActions", "ColorActions", "MenuActions"],
		{
			"green": self.keySave,
			"red": self.keyCancel,
			"cancel": self.keyCancel,
			"ok": self.ok,
			"menu": self.closeRecursive,
		}, -2)
		self.onLayoutFinish.append(self.layoutFinished)

	def checkReadWriteDir(self, configele):
		print("checkReadWrite: ", configele.value)
		if configele.value in [x[0] for x in self.styles] or fileExists(configele.value, "w"):
			configele.last_value = configele.value
			return True
		else:
			dir = configele.value
			configele.value = configele.last_value
			self.session.open(
				MessageBox,
				_("The directory %s is not writable.\nMake sure you select a writable directory instead.")%dir,
				type = MessageBox.TYPE_ERROR
				)
			return False

	def createSetup(self):
		self.styles = hddchoises
		styles_keys = [x[0] for x in self.styles]
		tmp = config.misc.allowed_picon_paths.value
		default = config.misc.picon_path.value
		if default not in tmp and default not in styles_keys:
			tmp = tmp[:]
			tmp.append(default)
		print("Picon Path: ", default, tmp)
		self.picon_dirname = ConfigSelection(default = default, choices = self.styles+tmp)

		#self.picon_dirname.addNotifier(self.checkReadWriteDir, initial_call=False, immediate_feedback=False)

		list = []
		if config.usage.setup_level.index >= 0:
			self.picon_entry = getConfigListEntry(_("Picon location"), self.picon_dirname, _("Select folder where your picons are located."))
			list.append(self.picon_entry)
			self.piconHDD_entry = getConfigListEntry(_("Search picons in /media/hdd"), config.misc.picon_search_hdd, _("Enable or disable searching picons in HDD."))
			list.append(self.piconHDD_entry)

		self.refill(list)
		self["config"].setList(list)
		if config.usage.sort_settings.value:
			self["config"].list.sort()

	def layoutFinished(self):
		self.setTitle(_(self.setup_title))

	# for summary:
	def changedEntry(self):
		self.item = self["config"].getCurrent()
		if self["config"].getCurrent()[0] == _("Picon location"):
			self.checkReadWriteDir(self["config"].getCurrent()[1])
		for x in self.onChangedEntry:
			x()
			config.misc.picon_path.value = self.picon_dirname.value
			config.misc.picon_path.save()
		try:
			if isinstance(self["config"].getCurrent()[1], ConfigYesNo) or isinstance(self["config"].getCurrent()[1], ConfigSelection):
				self.createSetup()
		except:
			pass

	def getCurrentEntry(self):
		return self["config"].getCurrent() and self["config"].getCurrent()[0] or ""

	def getCurrentValue(self):
		return self["config"].getCurrent() and str(self["config"].getCurrent()[1].getText()) or ""

	def getCurrentDescription(self):
		return self["config"].getCurrent() and len(self["config"].getCurrent()) > 2 and self["config"].getCurrent()[2] or ""

	def ok(self):
		currentry = self["config"].getCurrent()
		if currentry == self.picon_entry:
			self.entrydirname = self.picon_dirname
			config.misc.picon_path.value = self.picon_dirname.value
			self.session.openWithCallback(
				self.dirnameSelected,
				PiconLocationBox
			)

	def dirnameSelected(self, res):
		if res is not None:
			self.entrydirname.value = res
			currentry = self["config"].getCurrent()
			if currentry == self.picon_entry:
				styles_keys = [x[0] for x in self.styles]
				tmp = config.misc.allowed_picon_paths.value
				default = self.picon_dirname.value
				if default not in tmp and default not in styles_keys:
					tmp = tmp[:]
					tmp.append(default)
				self.picon_dirname.setChoices(self.styles+tmp, default=default)
				self.entrydirname.value = res

	def saveAll(self):
		currentry = self["config"].getCurrent()
		config.misc.picon_path.value = self.picon_dirname.value
		config.misc.picon_path.save()
		config.misc.picon_search_hdd.save()
		from Components.Renderer import Picon
		Picon.setPiconPath()
		try:
			from Components.Renderer import Picon
			Picon.setPiconPath()
		except:
			pass
		for x in self["config"].list:
			x[1].save()
		configfile.save()

	# keySave and keyCancel are just provided in case you need them.
	# you have to call them by yourself.
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
			self.session.openWithCallback(self.cancelConfirm, MessageBox, _("Really close without saving settings?"), default = False)
		else:
			self.close()

	def createSummary(self):
		return SetupSummary

	def addItems(self, list, parentNode):
		for x in parentNode:
			if not x.tag:
				continue
			if x.tag == 'item':
				item_level = int(x.get("level", 0))
				item_rectunerlevel = int(x.get("rectunerlevel", 0))

				if self.levelChanged not in config.usage.setup_level.notifiers:
					config.usage.setup_level.notifiers.append(self.levelChanged)
					self.onClose.append(self.removeNotifier)

				if item_level > config.usage.setup_level.index:
					continue

				requires = x.get("requires")
				if requires and requires.startswith('config.'):
					item = eval(requires or "")
					if item.value and not item.value == "0":
						SystemInfo[requires] = True
					else:
						SystemInfo[requires] = False

				if requires and not SystemInfo.get(requires, False):
					continue

				item_text = _(six.ensure_str(x.get("text", "??")))
				item_description = _(six.ensure_str(x.get("description", " ")))

				item_text = item_text.replace("%s %s","%s %s" % (getMachineBrand(), getMachineName()))
				item_description = item_description.replace("%s %s","%s %s" % (getMachineBrand(), getMachineName()))
				try:
					b = eval(x.text or "")
				except:
					b = ""
				if b == "":
					continue
				#add to configlist
				item = b
				# the first b is the item itself, ignored by the configList.
				# the second one is converted to string.
				if not isinstance(item, ConfigNothing):
					list.append((item_text, item, item_description))

