from enigma import eDVBResourceManager, eDVBFrontendParametersSatellite, iDVBFrontend, eConsoleAppContainer

from Screens.ScanSetup import ScanSetup, buildTerTransponder
from Screens.ServiceScan import ServiceScan
from Screens.MessageBox import MessageBox
from Plugins.Plugin import PluginDescriptor

from Components.Sources.FrontendStatus import FrontendStatus
from Components.ActionMap import ActionMap
from Components.NimManager import nimmanager
from Components.config import config
from Components.TuneTest import Tuner
from Components.Sources.StaticText import StaticText
from Components.Label import Label
from Tools.Transponder import channel2frequency
from Tools.BoundFunction import boundFunction
from Tools.Directories import isPluginInstalled

if isPluginInstalled("AutoBouquetsMaker"):
	dvbreader_available = True
	from Plugins.SystemPlugins.AutoBouquetsMaker.scanner import dvbreader
	import time
	import datetime
	import _thread
else:
	dvbreader_available = False


class Satfinder(ScanSetup, ServiceScan):
	def __init__(self, session):
		self.initcomplete = False
		service = session and session.nav.getCurrentService()
		feinfo = service and service.frontendInfo()
		self.frontendData = feinfo and feinfo.getAll(True)
		del feinfo
		del service

		self.systemEntry = None
		self.systemEntryATSC = None
		self.satfinderTunerEntry = None
		self.satEntry = None
		self.frequencyEntry = None
		self.polarizationEntry = None
		self.symbolrateEntry = None
		self.inversionEntry = None
		self.rolloffEntry = None
		self.pilotEntry = None
		self.fecEntry = None
		self.transponder = None
		self.is_id_boolEntry = None
		self.t2mi_plp_id_boolEntry = None

		ScanSetup.__init__(self, session)
		self.setTitle(_("Signal Finder"))
		self["header"] = Label(_("Manual Scan"))
		self["key_blue"] = StaticText(_("Extras") if not isPluginInstalled("AutoBouquetsMaker") else "")
		self["Frontend"] = FrontendStatus(frontend_source=lambda: self.frontend, update_interval=100)

		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"save": self.keyGoScan,
			"ok": self.keyGoScan,
			"blue": self.extras,
			"cancel": self.keyCancel,
		}, -3)

		self.initcomplete = True
		self.session.postScanService = self.session.nav.getCurrentlyPlayingServiceOrGroup()
		self.onClose.append(self.__onClose)
		self.onShow.append(self.prepareFrontend)

	def openFrontend(self):
		res_mgr = eDVBResourceManager.getInstance()
		if res_mgr:
			fe_id = int(self.scan_nims.value)
			self.raw_channel = res_mgr.allocateRawChannel(fe_id)
			if self.raw_channel:
				self.frontend = self.raw_channel.getFrontend()
				if self.frontend:
					return True
		return False

	def restartUI(self, answer):
		if answer:
			from Screens.Standby import TryQuitMainloop
			self.session.open(TryQuitMainloop, 3)

	def extras(self):
		eConsoleAppContainer().execute("opkg update")

		def installAutoBouquetsMaker(answer=False):
			if answer:
				from time import sleep
				eConsoleAppContainer().execute("opkg install enigma2-plugin-systemplugins-autobouquetsmaker")
				sleep(2.5)
				if not isPluginInstalled("AutoBouquetsMaker"):
					sleep(1)
				if isPluginInstalled("AutoBouquetsMaker"):
					self.session.openWithCallback(self.restartUI, MessageBox, _("AutoBoquetsMaker was installed successfully.\nIt is necessary to restart enigma2 to apply the changes.\nDo you want to do it now?"), MessageBox.TYPE_YESNO, simple=True)

		if not isPluginInstalled("AutoBouquetsMaker"):
			self.session.openWithCallback(installAutoBouquetsMaker, MessageBox, _("To add extras you need to install AutoBouquetsMaker.\nIf you press \"Yes\" please wait.\nDo you want to install it now?"), type=MessageBox.TYPE_YESNO, simple=True)

	def prepareFrontend(self):
		self.frontend = None
		try:
			if not self.openFrontend():
				self.session.nav.stopService()
				if not self.openFrontend():
					if self.session.pipshown:
						from Screens.InfoBar import InfoBar
						InfoBar.instance and hasattr(InfoBar.instance, "showPiP") and InfoBar.instance.showPiP()
						if not self.openFrontend():
							self.frontend = None  # in normal case this should not happen
			self.tuner = Tuner(self.frontend)
			self.createSetup()
			self.retune()
		except:
			pass

	def __onClose(self):
		self.session.nav.playService(self.session.postScanService)

	def newConfig(self):
