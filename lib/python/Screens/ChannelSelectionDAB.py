from enigma import eServiceReference

from Components.ActionMap import ActionMap
from Components.config import config
from Screens.ChannelSelection import ChannelSelection, ChannelSelectionBase, MODE_RADIO, SelectionEventInfo
from Screens.newChannelSelection import newChannelSelection
from skin import findSkinScreen


class ChannelSelectionDAB(newChannelSelection):
	def __init__(self, session):
		self.dabListActive = False
		self.dabSavedActionStates = {}
		super().__init__(session)
		self["dabListActions"] = ActionMap(["OkCancelActions", "TvRadioActions"], {
			"cancel": self.cancel,
			"ok": self.channelSelected,
			"keyRadio": self.setModeRadio,
			"keyTV": self.setModeTv,
		})
		self["dabListActions"].setEnabled(False)
		self["spaNeutrinoPageActions"] = ActionMap(["DirectionActions"], {
			"left": self.key_pageUp,
			"right": self.key_pageDown,
		}, prio=-3)
		self["spaNeutrinoPageActions"].setEnabled("keymap.ntr" in config.usage.keymap.value)

	def updateRadioListSkin(self):
		if self is not ChannelSelection.instance:
			return
		reference = self.session.nav.getCurrentlyPlayingServiceReference()
		isDAB = (
			self.mode == MODE_RADIO
			and config.usage.e1like_radio_mode.value
			and reference is not None
			and reference.type == eServiceReference.idServiceDAB
			and findSkinScreen("ChannelSelectionRadioDABList")
		)
		self["spaNeutrinoPageActions"].setEnabled(not isDAB and "keymap.ntr" in config.usage.keymap.value)
		if bool(isDAB) != self.dabListActive:
			self.dabListActive = bool(isDAB)
			if self.dabListActive:
				for name in ("actions", "ChannelSelectBaseActions", *(f"hactions{x}" for x in range(1, 9))):
					actionMap = self.get(name)
					if actionMap is not None:
						self.dabSavedActionStates[name] = actionMap.getEnabled()
						actionMap.setEnabled(False)
				self.cbTimer.stop()
				self.timerEpg.stop()
				self.seg_plano_exit = True
				self.activo = "list"
				self["dabListActions"].setEnabled(True)
			else:
				self["dabListActions"].setEnabled(False)
				for name, enabled in self.dabSavedActionStates.items():
					self[name].setEnabled(enabled)
				self.dabSavedActionStates.clear()
		super().updateRadioListSkin()

	def setModeTv(self):
		super().setModeTv()
		if self.dabListActive and not self.execing:
			self.updateRadioListSkin()

	def alcrear(self):
		if not self.dabListActive:
			callbacks = self.servicelist.onSelectionChanged
			if self.actualizaepgtmp in callbacks:
				callbacks.remove(self.actualizaepgtmp)
			super().alcrear()

	def cbEV(self):
		if not self.dabListActive:
			super().cbEV()

	def actualizaepgtmp(self):
		if not self.dabListActive:
			super().actualizaepgtmp()

	def updateEventInfo(self):
		if self.dabListActive:
			SelectionEventInfo.updateEventInfo(self)
		else:
			super().updateEventInfo()

	def nextBouquet(self):
		if self.dabListActive:
			ChannelSelectionBase.nextBouquet(self)
		else:
			super().nextBouquet()

	def prevBouquet(self):
		if self.dabListActive:
			ChannelSelectionBase.prevBouquet(self)
		else:
			super().prevBouquet()

	def nextMarker(self):
		if self.dabListActive:
			ChannelSelectionBase.nextMarker(self)
		else:
			super().nextMarker()

	def prevMarker(self):
		if self.dabListActive:
			ChannelSelectionBase.prevMarker(self)
		else:
			super().prevMarker()

	def keyNumberGlobal(self, number=""):
		if self.dabListActive:
			ChannelSelectionBase.keyNumberGlobal(self, number)
		else:
			super().keyNumberGlobal(number)

	def keyAsciiCode(self, number=""):
		if self.dabListActive:
			ChannelSelectionBase.keyAsciiCode(self)
		else:
			super().keyAsciiCode(number)