#		self.transponder = None
		cur = self["config"].getCurrent()
		print("cur ", cur)

		if cur == self.tunerEntry:
			self.feid = int(self.scan_nims.value)
			self.prepareFrontend()
			if self.frontend is None and self.session.nav.RecordTimer.isRecording():
				slot = nimmanager.nim_slots[self.feid]
				msg = _("%s not available.") % slot.getSlotName()
				msg += _("\nRecording in progress.")
				self.session.open(MessageBox, msg, MessageBox.TYPE_ERROR)
		elif cur == self.is_id_boolEntry:
			if self.is_id_boolEntry[1].value:
				self.scan_sat.is_id.value = 0 if self.is_id_memory < 0 else self.is_id_memory
				self.scan_sat.pls_mode.value = self.pls_mode_memory
				self.scan_sat.pls_code.value = self.pls_code_memory
			else:
				self.is_id_memory = self.scan_sat.is_id.value
				self.pls_mode_memory = self.scan_sat.pls_mode.value
				self.pls_code_memory = self.scan_sat.pls_code.value
				self.scan_sat.is_id.value = eDVBFrontendParametersSatellite.No_Stream_Id_Filter
				self.scan_sat.pls_mode.value = eDVBFrontendParametersSatellite.PLS_Gold
				self.scan_sat.pls_code.value = eDVBFrontendParametersSatellite.PLS_Default_Gold_Code
			self.createSetup()
			self.retune()
		elif cur == self.t2mi_plp_id_boolEntry:
			if self.t2mi_plp_id_boolEntry[1].value:
				self.scan_sat.t2mi_plp_id.value = 0 if self.t2mi_plp_id_memory < 0 else self.t2mi_plp_id_memory
				self.scan_sat.t2mi_pid.value = self.t2mi_pid_memory
			else:
				self.t2mi_plp_id_memory = self.scan_sat.t2mi_plp_id.value
				self.t2mi_pid_memory = self.scan_sat.t2mi_pid.value
				self.scan_sat.t2mi_plp_id.value = eDVBFrontendParametersSatellite.No_T2MI_PLP_Id
				self.scan_sat.t2mi_pid.value = eDVBFrontendParametersSatellite.T2MI_Default_Pid
			self.createSetup()
			self.retune()
		else:
			ScanSetup.newConfig(self)
		if cur[1].value == "single_transponder":
			self.retune()

	def createSetup(self):
		ScanSetup.createSetup(self)

#manipulate "config", remove "self.scan_networkScan", "self.scan_clearallservices" and "self.scan_onlyfree"
		tlist = self["config"].getList()
		for x in (self.scan_networkScan, self.scan_clearallservices, self.scan_onlyfree):
			for y in tlist:
				if x == y[1]:
					tlist.remove(y)
		self["config"].list = tlist
		self["config"].l.setList(tlist)

#manipulate choices, we need only "single_transponder","predefined_transponder"
		for scan_type in (self.scan_type, self.scan_typecable, self.scan_typeterrestrial, self.scan_typeatsc):
			slist = scan_type.choices.choices
			dlist = []
			for x in slist:
				if x[0] in ("single_transponder", "predefined_transponder"):
					dlist.append(x)
			scan_type.choices.choices = dlist

	def TunerTypeChanged(self):
		fe_id = int(self.scan_nims.value)
		multiType = config.Nims[fe_id].multiType
		system = multiType.getText()
		if (system in ('DVB-S', 'DVB-S2') and config.Nims[fe_id].dvbs.configMode.value == "nothing") or \
			(system in ('DVB-T', 'DVB-T2') and config.Nims[fe_id].dvbt.configMode.value == "nothing") or \
			(system in ('DVB-C') and config.Nims[fe_id].dvbc.configMode.value == "nothing") or \
			(system in ('ATSC') and config.Nims[fe_id].atsc.configMode.value == "nothing"):
			return
		slot = nimmanager.nim_slots[fe_id]
		print("dvb_api_version ", iDVBFrontend.dvb_api_version)
		self.frontend = None
		if not self.openFrontend():
			self.session.nav.stopService()
			if not self.openFrontend():
				if self.session.pipshown:
					from Screens.InfoBar import InfoBar
					InfoBar.instance and hasattr(InfoBar.instance, "showPiP") and InfoBar.instance.showPiP()
					if not self.openFrontend():
						self.frontend = None  # in normal case this should not happen
		self.tuner = Tuner(self.frontend)

		if slot.isMultiType():
			eDVBResourceManager.getInstance().setFrontendType(slot.frontend_id, "dummy", False)  # to force a clear of m_delsys_whitelist
			types = slot.getMultiTypeList()
			for FeType in types.values():
				if FeType in ("DVB-S", "DVB-S2", "DVB-S2X") and config.Nims[slot.slot].dvbs.configMode.value == "nothing":
					continue
				elif FeType in ("DVB-T", "DVB-T2") and config.Nims[slot.slot].dvbt.configMode.value == "nothing":
					continue
				elif FeType in ("DVB-C", "DVB-C2") and config.Nims[slot.slot].dvbc.configMode.value == "nothing":
					continue
				elif FeType in ("ATSC") and config.Nims[slot.slot].atsc.configMode.value == "nothing":
					continue
				eDVBResourceManager.getInstance().setFrontendType(slot.frontend_id, FeType, True)
		else:
			eDVBResourceManager.getInstance().setFrontendType(slot.frontend_id, slot.getType())


#			if not path.exists("/proc/stb/frontend/%d/mode" % fe_id) and iDVBFrontend.dvb_api_version >= 5:
		print("api >=5 and new style tuner driver")
		if self.frontend:
			if system == 'DVB-C':
				ret = self.frontend.changeType(iDVBFrontend.feCable)
			elif system in ('DVB-T', 'DVB-T2'):
				ret = self.frontend.changeType(iDVBFrontend.feTerrestrial)
			elif system in ('DVB-S', 'DVB-S2'):
				ret = self.frontend.changeType(iDVBFrontend.feSatellite)
			elif system == 'ATSC':
				ret = self.frontend.changeType(iDVBFrontend.feATSC)
			else:
				ret = False
			if not ret:
				print("%d: tunerTypeChange to '%s' failed" % (fe_id, system))
			else:
				print("new system ", system)
		else:
			print("%d: tunerTypeChange to '%s' failed (BUSY)" % (fe_id, multiType.getText()))
		self.retune()

	def createConfig(self):
		ScanSetup.createConfig(self)
		if self.scan_nims.value:  # OpenSPA {norhap] tuner sanity check configured.
			for x in (
				self.scan_sat.frequency,
				self.scan_satselection[int(self.scan_nims.value)],
				self.scan_sat.symbolrate,
				self.scan_sat.is_id,
				self.scan_sat.pls_mode,
				self.scan_sat.pls_code,
				self.scan_sat.t2mi_plp_id,
				self.scan_sat.t2mi_pid,
				self.scan_ter.channel,
				self.scan_ter.frequency,
				self.scan_ter.inversion,
				self.scan_ter.bandwidth, self.scan_ter.fechigh, self.scan_ter.feclow,
				self.scan_ter.modulation, self.scan_ter.transmission,
				self.scan_ter.guard, self.scan_ter.hierarchy,
				self.scan_ter.plp_id,
				self.scan_cab.frequency, self.scan_cab.inversion, self.scan_cab.symbolrate,
				self.scan_cab.modulation, self.scan_cab.fec,
				self.scan_ats.frequency, self.scan_ats.modulation, self.scan_ats.inversion,
				self.scan_ats.system,

				):
				if x is not None:
					x.clearNotifiers()
					x.addNotifier(self.TriggeredByConfigElement, initial_call=False)

	def TriggeredByConfigElement(self, configElement):
		self.retune()

	def retune(self):
		nim = nimmanager.nim_slots[int(self.scan_nims.value)]
		if nim.isCompatible("DVB-S") and nim.config.dvbs.configMode.value != "nothing":
			return self.retuneSat()
		if nim.isCompatible("DVB-T") and nim.config.dvbt.configMode.value != "nothing":
			return self.retuneTerr()
		if nim.isCompatible("DVB-C") and nim.config.dvbc.configMode.value != "nothing":
			return self.retuneCab()
		if nim.isCompatible("ATSC") and nim.config.atsc.configMode.value != "nothing":
			return self.retuneATSC()
		self.frontend = None
		self.raw_channel = None
		print("error: tuner not enabled/supported", nim.getType())

	def retuneCab(self):
		if self.initcomplete:
			if self.scan_typecable.value == "single_transponder":
				transponder = (
					self.scan_cab.frequency.value[0] * 1000 + self.scan_cab.frequency.value[1],
					self.scan_cab.symbolrate.value * 1000,
					self.scan_cab.modulation.value,
					self.scan_cab.fec.value,
					self.scan_cab.inversion.value
				)
				self.tuner.tuneCab(transponder)
				self.transponder = transponder
			elif self.scan_typecable.value == "predefined_transponder":
				if self.CableTransponders is not None:
					tps = nimmanager.getTranspondersCable(int(self.scan_nims.value))
					if len(tps) > self.CableTransponders.index:
						tp = tps[self.CableTransponders.index]
						# tp = 0 transponder type, 1 freq, 2 sym, 3 mod, 4 fec, 5 inv, 6 sys
						transponder = (tp[1], tp[2], tp[3], tp[4], tp[5])
						self.tuner.tuneCab(transponder)
						self.transponder = transponder

	def retuneTerr(self):
		if self.initcomplete:
			if self.scan_input_as.value == "channel":
				frequency = channel2frequency(self.scan_ter.channel.value, self.ter_tnumber)
				if frequency:
					frequency = int(frequency)
				else:  # FIXME channel2frequency return None because of channel not found
					print("[Satfinder] retuneTerr DVB-T channel '%s' out of scope" % str(self.scan_ter.channel.value))
					return
			else:
				frequency = self.scan_ter.frequency.floatint * 1000
			if self.scan_typeterrestrial.value == "single_transponder":
				transponder = [
					2,  # TERRESTRIAL
					frequency,
					self.scan_ter.bandwidth.value,
					self.scan_ter.modulation.value,
					self.scan_ter.fechigh.value,
					self.scan_ter.feclow.value,
					self.scan_ter.guard.value,
					self.scan_ter.transmission.value,
					self.scan_ter.hierarchy.value,
					self.scan_ter.inversion.value,
					self.scan_ter.system.value,
					self.scan_ter.plp_id.value]
				self.tuner.tuneTerr(transponder[1], transponder[9], transponder[2], transponder[4], transponder[5], transponder[3], transponder[7], transponder[6], transponder[8], transponder[10], transponder[11])
				self.transponder = transponder
			elif self.scan_typeterrestrial.value == "predefined_transponder":
				if self.TerrestrialTransponders is not None:
					region = nimmanager.getTerrestrialDescription(int(self.scan_nims.value))
					tps = nimmanager.getTranspondersTerrestrial(region)
					if len(tps) > self.TerrestrialTransponders.index:
						transponder = tps[self.TerrestrialTransponders.index]
						# frequency 1, inversion 9, bandwidth 2, fechigh 4, feclow 5, modulation 3, transmission 7, guard 6, hierarchy 8, system 10, plp_id 11
						self.tuner.tuneTerr(transponder[1], transponder[9], transponder[2], transponder[4], transponder[5], transponder[3], transponder[7], transponder[6], transponder[8], transponder[10], transponder[11])
						self.transponder = transponder

	def retuneSat(self):
		fe_id = int(self.scan_nims.value)
		nimsats = self.satList[fe_id]
		selsatidx = self.scan_satselection[fe_id].index
		if len(nimsats):
			orbpos = nimsats[selsatidx][0]
			if self.initcomplete:
				if self.scan_type.value == "single_transponder":
					if self.scan_sat.system.value == eDVBFrontendParametersSatellite.System_DVB_S2:
						fec = self.scan_sat.fec_s2.value
					else:
						fec = self.scan_sat.fec.value

					transponder = (
						self.scan_sat.frequency.value,
						self.scan_sat.symbolrate.value,
						self.scan_sat.polarization.value,
						fec,
						self.scan_sat.inversion.value,
						orbpos,
						self.scan_sat.system.value,
						self.scan_sat.modulation.value,
						self.scan_sat.rolloff.value,
						self.scan_sat.pilot.value,
						self.scan_sat.is_id.value,
						self.scan_sat.pls_mode.value,
						self.scan_sat.pls_code.value,
						self.scan_sat.t2mi_plp_id.value,
						self.scan_sat.t2mi_pid.value)
					self.tuner.tune(transponder)
					self.transponder = transponder
				elif self.scan_type.value == "predefined_transponder":
					tps = nimmanager.getTransponders(orbpos)
					if len(tps) > self.preDefTransponders.index:
						tp = tps[self.preDefTransponders.index]
						transponder = (tp[1] // 1000, tp[2] // 1000,
							tp[3], tp[4], 2, orbpos, tp[5], tp[6], tp[8], tp[9], tp[10], tp[11], tp[12], tp[13], tp[14])
						self.tuner.tune(transponder)
						self.transponder = transponder

	def retuneATSC(self):
		if self.initcomplete:
			if self.scan_typeatsc.value == "single_transponder":
				transponder = (
					self.scan_ats.frequency.floatint * 1000,
					self.scan_ats.modulation.value,
					self.scan_ats.inversion.value,
					self.scan_ats.system.value,
				)
				if self.initcomplete:
					self.tuner.tuneATSC(transponder)
				self.transponder = transponder
			elif self.scan_typeatsc.value == "predefined_transponder":
				tps = nimmanager.getTranspondersATSC(int(self.scan_nims.value))
				if tps and len(tps) > self.ATSCTransponders.index:
					tp = tps[self.ATSCTransponders.index]
					transponder = (tp[1], tp[2], tp[3], tp[4])
					if self.initcomplete:
						self.tuner.tuneATSC(transponder)
					self.transponder = transponder

	def keyGoScan(self):
		if self.transponder is None:
			print("error: no transponder data")
			return
		fe_id = int(self.scan_nims.value)
		nim = nimmanager.nim_slots[fe_id]
		self.frontend = None
		if self.raw_channel:
			self.raw_channel = None
		tlist = []
		if nim.isCompatible("DVB-S"):
			nimsats = self.satList[fe_id]
			selsatidx = self.scan_satselection[fe_id].index
			if len(nimsats):
				orbpos = nimsats[selsatidx][0]
				self.addSatTransponder(tlist,
					self.transponder[0],  # frequency
					self.transponder[1],  # sr
					self.transponder[2],  # pol
					self.transponder[3],  # fec
					self.transponder[4],  # inversion
					orbpos,
					self.transponder[6],  # system
					self.transponder[7],  # modulation
					self.transponder[8],  # rolloff
					self.transponder[9],  # pilot
					self.transponder[10],  # input stream id
					self.transponder[11],  # pls mode
					self.transponder[12],  # pls code
					self.transponder[13],  # t2mi_plp_id
					self.transponder[14]  # t2mi_pid
				)
		elif nim.isCompatible("DVB-T"):
			parm = buildTerTransponder(
				self.transponder[1],  # frequency
				self.transponder[9],  # inversion
				self.transponder[2],  # bandwidth
				self.transponder[4],  # fechigh
				self.transponder[5],  # feclow
				self.transponder[3],  # modulation
				self.transponder[7],  # transmission
				self.transponder[6],  # guard
				self.transponder[8],  # hierarchy
				self.transponder[10],  # system
				self.transponder[11]  # plp_id
			)
			tlist.append(parm)
		elif nim.isCompatible("DVB-C"):
			self.addCabTransponder(tlist,
				self.transponder[0],  # frequency
				self.transponder[1],  # sr
				self.transponder[2],  # modulation
				self.transponder[3],  # fec_inner
				self.transponder[4]  # inversion
			)
		elif nim.isCompatible("ATSC"):
			self.addATSCTransponder(tlist,
				self.transponder[0],  # frequency
				self.transponder[1],  # modulation
				self.transponder[2],  # inversion
				self.transponder[3]  # system
			)
		else:
			print("error: tuner not enabled/supported", nim.getType())
		self.startScan(tlist, fe_id)

	def startScan(self, tlist, feid):
		flags = 0
		networkid = 0
		self.session.openWithCallback(self.startScanCallback, ServiceScan, [{"transponders": tlist, "feid": feid, "flags": flags, "networkid": networkid}])

	def startScanCallback(self, answer=None):
		if answer:
			self.doCloseRecursive()

	def keyCancel(self):
		if self.session.postScanService and self.frontend:
			self.frontend = None
			self.raw_channel = None
		self.close(False)

	def doCloseRecursive(self):
		if self.session.postScanService and self.frontend:
			self.frontend = None
			self.raw_channel = None
		self.close(True)


class SatfinderExtra(Satfinder):
	# This class requires AutoBouquetsMaker to be installed.
	def __init__(self, session):
		Satfinder.__init__(self, session)
		self.skinName = ["Satfinder"]

		self["key_yellow"] = StaticText("")

		self["actions2"] = ActionMap(["ColorActions"],
		{
			"yellow": self.keyReadServices,
		}, -3)
		self["actions2"].setEnabled(False)

		# DVB stream info
		self.serviceList = []
		self["tsid"] = StaticText("")
		self["onid"] = StaticText("")
		self["pos"] = StaticText("")
		self["tsidtext"] = StaticText("")
		self["onidtext"] = StaticText("")
		self["postext"] = StaticText("")

	def retune(self, configElement=None):
		Satfinder.retune(self)
		self.dvb_read_stream()

	def openFrontend(self):
		if Satfinder.openFrontend(self):
			self.demux = self.raw_channel.reserveDemux()  # used for keyReadServices()
			return True
		return False

	def prepareFrontend(self):
		self.demux = -1  # used for keyReadServices()
		Satfinder.prepareFrontend(self)

	def dvb_read_stream(self):
		print("[satfinder][dvb_read_stream] starting")
		try:
			_thread.start_new_thread(self.getCurrentTsidOnid, (True,))
		except Exception:
			pass

	def getCurrentTsidOnid(self, from_retune=False):
		self.currentProcess = currentProcess = datetime.datetime.now()
		self["tsid"].setText("")
		self["onid"].setText("")
		self["postext"].setText(_("DVB type:"))
		if nimmanager.hasNimType("DVB-S"):
			self["pos"].setText("DVB-S")
		elif nimmanager.hasNimType("DVB-T"):
			self["pos"].setText("DVB-T")
		else:
			self["pos"].setText("ATSC")
		self["key_yellow"].setText("")
		self["actions2"].setEnabled(False)
		self.serviceList = []

		if not dvbreader_available or self.frontend is None or self.demux < 0:
			return

		if from_retune:  # give the tuner a chance to retune or we will be reading the old stream
			time.sleep(1.0)

		if not self.waitTunerLock(currentProcess):  # dont even try to read the transport stream if tuner is not locked
			return

		_thread.start_new_thread(self.monitorTunerLock, (currentProcess,))  # if tuner loses lock we start again from scratch

		adapter = 0

		sdt_pid = 0x11
		sdt_current_table_id = 0x42
		mask = 0xff
		tsidOnidTimeout = 60  # maximum time allowed to read the service descriptor table (seconds)
		self.tsid = None
		self.onid = None

		sdt_current_version_number = -1
		sdt_current_sections_read = []
		sdt_current_sections_count = 0
		sdt_current_content = []
		sdt_current_completed = False

		timeout = datetime.datetime.now()
		timeout += datetime.timedelta(0, tsidOnidTimeout)
		self.feid = int(self.scan_nims.value)
		if hasattr(self, "demux"):
			demuxer_device = "/dev/dvb/adapter%d/demux%d" % (adapter, self.demux)
			if demuxer_device:
				fd = dvbreader.open(demuxer_device, sdt_pid, sdt_current_table_id, mask, self.feid)
				if fd:
					if fd < 0:
						print("[Satfinder][getCurrentTsidOnid] Cannot open the demuxer")
						return None

				while True:
					if datetime.datetime.now() > timeout:
						print("[Satfinder][getCurrentTsidOnid] Timed out")
						break

					if hasattr(self, "currentProcess") and self.currentProcess != currentProcess:
						dvbreader.close(fd)
						return
					if fd:
						section = dvbreader.read_sdt(fd, sdt_current_table_id, 0x00)
					if section is None:
						time.sleep(0.1)  # no data.. so we wait a bit
						continue

					if section["header"]["table_id"] == sdt_current_table_id and not sdt_current_completed:
						if section["header"]["version_number"] != sdt_current_version_number:
							sdt_current_version_number = section["header"]["version_number"]
							sdt_current_sections_read = []
							sdt_current_sections_count = section["header"]["last_section_number"] + 1
							sdt_current_content = []

						if section["header"]["section_number"] not in sdt_current_sections_read:
							sdt_current_sections_read.append(section["header"]["section_number"])
							sdt_current_content += section["content"]
							if hasattr(self, "tsid") and self.tsid is None or hasattr(self, "onid") and self.onid is None:  # write first find straight to the screen
								self.tsid = section["header"]["transport_stream_id"]
								self.onid = section["header"]["original_network_id"]
								self["tsidtext"].setText("TSID:")
								self["onidtext"].setText("ONID:")
								self["tsid"].setText("%d" % (section["header"]["transport_stream_id"]))
								self["onid"].setText("%d" % (section["header"]["original_network_id"]))
								self["introduction"].text = _("Press OK to start the scan")
								print("[Satfinder][getCurrentTsidOnid] tsid %d, onid %d" % (section["header"]["transport_stream_id"], section["header"]["original_network_id"]))

							if len(sdt_current_sections_read) == sdt_current_sections_count:
								sdt_current_completed = True

					if sdt_current_completed:
						break

				dvbreader.close(fd)

		if not sdt_current_content:
			print("[Satfinder][getCurrentTsidOnid] no services found on transponder")
			return

		for i in range(len(sdt_current_content)):
			if not sdt_current_content[i]["service_name"]:  # if service name is empty use SID
				sdt_current_content[i]["service_name"] = "0x%x" % sdt_current_content[i]["service_id"]

		self.serviceList = sorted(sdt_current_content, key=lambda listItem: listItem["service_name"])
		if self.serviceList:
			self["key_yellow"].setText(_("Services list"))
			self["actions2"].setEnabled(True)

		self.getOrbPosFromNit(currentProcess)

	def getOrbPosFromNit(self, currentProcess):
		if not nimmanager.hasNimType("DVB-S") or not dvbreader_available or self.frontend is None or self.demux < 0:
			return

		adapter = 0
		if hasattr(self, "demux"):
			demuxer_device = "/dev/dvb/adapter%d/demux%d" % (adapter, self.demux)

		nit_current_pid = 0x10
		nit_current_table_id = 0x40
		nit_other_table_id = 0x00  # don't read other table
		if nit_other_table_id == 0x00:
			mask = 0xff
		else:
			mask = nit_current_table_id ^ nit_other_table_id ^ 0xff
		nit_current_timeout = 60  # maximum time allowed to read the network information table (seconds)

		nit_current_version_number = -1
		nit_current_sections_read = []
		nit_current_sections_count = 0
		nit_current_content = []
		nit_current_completed = False

		fd = dvbreader.open(demuxer_device, nit_current_pid, nit_current_table_id, mask, self.feid)
		if fd < 0:
			print("[Satfinder][getOrbPosFromNit] Cannot open the demuxer")
			return

		timeout = datetime.datetime.now()
		timeout += datetime.timedelta(0, nit_current_timeout)

		while True:
			if datetime.datetime.now() > timeout:
				print("[Satfinder][getOrbPosFromNit] Timed out reading NIT")
				break

			if hasattr(self, "currentProcess"):
				if self.currentProcess != currentProcess:
					dvbreader.close(fd)
					return

			section = dvbreader.read_nit(fd, nit_current_table_id, nit_other_table_id)
			if section is None:
				time.sleep(0.1)  # no data.. so we wait a bit
				continue

			if section["header"]["table_id"] == nit_current_table_id and not nit_current_completed:
				if section["header"]["version_number"] != nit_current_version_number:
					nit_current_version_number = section["header"]["version_number"]
					nit_current_sections_read = []
					nit_current_sections_count = section["header"]["last_section_number"] + 1
					nit_current_content = []

				if section["header"]["section_number"] not in nit_current_sections_read:
					nit_current_sections_read.append(section["header"]["section_number"])
					nit_current_content += section["content"]

					if len(nit_current_sections_read) == nit_current_sections_count:
						nit_current_completed = True

			if nit_current_completed:
				break

		dvbreader.close(fd)

		if not nit_current_content:
			print("[Satfinder][getOrbPosFromNit] current transponder not found")
			return
		if hasattr(self, "tsid") or hasattr(self, "onid"):
			transponders = [t for t in nit_current_content if "descriptor_tag" in t and t["descriptor_tag"] == 0x43 and t["original_network_id"] == self.onid and t["transport_stream_id"] == self.tsid]
			transponders2 = [t for t in nit_current_content if "descriptor_tag" in t and t["descriptor_tag"] == 0x43 and t["transport_stream_id"] == self.tsid]
			if transponders and "orbital_position" in transponders[0]:
				orb_pos = self.getOrbitalPosition(transponders[0]["orbital_position"], transponders[0]["west_east_flag"])
				self["postext"].setText(_("Orbital position") + ":")
				self["pos"].setText(_("%s") % orb_pos)
				print("[satfinder][getOrbPosFromNit] orb_pos", orb_pos)
			elif transponders2 and "orbital_position" in transponders2[0]:
				orb_pos = self.getOrbitalPosition(transponders2[0]["orbital_position"], transponders2[0]["west_east_flag"])
				self["postext"].setText(_("Orbital position") + ":")
				self["pos"].setText(_("%s?") % orb_pos)
				print("[satfinder][getOrbPosFromNit] orb_pos tentative, tsid match, onid mismatch between NIT and SDT", orb_pos)
			else:
				print("[satfinder][getOrbPosFromNit] no orbital position found")

	def getOrbitalPosition(self, bcd, w_e_flag=1):
		# 4 bit BCD (binary coded decimal)
		# w_e_flag, 0 == west, 1 == east
		op = 0
		bits = 4
		for i in range(bits):
			op += ((bcd >> 4 * i) & 0x0F) * 10**i
		if op > 1800:
			op = (3600 - op) * -1
		if w_e_flag == 0:
			op *= -1
		return "%0.1f%s" % (abs(op) // 10., "W" if op < 0 else "E")

	def waitTunerLock(self, currentProcess):
		lock_timeout = 120

		timeout = datetime.datetime.now()
		timeout += datetime.timedelta(0, lock_timeout)

		while True:
			if datetime.datetime.now() > timeout:
				print("[Satfinder][waitTunerLock] tuner lock timeout reached, seconds:", lock_timeout)
				return False

			if hasattr(self, "currentProcess"):
				if self.currentProcess != currentProcess:
					return False

			if hasattr(self, "frontend"):
				frontendStatus = {}
				if self.frontend:
					self.frontend.getFrontendStatus(frontendStatus)
					if frontendStatus["tuner_state"] == "FAILED":
						print("[Satfinder][waitTunerLock] TUNING FAILED FATAL")  # enigma2 cpp code has given up trying
						return False
					if frontendStatus["tuner_state"] != "LOCKED":
						self["introduction"].text = _("The data provided will not find services.")
						time.sleep(0.25)
						continue

			return True

	def monitorTunerLock(self, currentProcess):
		while True:
			if hasattr(self, "currentProcess"):
				return
			frontendStatus = {}
			if frontendStatus:
				print("[monitorTunerLock] starting again from scratch")
				self.getCurrentTsidOnid(False)  # if tuner lock fails start again from beginning
				return
			time.sleep(1.0)

	def keyReadServices(self):
		from Screens.TextBox import TextBox
		if not self.serviceList:
			return
		tv = [1, 17, 22, 25]
		radio = [2, 10]
		red = r"\c00ff8888"  # Encrypted
		green = r"\c0088ff88"  # FTA
		yellow = r"\c00ffff00"  # UHD
		blue = r"\c007799ff"  # Radio
		mix = r"\c0000fafa"  # Others
		default = r"\c00ffffff"  # colour default white
		dash = f"{default}- "
		services = []
		legend = f"{default} {_('Services')}:               {red}{_('Encrypted')}  {green}{_('FTA')}  {yellow}{_('UHD')}  {blue}{_('Radio')}  {mix}{_('Others')}\n"
		for service in self.serviceList:
			fta = "free_ca" in service and service["free_ca"] == 0
			if service["service_type"] in radio:
				colour = blue
			elif service["service_type"] not in tv:
				colour = yellow if "UHD" in service["service_name"] or "4K" in service["service_name"].upper() else mix
			elif fta:
				colour = green
			else:
				colour = red
			services.append(f"{dash}{colour}{service['service_name']}")  # if version_info.major >= 3 else services.append("%s%s%s" % (dash, colour, service["service_name"].decode("ISO-8859-1").encode("UTF-8")))

		self.session.open(TextBox, "\n".join(services), legend)


def SatfinderCallback(close, answer):
	if close and answer:
		close(True)


def SatfinderMain(session, close=None, **kwargs):
	nims = nimmanager.nim_slots
	nimList = []
	for n in nims:
		if n.isMultiType():
			if not (n.isCompatible("DVB-S") or n.isCompatible("DVB-T") or n.isCompatible("DVB-C") or n.isCompatible("ATSC")):
				continue
		else:
			if not (n.isCompatible("DVB-S") or n.isCompatible("DVB-T") or n.isCompatible("DVB-C") or n.isCompatible("ATSC")):
				continue
			if n.isCompatible("DVB-S") and n.config.dvbs.configMode.value in ("loopthrough", "satposdepends", "nothing"):
				continue
			if n.isCompatible("DVB-S") and n.config.dvbs.configMode.value == "advanced" and len(nimmanager.getSatListForNim(n.slot)) < 1:
				continue
		nimList.append(n)

	if len(nimList) == 0:
		session.open(MessageBox, _("No satellite, terrestrial or cable tuner is configured. Please check your tuner setup."), MessageBox.TYPE_ERROR)
	else:
		if dvbreader_available or isPluginInstalled("AutoBouquetsMaker"):
			session.openWithCallback(boundFunction(SatfinderCallback, close), SatfinderExtra)
		else:
			session.openWithCallback(boundFunction(SatfinderCallback, close), Satfinder)



def SatfinderStart(menuid, **kwargs):
	if menuid == "scan":
		return [(_("Manual scan & signals"), SatfinderMain, "satfinder", 5)]
	else:
		return []


def Plugins(**kwargs):
	if nimmanager.hasNimType("DVB-S") or nimmanager.hasNimType("DVB-T") or nimmanager.hasNimType("DVB-C") or nimmanager.hasNimType("ATSC"):
		return PluginDescriptor(name=_("Signal Finder"), description=_("Helps setting up your signal"), where=PluginDescriptor.WHERE_MENU, needsRestart=False, fnc=SatfinderStart)
	else:
		return []
