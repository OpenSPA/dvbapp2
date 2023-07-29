from os.path import exists
from os import W_OK, access, system
from time import sleep
from enigma import eAVControl, eDVBVolumecontrol, getDesktop, iServiceInformation
from Components.config import ConfigBoolean, ConfigEnableDisable, ConfigInteger, ConfigNothing, ConfigOnOff, ConfigSelection, ConfigSelectionNumber, ConfigSlider, ConfigSubDict, ConfigSubsection, ConfigYesNo, NoSave, config
from Components.About import about
from Components.SystemInfo import BoxInfo
from Tools.CList import CList
from Tools.Directories import fileReadLine, fileWriteLine

MODULE_NAME = __name__.split(".")[-1]
BRAND = BoxInfo.getItem("brand")
MACHINEBUILD = BoxInfo.getItem("machinebuild")

config.av = ConfigSubsection()
config.av.edid_override = ConfigYesNo(default=False)


class AVSwitchBase:
	axis = {
		"480i": "0 0 719 479",
		"480p": "0 0 719 479",
		"576i": "0 0 719 575",
		"576p": "0 0 719 575",
		"720p": "0 0 1279 719",
		"1080i": "0 0 1919 1079",
		"1080p": "0 0 1919 1079",
		"2160p30": "0 0 3839 2159",
		"2160p": "0 0 3839 2159",
		"smpte": "0 0 4095 2159"
	}

	rates = {}  # High-level, use selectable modes.
	rates["PAL"] = {
		"50Hz": {50: "pal"},
		"60Hz": {60: "pal60"},
		"multi": {50: "pal", 60: "pal60"}
	}
	rates["NTSC"] = {
		"60Hz": {60: "ntsc"}
	}
	rates["Multi"] = {
		"multi": {50: "pal", 60: "ntsc"}
	}
	if BoxInfo.getItem("AmlogicFamily"):
		rates["480i"] = {
			"60Hz": {60: "480i60hz"}
		}
		rates["576i"] = {
			"50Hz": {50: "576i50hz"}
		}
		rates["480p"] = {
			"60Hz": {60: "480p60hz"}
		}
		rates["576p"] = {
			"50Hz": {50: "576p50hz"}
		}
		rates["720p"] = {
			"50Hz": {50: "720p50hz"},
			"60Hz": {60: "720p60hz"},
			"auto": {60: "720p60hz"}
		}
		rates["1080i"] = {
			"50Hz": {50: "1080i50hz"},
			"60Hz": {60: "1080i60hz"},
			"auto": {60: "1080i60hz"}
		}
		rates["1080p"] = {
			"50Hz": {50: "1080p50hz"},
			"60Hz": {60: "1080p60hz"},
			"30Hz": {30: "1080p30hz"},
			"25Hz": {25: "1080p25hz"},
			"24Hz": {24: "1080p24hz"},
			"auto": {60: "1080p60hz"}
		}
		rates["2160p"] = {
			"50Hz": {50: "2160p50hz"},
			"60Hz": {60: "2160p60hz"},
			"30Hz": {30: "2160p30hz"},
			"25Hz": {25: "2160p25hz"},
			"24Hz": {24: "2160p24hz"},
			"auto": {60: "2160p60hz"}
		}
		rates["2160p30"] = {
			"25Hz": {50: "2160p25hz"},
			"30Hz": {60: "2160p30hz"},
			"auto": {60: "2160p30hz"}
		}
	else:
		rates["480i"] = {"60Hz": {60: "480i"}}
		rates["576i"] = {"50Hz": {50: "576i"}}
		rates["480p"] = {"60Hz": {60: "480p"}}
		rates["576p"] = {"50Hz": {50: "576p"}}
		rates["720p"] = {
			"50Hz": {50: "720p50"},
			"60Hz": {60: "720p"},
			"multi": {50: "720p50", 60: "720p"},
			"auto": {50: "720p50", 60: "720p", 24: "720p24"}
		}
		rates["1080i"] = {
			"50Hz": {50: "1080i50"},
			"60Hz": {60: "1080i"},
			"multi": {50: "1080i50", 60: "1080i"},
			"auto": {50: "1080i50", 60: "1080i", 24: "1080i24"}
		}
		rates["1080p"] = {
			"50Hz": {50: "1080p50"},
			"60Hz": {60: "1080p"},
			"multi": {50: "1080p50", 60: "1080p"},
			"auto": {50: "1080p50", 60: "1080p", 24: "1080p24"}
		}
		rates["2160p"] = {
			"50Hz": {50: "2160p50"},
			"60Hz": {60: "2160p"},
			"multi": {50: "2160p50", 60: "2160p"},
			"auto": {50: "2160p50", 60: "2160p", 24: "2160p24"}
		}
		rates["2160p30"] = {
			"25Hz": {50: "2160p25"},
			"30Hz": {60: "2160p30"},
			"multi": {50: "2160p25", 60: "2160p30"},
			"auto": {50: "2160p25", 60: "2160p30", 24: "2160p24"}
		}

	rates["smpte"] = {
		"50Hz": {50: "smpte50hz"},
		"60Hz": {60: "smpte60hz"},
		"30Hz": {30: "smpte30hz"},
		"25Hz": {25: "smpte25hz"},
		"24Hz": {24: "smpte24hz"},
		"auto": {60: "smpte60hz"}
	}

	rates["PC"] = {
		"1024x768": {60: "1024x768"},
		"800x600": {60: "800x600"},  # also not possible
		"720x480": {60: "720x480"},
		"720x576": {60: "720x576"},
		"1280x720": {60: "1280x720"},
		"1280x720 multi": {50: "1280x720_50", 60: "1280x720"},
		"1920x1080": {60: "1920x1080"},
		"1920x1080 multi": {50: "1920x1080", 60: "1920x1080_50"},
		"1280x1024": {60: "1280x1024"},
		"1366x768": {60: "1366x768"},
		"1366x768 multi": {50: "1366x768", 60: "1366x768_50"},
		"1280x768": {60: "1280x768"},
		"640x480": {60: "640x480"}
	}
	modes = {}  # A list of (high-level) modes for a certain port.
	modes["Scart"] = [
		"PAL",
		"NTSC",
		"Multi"
	]
	# modes["DVI-PC"] = [  # This mode does not exist.
	# 	"PC"
	# ]

	if BoxInfo.getItem("AmlogicFamily"):
		modes["HDMI"] = ["720p", "1080p", "smpte", "2160p30", "2160p", "1080i", "576p", "576i", "480p", "480i"]
	elif (about.getChipSetString() in ("7366", "7376", "5272s", "7444", "7445", "7445s")):
		modes["HDMI"] = ["720p", "1080p", "2160p", "1080i", "576p", "576i", "480p", "480i"]
	elif (about.getChipSetString() in ("7252", "7251", "7251S", "7252S", "7251s", "7252s", "72604", "7278", "7444s", "3798mv200", "3798mv200h", "3798cv200", "hi3798mv200", "hi3798mv200h", "hi3798cv200", "hi3798mv300", "3798mv300")):
		modes["HDMI"] = ["720p", "1080p", "2160p", "2160p30", "1080i", "576p", "576i", "480p", "480i"]
	elif (about.getChipSetString() in ("7241", "7358", "7362", "73625", "7346", "7356", "73565", "7424", "7425", "7435", "7552", "7581", "7584", "75845", "7585", "pnx8493", "7162", "7111", "3716mv410", "hi3716mv410", "hi3716mv430", "3716mv430")):
		modes["HDMI"] = ["720p", "1080p", "1080i", "576p", "576i", "480p", "480i"]
	else:
		modes["HDMI"] = ["720p", "1080i", "576p", "576i", "480p", "480i"]

	modes["YPbPr"] = modes["HDMI"]
	if BoxInfo.getItem("scartyuv", False):
		modes["Scart-YPbPr"] = modes["HDMI"]
	# if "DVI-PC" in modes and not getModeList("DVI-PC"):
	# 	print "[AVSwitch] Remove DVI-PC because that mode does not exist."
	# 	del modes["DVI-PC"]
	if "YPbPr" in modes and not BoxInfo.getItem("yuv", False):
		del modes["YPbPr"]
	if "Scart" in modes and not BoxInfo.getItem("scart", False) and not BoxInfo.getItem("rca", False) and not BoxInfo.getItem("avjack", False):
		del modes["Scart"]

	if MACHINEBUILD == "mutant2400":
		mode = fileReadLine("/proc/stb/info/board_revision", default="", source=MODULE_NAME)
		if mode >= "2":
			del modes["YPbPr"]

	widescreenModes = tuple([x for x in modes["HDMI"] if x not in ("576p", "576i", "480p", "480i")])

	ASPECT_SWITCH_MSG = (_("16/9 reset to normal"),
			"1.85:1 %s" % _("Letterbox"),
			"2.00:1 %s" % _("Letterbox"),
			"2.21:1 %s" % _("Letterbox"),
			"2.35:1 %s" % _("Letterbox"))

	def __init__(self):
		self.last_modes_preferred = []
		self.on_hotplug = CList()
		self.current_mode = None
		self.current_port = None
		self.readAvailableModes()
		self.is24hzAvailable()
		self.readPreferredModes()
		self.createConfig()

	def readAvailableModes(self):
		modes = eAVControl.getInstance().getAvailableModes()
		print("[AVSwitch] getAvailableModes:'%s'" % modes)
		return modes.split()

	def is24hzAvailable(self):
		BoxInfo.setItem("have24hz", eAVControl.getInstance().has24hz())

	def readPreferredModes(self, saveMode=False, readOnly=False):
		modes = ""
		if config.av.edid_override.value is False:
			modes = eAVControl.getInstance().getPreferredModes(1)
			if saveMode:
				modes = modes.split()
				return modes if len(modes) > 1 else []

			print("[AVSwitch] getPreferredModes:'%s'" % modes)
			self.modes_preferred = modes.split()

		if len(modes) < 2:
			self.modes_preferred = self.readAvailableModes()
			print("[AVSwitch] used default modes:%s" % self.modes_preferred)

		if len(self.modes_preferred) <= 2:
			print("[AVSwitch] preferend modes not ok, possible driver failer, len=%s" % len(self.modes_preferred))
			self.modes_preferred = self.readAvailableModes()

		if readOnly:
			return self.modes_preferred

		if self.modes_preferred != self.last_modes_preferred:
			self.last_modes_preferred = self.modes_preferred
			self.on_hotplug("HDMI")  # must be HDMI

	def getWindowsAxis(self):
		port = config.av.videoport.value
		mode = config.av.videomode[port].value
		return self.axis[mode]

	def createConfig(self, *args):
		config.av.videomode = ConfigSubDict()
		config.av.autores_mode_sd = ConfigSubDict()
		config.av.autores_mode_hd = ConfigSubDict()
		config.av.autores_mode_fhd = ConfigSubDict()
		config.av.autores_mode_uhd = ConfigSubDict()
		config.av.videorate = ConfigSubDict()
		config.av.autores_rate_sd = ConfigSubDict()
		config.av.autores_rate_hd = ConfigSubDict()
		config.av.autores_rate_fhd = ConfigSubDict()
		config.av.autores_rate_uhd = ConfigSubDict()
		portList = []  # Create list of output ports.
		for port in self.getPortList():
			if "HDMI" in port:
				portList.insert(0, (port, port))
			else:
				portList.append((port, port))
			modes = self.getModeList(port)
			if len(modes):
				config.av.videomode[port] = ConfigSelection(choices=[mode for (mode, rates) in modes])
				config.av.autores_mode_sd[port] = ConfigSelection(choices=[mode for (mode, rates) in modes])
				config.av.autores_mode_hd[port] = ConfigSelection(choices=[mode for (mode, rates) in modes])
				config.av.autores_mode_fhd[port] = ConfigSelection(choices=[mode for (mode, rates) in modes])
				config.av.autores_mode_uhd[port] = ConfigSelection(choices=[mode for (mode, rates) in modes])
			for (mode, rates) in modes:
				rateList = []
				for rate in rates:
					if rate == "auto" and not BoxInfo.getItem("have24hz"):
						continue
					rateList.append((rate, rate))
				config.av.videorate[mode] = ConfigSelection(choices=rateList)
				config.av.autores_rate_sd[mode] = ConfigSelection(choices=rateList)
				config.av.autores_rate_hd[mode] = ConfigSelection(choices=rateList)
				config.av.autores_rate_fhd[mode] = ConfigSelection(choices=rateList)
				config.av.autores_rate_uhd[mode] = ConfigSelection(choices=rateList)
		config.av.videoport = ConfigSelection(choices=portList)

		defaults = (0,  # the preset values for the offset heights
				62,   # 1.85:1
				100,  # 2.00:1
				144,  # 2.21:1
				170)  # 2.35:1

		config.av.aspectswitch = ConfigSubsection()
		config.av.aspectswitch.enabled = ConfigYesNo(default=False)
		config.av.aspectswitch.offsets = ConfigSubDict()
		for aspect in range(5):
			config.av.aspectswitch.offsets[str(aspect)] = ConfigInteger(default=defaults[aspect], limits=(0, 170))

	def isPortAvailable(self, port):  # Fix me!
		return True

	def isModeAvailable(self, port, mode, rate):  # Check if a high-level mode with a given rate is available.
		rate = self.rates[mode][rate]
		for mode in rate.values():
			if port != "HDMI":
				if mode not in self.readAvailableModes():
					return False
			elif mode not in self.modes_preferred:
				return False
		return True

	def isPortUsed(self, port):
		if port == "HDMI":
			self.readPreferredModes()
			return len(self.modes_preferred) != 0
		else:
			return True

	def isWidescreenMode(self, port, mode):  # This is only used in getOutputAspect
		return mode in self.widescreenModes

	# TODO AML
	def getAspectRatioSetting(self):
		return {
			"4_3_letterbox": 0,
			"4_3_panscan": 1,
			"16_9": 2,
			"16_9_always": 3,
			"16_10_letterbox": 4,
			"16_10_panscan": 5,
			"16_9_letterbox": 6
		}.get(config.av.aspectratio.value, config.av.aspectratio.value)

	def getFramebufferScale(self):
		return (1, 1)

	def getModeList(self, port):  # Get a list with all modes, with all rates, for a given port.
		results = []
		for mode in self.modes[port]:
			rates = [rate for rate in self.rates[mode] if self.isModeAvailable(port, mode, rate)]  # List all rates which are completely valid.
			if len(rates):  # If at least one rate is OK then add this mode.
				results.append((mode, rates))
		return results

	def getPortList(self):
		return [port for port in self.modes if self.isPortAvailable(port)]

	def setAspect(self, configElement):
		eAVControl.getInstance().setAspect(configElement.value, 1)

	def setAspectRatio(self, value):
		if value < 100:
			eAVControl.getInstance().setAspectRatio(value)
		else:  # Aspect Switcher
			value -= 100
			offset = config.av.aspectswitch.offsets[str(value)].value
			newheight = 576 - offset
			newtop = offset // 2
			if value:
				newwidth = 720
			else:
				newtop = 0
				newwidth = 0
				newheight = 0

			eAVControl.getInstance().setAspectRatio(2)  # 16:9
			eAVControl.getInstance().setVideoSize(newtop, 0, newwidth, newheight)

	def setColorFormat(self, value):
		if not self.current_port:
			self.current_port = config.av.videoport.value
		if self.current_port in ("YPbPr", "Scart-YPbPr"):
			eAVControl.getInstance().setColorFormat("yuv")
		elif self.current_port == "RCA":
			eAVControl.getInstance().setColorFormat("cvbs")
		else:
			eAVControl.getInstance().setColorFormat(value)

	def setConfiguredMode(self):
		port = config.av.videoport.value
		if port in config.av.videomode:
			mode = config.av.videomode[port].value
			if mode in config.av.videorate:
				rate = config.av.videorate[mode].value
				self.setMode(port, mode, rate)
			else:
				print("[AVSwitch] Current mode not available, not setting video mode!")
		else:
			print("[AVSwitch] Current port not available, not setting video mode!")

	def setInput(self, input):
		eAVControl.getInstance().setInput(input, 1)

	def setVideoModeDirect(self, mode):
		if BoxInfo.getItem("AmlogicFamily"):
			rate = mode[-4:].replace("hz", "Hz")
			force = int(rate[:-2])
			mode = mode[:-4]
			self.setMode("HDMI", mode, rate, force)
		else:
			eAVControl.getInstance().setVideoMode(mode)

	def setMode(self, port, mode, rate, force=None):
		print("[AVSwitch] Setting mode for port '%s', mode '%s', rate '%s'." % (port, mode, rate))
		# config.av.videoport.value = port  # We can ignore "port".
		self.current_mode = mode
		self.current_port = port
		modes = self.rates[mode][rate]

		mode50 = modes.get(50)
		mode60 = modes.get(60)
		mode24 = modes.get(24)

		if mode50 is None or force == 60:
			mode50 = mode60
		if mode60 is None or force == 50:
			mode60 = mode50
		if mode24 is None or force:
			mode24 = mode60
			if force == 50:
				mode24 = mode50

		if BoxInfo.getItem("AmlogicFamily"):
			amlmode = list(modes.values())[0]
			oldamlmode = fileReadLine("/sys/class/display/mode", default="", source=MODULE_NAME)
			fileWriteLine("/sys/class/display/mode", amlmode, source=MODULE_NAME)
			print("[AVSwitch] Amlogic setting videomode to mode: %s" % amlmode)
			fileWriteLine("/etc/u-boot.scr.d/000_hdmimode.scr", "setenv hdmimode %s" % amlmode, source=MODULE_NAME)
			fileWriteLine("/etc/u-boot.scr.d/000_outputmode.scr", "setenv outputmode %s" % amlmode, source=MODULE_NAME)
			system("update-autoexec")
			fileWriteLine("/sys/class/ppmgr/ppscaler", "1", source=MODULE_NAME)
			fileWriteLine("/sys/class/ppmgr/ppscaler", "0", source=MODULE_NAME)
			fileWriteLine("/sys/class/video/axis", self.axis[mode], source=MODULE_NAME)
			stride = fileReadLine("/sys/class/graphics/fb0/stride", default="", source=MODULE_NAME)
			limits = [int(x) for x in self.axis[mode].split()]
			config.osd.dst_left = ConfigSelectionNumber(default=limits[0], stepwidth=1, min=limits[0] - 255, max=limits[0] + 255, wraparound=False)
			config.osd.dst_top = ConfigSelectionNumber(default=limits[1], stepwidth=1, min=limits[1] - 255, max=limits[1] + 255, wraparound=False)
			config.osd.dst_width = ConfigSelectionNumber(default=limits[2], stepwidth=1, min=limits[2] - 255, max=limits[2] + 255, wraparound=False)
			config.osd.dst_height = ConfigSelectionNumber(default=limits[3], stepwidth=1, min=limits[3] - 255, max=limits[3] + 255, wraparound=False)

			if oldamlmode != amlmode:
				config.osd.dst_width.setValue(limits[0])
				config.osd.dst_height.setValue(limits[1])
				config.osd.dst_left.setValue(limits[2])
				config.osd.dst_top.setValue(limits[3])
				config.osd.dst_left.save()
				config.osd.dst_width.save()
				config.osd.dst_top.save()
				config.osd.dst_height.save()
			print("[AVSwitch] Framebuffer mode:%s  stride:%s axis:%s" % (getDesktop(0).size().width(), stride, self.axis[mode]))
			return

		success = fileWriteLine("/proc/stb/video/videomode_50hz", mode50, source=MODULE_NAME)
		if success:
			success = fileWriteLine("/proc/stb/video/videomode_60hz", mode60, source=MODULE_NAME)
		if not success:  # Fallback if no possibility to setup 50/60 hz mode
			fileWriteLine("/proc/stb/video/videomode", mode50, source=MODULE_NAME)

		if BoxInfo.getItem("have24hz"):
			fileWriteLine("/proc/stb/video/videomode_24hz", mode24, source=MODULE_NAME)

		if BRAND == "gigablue":
			# use 50Hz mode (if available) for booting
			fileWriteLine("/etc/videomode", mode50, source=MODULE_NAME)

		self.setColorFormat(config.av.colorformat.value)

	def setPolicy43(self, configElement):
		eAVControl.getInstance().setPolicy43(configElement.value, 1)

	def setPolicy169(self, configElement):
		eAVControl.getInstance().setPolicy169(configElement.value, 1)

	def setWss(self, configElement):
		eAVControl.getInstance().setWSS(configElement.value, 1)

	def saveMode(self, port, mode, rate):
		config.av.videoport.value = port
		config.av.videoport.save()
		if port in config.av.videomode:
			config.av.videomode[port].value = mode
			config.av.videomode[port].save()
		if mode in config.av.videorate:
			config.av.videorate[mode].value = rate
			config.av.videorate[mode].save()


def InitAVSwitch():
	if MACHINEBUILD == "vuduo":
		config.av.yuvenabled = ConfigBoolean(default=False)
	else:
		config.av.yuvenabled = ConfigBoolean(default=True)
	config.av.osd_alpha = ConfigSlider(default=255, increment=5, limits=(20, 255))  # Make openATV compatible with some plugins who still use config.av.osd_alpha.

	config.av.autores = ConfigSelection(default="disabled", choices=[
		("disabled", _("Disabled")),
		("simple", _("Simple")),
		("native", _("Native")),
		("all", _("All resolutions")),
		("hd", _("Only HD"))
	])

	config.av.autores_preview = NoSave(ConfigYesNo(default=False))
	config.av.autores_1080i_deinterlace = ConfigYesNo(default=False)
	choiceList = [
		("24,24", "24p/24p"),  # These display values do not require translation.
		("24,25", "24p/25p"),
		("24,30", "24p/30p"),
		("24,50", "24p/50p"),
		("24,60", "24p/60p"),
		("25,24", "25p/24p"),
		("30,24", "30p/24p"),
		("50,24", "50p/24p"),
		("60,24", "60p/24p"),
		("25,25", "25p/25p"),
		("25,30", "25p/30p"),
		("25,50", "25p/50p"),
		("25,60", "25p/60p"),
		("30,25", "30p/25p"),
		("50,25", "50p/25p"),
		("60,25", "60p/25p"),
		("30,30", "30p/30p"),
		("30,50", "30p/50p"),
		("30,60", "30p/60p"),
		("50,30", "50p/30p"),
		("60,30", "60p/30p"),
		("50,50", "50p/50p"),
		("50,60", "50p/60p"),
		("60,50", "60p/50p"),
		("60,60", "60p/60p")
	]  # First value <= 720p, second value > 720p.
	config.av.autores_24p = ConfigSelection(default="50,24", choices=choiceList)
	config.av.autores_25p = ConfigSelection(default="50,25", choices=choiceList)
	config.av.autores_30p = ConfigSelection(default="60,30", choices=choiceList)

	config.av.autores_unknownres = ConfigSelection(default="next", choices=[
		("next", _("Next higher resolution")),
		("highest", _("Highest resolution"))
	])

	choiceList = []
	for timeout in range(5, 16):
		choiceList.append((timeout, ngettext("%d Second", "%d Seconds", timeout) % timeout))
	config.av.autores_label_timeout = ConfigSelection(default=5, choices=[(0, _("Not Shown"))] + choiceList)
	config.av.autores_delay = ConfigSelectionNumber(min=0, max=3000, stepwidth=50, default=400, wraparound=True)
	config.av.autores_deinterlace = ConfigYesNo(default=False)
	hertz = _("Hz")
	if BoxInfo.getItem("AmlogicFamily"):
		config.av.autores_sd = ConfigSelection(default="720p50hz", choices=[
			("720p50hz", "720p50%s" % hertz),
			("720p", "720p"),
			("1080i50hz", "1080i50%s" % hertz),
			("1080i", "1080i")
		])
		config.av.autores_480p24 = ConfigSelection(default="1080p24hz", choices=[
			("480p24", "480p 24%s" % hertz),
			("720p24hz", "720p 24%s" % hertz),
			("1080p24hz", "1080p 24%s" % hertz)
		])
		config.av.autores_720p24 = ConfigSelection(default="720p24hz", choices=[
			("720p24hz", "720p 24%s" % hertz),
			("1080p24hz", "1080p 24%s" % hertz),
			("1080i50hz", "1080i 50%s" % hertz),
			("1080i", "1080i 60%s" % hertz)
		])
		config.av.autores_1080p24 = ConfigSelection(default="1080p24hz", choices=[
			("1080p24hz", "1080p 24%s" % hertz),
			("1080p25hz", "1080p 25%s" % hertz),
			("1080i50hz", "1080p 50%s" % hertz),
			("1080i", "1080i 60%s" % hertz)
		])
		config.av.autores_1080p25 = ConfigSelection(default="1080p25hz", choices=[
			("1080p25hz", "1080p 25%s" % hertz),
			("1080p50hz", "1080p 50%s" % hertz),
			("1080i50hz", "1080i 50%s" % hertz)
		])
		config.av.autores_1080p30 = ConfigSelection(default="1080p30hz", choices=[
			("1080p30hz", "1080p 30%s" % hertz),
			("1080p60hz", "1080p 60%s" % hertz),
			("1080i", "1080i 60%s" % hertz)
		])
		config.av.autores_2160p24 = ConfigSelection(default="2160p24hz", choices=[
			("2160p24hz", "2160p 24%s" % hertz),
			("2160p25hz", "2160p 25%s" % hertz),
			("2160p30hz", "2160p 30%s" % hertz)
		])
		config.av.autores_2160p25 = ConfigSelection(default="2160p25hz", choices=[
			("2160p25hz", "2160p 25%s" % hertz),
			("2160p50hz", "2160p 50%s" % hertz)
		])
		config.av.autores_2160p30 = ConfigSelection(default="2160p30hz", choices=[
			("2160p30hz", "2160p 30%s" % hertz),
			("2160p60hz", "2160p 60%s" % hertz)
		])

		policy_choices = [
			("4", _("Stretch nonlinear")),
			("3", _("Stretch linear")),
			("1", _("Stretch full")),
			("10", _("Ignore")),
			("11", _("Letterbox")),
			("12", _("Pan&scan")),
			("13", _("Combined")),
			("0", _("Pillarbox")),
		]

		config.av.policy_169 = ConfigSelection(default="11", choices=policy_choices)

		policy_choices = [
			("2", _("Pillarbox")),
			("6", _("Ignore")),
			("7", _("Letterbox")),
			("8", _("Pan&scan")),
			("9", _("Combined")),
		]

		config.av.policy_43 = ConfigSelection(default="8", choices=policy_choices)
	else:
		config.av.autores_sd = ConfigSelection(default="720p50", choices=[
			("720p50", "720p50"),
			("720p", "720p"),
			("1080i50", "1080i50"),
			("1080i", "1080i")
		])
		config.av.autores_480p24 = ConfigSelection(default="1080p24", choices=[
			("480p24", "480p 24%s" % hertz),
			("720p24", "720p 24%s" % hertz),
			("1080p24", "1080p 24%s" % hertz)
		])
		config.av.autores_720p24 = ConfigSelection(default="720p24", choices=[
			("720p24", "720p 24%s" % hertz),
			("1080p24", "1080p 24%s" % hertz),
			("1080i50", "1080i 50%s" % hertz),
			("1080i", "1080i 60%s" % hertz)
		])
		config.av.autores_1080p24 = ConfigSelection(default="1080p24", choices=[
			("1080p24", "1080p 24%s" % hertz),
			("1080p25", "1080p 25%s" % hertz),
			("1080i50", "1080p 50%s" % hertz),
			("1080i", "1080i 60%s" % hertz)
		])
		config.av.autores_1080p25 = ConfigSelection(default="1080p25", choices=[
			("1080p25", "1080p 25%s" % hertz),
			("1080p50", "1080p 50%s" % hertz),
			("1080i50", "1080i 50%s" % hertz)
		])
		config.av.autores_1080p30 = ConfigSelection(default="1080p30", choices=[
			("1080p30", "1080p 30%s" % hertz),
			("1080p60", "1080p 60%s" % hertz),
			("1080i", "1080i 60%s" % hertz)
		])
		config.av.autores_2160p24 = ConfigSelection(default="2160p24", choices=[
			("2160p24", "2160p 24%s" % hertz),
			("2160p25", "2160p 25%s" % hertz),
			("2160p30", "2160p 30%s" % hertz)
		])
		config.av.autores_2160p25 = ConfigSelection(default="2160p25", choices=[
			("2160p25", "2160p 25%s" % hertz),
			("2160p50", "2160p 50%s" % hertz)
		])
		config.av.autores_2160p30 = ConfigSelection(default="2160p30", choices=[
			("2160p30", "2160p 30%s" % hertz),
			("2160p60", "2160p 60%s" % hertz)
		])

		# Some boxes have a redundant proc entry for policy2 choices, but some don't (The choices are from a 16:9 point of view anyways)
		policy2_choices_proc = "/proc/stb/video/policy2_choices"
		if not exists(policy2_choices_proc):
			policy2_choices_proc = "/proc/stb/video/policy_choices"

		policy2_choices_raw = "letterbox"
		try:
			with open(policy2_choices_proc, "r") as fd:
				policy2_choices_raw = fd.read()
		except OSError:
			pass

		policy2_choices = {}

		if "letterbox" in policy2_choices_raw:
			# TRANSLATORS: (aspect ratio policy: black bars on top/bottom) in doubt, keep english term.
			policy2_choices.update({"letterbox": _("Letterbox")})

		if "panscan" in policy2_choices_raw:
			# TRANSLATORS: (aspect ratio policy: cropped content on left/right) in doubt, keep english term
			policy2_choices.update({"panscan": _("Pan&scan")})

		if "nonliner" in policy2_choices_raw and not "nonlinear" in policy2_choices_raw:
			# TRANSLATORS: (aspect ratio policy: display as fullscreen, with stretching the top/bottom (Center of picture maintains aspect, top/bottom lose aspect heaver than on linear stretch))
			policy2_choices.update({"nonliner": _("Stretch nonlinear")})
		if "nonlinear" in policy2_choices_raw:
			# TRANSLATORS: (aspect ratio policy: display as fullscreen, with stretching the top/bottom (Center of picture maintains aspect, top/bottom lose aspect heaver than on linear stretch))
			policy2_choices.update({"nonlinear": _("Stretch nonlinear")})

		if "scale" in policy2_choices_raw and "auto" not in policy2_choices_raw and "bestfit" not in policy2_choices_raw:
			# TRANSLATORS: (aspect ratio policy: display as fullscreen, with stretching all parts of the picture with the same factor (All parts lose aspect))
			policy2_choices.update({"scale": _("Stretch linear")})
		if "full" in policy2_choices_raw:
			# TRANSLATORS: (aspect ratio policy: display as fullscreen, with stretching all parts of the picture with the same factor (force aspect))
			policy2_choices.update({"full": _("Stretch full")})
		if "auto" in policy2_choices_raw and "bestfit" not in policy2_choices_raw:
			# TRANSLATORS: (aspect ratio policy: display as fullscreen, with stretching all parts of the picture with the same factor (All parts lose aspect))
			policy2_choices.update({"auto": _("Stretch linear")})
		if "bestfit" in policy2_choices_raw:
			# TRANSLATORS: (aspect ratio policy: display as fullscreen, with stretching all parts of the picture with the same factor (All parts lose aspect))
			policy2_choices.update({"bestfit": _("Stretch linear")})

		config.av.policy_169 = ConfigSelection(default="letterbox", choices=policy2_choices)

		policy_choices_proc = "/proc/stb/video/policy_choices"
		policy_choices_raw = "panscan"
		try:
			with open(policy_choices_proc, "r") as fd:
				policy_choices_raw = fd.read()
		except OSError:
			pass

		policy_choices = {}

		if "pillarbox" in policy_choices_raw and "panscan" not in policy_choices_raw:
			# Very few boxes support "pillarbox" as an alias for "panscan" (Which in fact does pillarbox)
			# So only add "pillarbox" if "panscan" is not listed in choices

			# TRANSLATORS: (aspect ratio policy: black bars on left/right) in doubt, keep english term.
			policy_choices.update({"pillarbox": _("Pillarbox")})

		if "panscan" in policy_choices_raw:
			# DRIVER BUG:	"panscan" in /proc actually does "pillarbox" (That's probably why an alias to it named "pillarbox" existed)!
			#		Interpret "panscan" setting with a "Pillarbox" text in order to show the correct value in GUI

			# TRANSLATORS: (aspect ratio policy: black bars on left/right) in doubt, keep english term.
			policy_choices.update({"panscan": _("Pillarbox")})

		if "letterbox" in policy_choices_raw:
			# DRIVER BUG:	"letterbox" in /proc actually does pan&scan
			#		"letterbox" and 4:3 content on 16:9 TVs is mutually exclusive, as "letterbox" is the method to show wide content on narrow TVs
			#		Probably the bug arose as the driver actually does the same here as it would for wide content on narrow TVs (It stretches the picture to fit width)

			# TRANSLATORS: (aspect ratio policy: Fit width, cut/crop top and bottom (Maintain aspect ratio))
			policy_choices.update({"letterbox": _("Pan&scan")})

		if "nonliner" in policy_choices_raw and "nonlinear" not in policy_choices_raw:
			# TRANSLATORS: (aspect ratio policy: display as fullscreen, with stretching the left/right (Center 50% of picture maintain aspect, left/right 25% lose aspect heaver than on linear stretch))
			policy_choices.update({"nonliner": _("Stretch nonlinear")})
		if "nonlinear" in policy_choices_raw:
			# TRANSLATORS: (aspect ratio policy: display as fullscreen, with stretching the left/right (Center 50% of picture maintain aspect, left/right 25% lose aspect heaver than on linear stretch))
			policy_choices.update({"nonlinear": _("Stretch nonlinear")})

		# "auto", "bestfit" and "scale" are aliasses for the same: Stretch linear
		if "scale" in policy_choices_raw and "auto" not in policy_choices_raw and "bestfit" not in policy_choices_raw:
			# TRANSLATORS: (aspect ratio policy: display as fullscreen, with stretching all parts of the picture with the same factor (All parts lose aspect))
			policy_choices.update({"scale": _("Stretch linear")})
		if "full" in policy_choices_raw:
			# TRANSLATORS: (aspect ratio policy: display as fullscreen, with stretching all parts of the picture with the same factor (force aspect))
			policy_choices.update({"full": _("Stretch full")})
		if "auto" in policy_choices_raw and "bestfit" not in policy_choices_raw:
			# TRANSLATORS: (aspect ratio policy: display as fullscreen, with stretching all parts of the picture with the same factor (All parts lose aspect))
			policy_choices.update({"auto": _("Stretch linear")})
		if "bestfit" in policy_choices_raw:
			# TRANSLATORS: (aspect ratio policy: display as fullscreen, with stretching all parts of the picture with the same factor (All parts lose aspect))
			policy_choices.update({"bestfit": _("Stretch linear")})

		config.av.policy_43 = ConfigSelection(default="panscan", choices=policy_choices)

	config.av.smart1080p = ConfigSelection(default="false", choices=[
		("false", _("Off")),
		("true", "1080p50: 24p/50p/60p"),
		("2160p50", "2160p50: 24p/50p/60p"),
		("1080i50", "1080i50: 24p/50i/60i"),
		("720p50", "720p50: 24p/50p/60p")
	])

	choiceList = [
		("cvbs", "CVBS"),
		("rgb", "RGB"),
		("svideo", "S-Video")
	]
	if config.av.yuvenabled.value:  # When YUV is not enabled, don't let the user select it.
		choiceList.append(("yuv", "YPbPr"))

	config.av.colorformat = ConfigSelection(default="rgb", choices=choiceList)

	config.av.aspectratio = ConfigSelection(default="16_9", choices=[
		("4_3_letterbox", _("4:3 Letterbox")),
		("4_3_panscan", _("4:3 PanScan")),
		("16_9", "16:9"),
		("16_9_always", _("16:9 Always")),
		("16_10_letterbox", _("16:10 Letterbox")),
		("16_10_panscan", _("16:10 PanScan")),
		("16_9_letterbox", _("16:9 Letterbox"))
	])

	config.av.aspect = ConfigSelection(default="16:9", choices=[
		("4:3", "4:3"),
		("16:9", "16:9"),
		("16:10", "16:10"),
		("auto", _("Automatic"))
	])

	config.av.tvsystem = ConfigSelection(default="pal", choices=[
		("pal", "PAL"),
		("ntsc", "NTSC"),
		("multinorm", _("multinorm"))
	])

	config.av.wss = ConfigEnableDisable(default=True)
	config.av.generalAC3delay = ConfigSelectionNumber(-1000, 1000, 5, default=0)
	config.av.generalPCMdelay = ConfigSelectionNumber(-1000, 1000, 5, default=0)
	config.av.vcrswitch = ConfigEnableDisable(default=False)

	#config.av.aspect.setValue('16:9')
	config.av.aspect.addNotifier(iAVSwitch.setAspect)
	config.av.wss.addNotifier(iAVSwitch.setWss)
	config.av.policy_43.addNotifier(iAVSwitch.setPolicy43)
	config.av.policy_169.addNotifier(iAVSwitch.setPolicy169)

	def setAspectRatio(configElement):  # Not used
		aspects = {
			"4_3_letterbox": 0,
			"4_3_panscan": 1,
			"16_9": 2,
			"16_9_always": 3,
			"16_10_letterbox": 4,
			"16_10_panscan": 5,
			"16_9_letterbox": 6
		}
		iAVSwitch.setAspectRatio(aspects[configElement.value])

	def setColorFormat(configElement):
		if config.av.videoport and config.av.videoport.value in ("YPbPr", "Scart-YPbPr"):
			iAVSwitch.setColorFormat("yuv")
		elif config.av.videoport and config.av.videoport.value in ("RCA"):
			iAVSwitch.setColorFormat("cvbs")
		else:
			iAVSwitch.setColorFormat(configElement.value)
	config.av.colorformat.addNotifier(setColorFormat)

	iAVSwitch.setInput("encoder")  # init on startup

	BoxInfo.setItem("ScartSwitch", eAVControl.getInstance().hasScartSwitch())

	bypassEDID = fileReadLine("/proc/stb/hdmi/bypass_edid_checking", default=None, source=MODULE_NAME)
	bypassEDID = bypassEDID.split() if bypassEDID else False

	BoxInfo.setItem("Canedidchecking", bypassEDID)

	if bypassEDID:
		config.av.bypass_edid_checking = ConfigYesNo(default=True)

		def setEDIDBypass(configElement):
			if configElement.value:
				value = "00000001" if configElement.value else "00000000"
				fileWriteLine("/proc/stb/hdmi/bypass_edid_checking", value, source=MODULE_NAME)
		config.av.bypass_edid_checking.addNotifier(setEDIDBypass)
	else:
		config.av.bypass_edid_checking = ConfigNothing()

	def setUnsupportModes(configElement):
		iAVSwitch.readPreferredModes()
		iAVSwitch.createConfig()
		# print("[AVSwitch] Setting EDID override to '%s'." % configElement.value)

	config.av.edid_override.addNotifier(setUnsupportModes)

	colorspace = fileReadLine("/proc/stb/video/hdmi_colorspace", default=None, source=MODULE_NAME)
	colorspace = colorspace.split() if colorspace else False

	BoxInfo.setItem("havecolorspace", colorspace)
	if colorspace:
		if MACHINEBUILD in ("vusolo4k", "vuuno4k", "vuuno4kse", "vuultimo4k", "vuduo4k", "vuduo4kse"):
			default = "Edid(Auto)"
			choiceList = [
				("Edid(Auto)", _("Auto")),
				("Hdmi_Rgb", "RGB"),
				("444", "YCbCr 444"),
				("422", "YCbCr 422"),
				("420", "YCbCr 420")
			]
		elif MACHINEBUILD in ("dm900", "dm920", "vuzero4k"):
			default = "Edid(Auto)"
			choiceList = [
				("Edid(Auto)", _("Auto")),
				("Hdmi_Rgb", "RGB"),
				("Itu_R_BT_709", "BT.709"),
				("DVI_Full_Range_RGB", _("Full Range RGB")),
				("FCC", "FCC 1953"),
				("Itu_R_BT_470_2_BG", "BT.470 BG"),
				("Smpte_170M", "SMPTE 170M"),
				("Smpte_240M", "SMPTE 240M"),
				("Itu_R_BT_2020_NCL", "BT.2020 NCL"),
				("Itu_R_BT_2020_CL", "BT.2020 CL"),
				("XvYCC_709", "BT.709 XvYCC"),
				("XvYCC_601", "BT.601 XvYCC")
			]
		else:
			default = "auto"
			choiceList = [
				("auto", _("Auto")),
				("rgb", "RGB"),
				("420", "YCbCr 420"),
				("422", "YCbCr 422"),
				("444", "YCbCr 444")
			]
		config.av.hdmicolorspace = ConfigSelection(default=default, choices=choiceList)

		def setHDMIColorspace(configElement):
			fileWriteLine("/proc/stb/video/hdmi_colorspace", configElement.value, source=MODULE_NAME)

		config.av.hdmicolorspace.addNotifier(setHDMIColorspace)
	else:
		config.av.hdmicolorspace = ConfigNothing()

	colorimetry = fileReadLine("/proc/stb/video/hdmi_colorimetry", default=None, source=MODULE_NAME)
	colorimetry = colorimetry.split() if colorimetry else False

	BoxInfo.setItem("havecolorimetry", colorimetry)
	if colorimetry:
		config.av.hdmicolorimetry = ConfigSelection(default="auto", choices=[
			("auto", _("Auto")),
			("bt2020ncl", "BT.2020 NCL"),
			("bt2020cl", "BT.2020 CL"),
			("bt709", "BT.709")
		])

		def setHDMIColorimetry(configElement):
			sleep(0.1)
			fileWriteLine("/proc/stb/video/hdmi_colorimetry", configElement.value, source=MODULE_NAME)
		config.av.hdmicolorimetry.addNotifier(setHDMIColorimetry)
	else:
		config.av.hdmicolorimetry = ConfigNothing()

	boxMode = fileReadLine("/proc/stb/info/boxmode", default=None, source=MODULE_NAME)
	boxMode = boxMode.split() if boxMode else False

	BoxInfo.setItem("haveboxmode", boxMode)
	if boxMode:
		config.av.boxmode = ConfigSelection(default="12", choices=[
			("12", _("Enable PiP no HDR")),
			("1", _("12bit 4:2:0/4:2:2 no PiP"))
		])

		def setBoxMode(configElement):
			fileWriteLine("/proc/stb/info/boxmode", configElement.value, source=MODULE_NAME)
		config.av.boxmode.addNotifier(setBoxMode)
	else:
		config.av.boxmode = ConfigNothing()

	colorDepth = fileReadLine("/proc/stb/video/hdmi_colordepth", default=None, source=MODULE_NAME)
	colorDepth = colorDepth.split() if colorDepth else False

	BoxInfo.setItem("havehdmicolordepth", colorDepth)

	if colorDepth:
		config.av.hdmicolordepth = ConfigSelection(default="auto", choices=[
			("auto", _("Auto")),
			("8bit", _("8bit")),
			("10bit", _("10bit")),
			("12bit", _("12bit"))
		])

		def setColorDepth(configElement):
			fileWriteLine("/proc/stb/video/hdmi_colordepth", configElement.value, source=MODULE_NAME)
		config.av.hdmicolordepth.addNotifier(setColorDepth)
	else:
		config.av.hdmicolordepth = ConfigNothing()

	syncMode = fileReadLine("/proc/stb/video/sync_mode_choices", default=None, source=MODULE_NAME)
	syncMode = syncMode.split() if syncMode else False

	BoxInfo.setItem("havesyncmode", syncMode)

	if syncMode:
		def setSyncMode(configElement):
			fileWriteLine("/proc/stb/video/sync_mode", configElement.value, source=MODULE_NAME)

		config.av.sync_mode = ConfigSelection(default="slow", choices=[
			("slow", _("Slow Motion")),
			("hold", _("Hold First Frame")),
			("black", _("Black Screen")),
		])
		config.av.sync_mode.addNotifier(setSyncMode)
	else:
		config.av.sync_mode = ConfigNothing()

	if exists("/sys/class/amhdmitx/amhdmitx0/config"):
		AMLHDRSupport = True
	else:
		AMLHDRSupport = False

	BoxInfo.setItem("haveamlhdrsupport", AMLHDRSupport)

	if AMLHDRSupport:

		config.av.amlhdr10_support = ConfigSelection(default="hdr10-2", choices=[
			("hdr10-0", _("Force enabled")),
			("hdr10-1", _("Force disabled")),
			("hdr10-2", _("Controlled by HDMI"))
		])

		def setAMLHDR10(configElement):
			fileWriteLine("/sys/class/amhdmitx/amhdmitx0/config", configElement.value, source=MODULE_NAME)

		config.av.amlhdr10_support.addNotifier(setAMLHDR10)
	else:
		config.av.amlhdr10_support = ConfigNothing()

	if AMLHDRSupport:

		config.av.amlhlg_support = ConfigSelection(default="hlg-2", choices=[
			("hlg-0", _("Force enabled")),
			("hlg-1", _("Force disabled")),
			("hlg-2", _("Controlled by HDMI"))
		])

		def setAMLHLG(configElement):
			fileWriteLine("/sys/class/amhdmitx/amhdmitx0/config", configElement.value, source=MODULE_NAME)

		config.av.amlhlg_support.addNotifier(setAMLHLG)
	else:
		config.av.amlhlg_support = ConfigNothing()

	hdrType = fileReadLine("/proc/stb/video/hdmi_hdrtype", default=None, source=MODULE_NAME)
	hdrType = hdrType.split() if hdrType else False

	BoxInfo.setItem("havehdmihdrtype", hdrType)

	if hdrType:
		config.av.hdmihdrtype = ConfigSelection(default="auto", choices=[
			("auto", _("Auto")),
			("dolby", "Dolby Vision"),
			("none", "SDR"),
			("hdr10", "HDR10"),
			# ("hdr10+", "HDR10+"),
			("hlg", "HLG")
		])

		def setHDRType(configElement):
			fileWriteLine("/proc/stb/video/hdmi_hdrtype", configElement.value, source=MODULE_NAME)

		config.av.hdmihdrtype.addNotifier(setHDRType)
	else:
		config.av.hdmihdrtype = ConfigNothing()

	hdrSupport = fileReadLine("/proc/stb/hdmi/hlg_support_choices", default=None, source=MODULE_NAME)
	hdrSupport = hdrSupport.split() if hdrSupport else False

	BoxInfo.setItem("HDRSupport", hdrSupport)

	if hdrSupport:
		def setHlgSupport(configElement):
			fileWriteLine("/proc/stb/hdmi/hlg_support", configElement.value, source=MODULE_NAME)

		config.av.hlg_support = ConfigSelection(default="auto(EDID)", choices=[
			("auto(EDID)", _("Controlled by HDMI")),
			("yes", _("Force enabled")),
			("no", _("Force disabled"))
		])
		config.av.hlg_support.addNotifier(setHlgSupport)

		def setHdr10Support(configElement):
			fileWriteLine("/proc/stb/hdmi/hdr10_support", configElement.value, source=MODULE_NAME)

		config.av.hdr10_support = ConfigSelection(default="auto(EDID)", choices=[
			("auto(EDID)", _("Controlled by HDMI")),
			("yes", _("Force enabled")),
			("no", _("Force disabled"))
		])
		config.av.hdr10_support.addNotifier(setHdr10Support)

		def setDisable12Bit(configElement):
			fileWriteLine("/proc/stb/video/disable_12bit", "1" if configElement.value else "0", source=MODULE_NAME)

		config.av.allow_12bit = ConfigYesNo(default=False)
		config.av.allow_12bit.addNotifier(setDisable12Bit)

		def setDisable10Bit(configElement):
			fileWriteLine("/proc/stb/video/disable_10bit", "1" if configElement.value else "0", source=MODULE_NAME)

		config.av.allow_10bit = ConfigYesNo(default=False)
		config.av.allow_10bit.addNotifier(setDisable10Bit)

	audioSource = fileReadLine("/sys/devices/virtual/amhdmitx/amhdmitx0/audio_source" if BoxInfo.getItem("AmlogicFamily") else "/proc/stb/hdmi/audio_source", default=None, source=MODULE_NAME)
	audioSource = audioSource.split() if audioSource else False

	BoxInfo.setItem("Canaudiosource", audioSource)

	if audioSource:
		if BoxInfo.getItem("AmlogicFamily"):
			config.av.audio_source = ConfigSelection(default="0", choices=[
				("0", "PCM"),
				("1", "S/PDIF"),
				("2", _("Bluetooth"))
			])
		else:
			config.av.audio_source = ConfigSelection(default="pcm", choices=[
				("pcm", "PCM"),
				("spdif", "S/PDIF")
			])

		def setAudioSource(configElement):
			fileWriteLine("/sys/devices/virtual/amhdmitx/amhdmitx0/audio_source" if BoxInfo.getItem("AmlogicFamily") else "/proc/stb/hdmi/audio_source", configElement.value, source=MODULE_NAME)

		config.av.audio_source.addNotifier(setAudioSource)
	else:
		config.av.audio_source = ConfigNothing()

	surround = fileReadLine("/proc/stb/audio/3d_surround_choices", default=None, source=MODULE_NAME)
	surround = surround.split() if surround else False

	BoxInfo.setItem("Can3DSurround", surround)

	if surround:
		config.av.surround_3d = ConfigSelection(default="none", choices=[
			("none", _("Off")),
			("hdmi", "HDMI"),
			("spdif", "S/PDIF"),
			("dac", "DAC")
		])

		def set3DSurround(configElement):
			fileWriteLine("/proc/stb/audio/3d_surround", configElement.value, source=MODULE_NAME)

		config.av.surround_3d.addNotifier(set3DSurround)
	else:
		config.av.surround_3d = ConfigNothing()

	surroundSpeaker = fileReadLine("/proc/stb/audio/3d_surround_speaker_position_choices", default=None, source=MODULE_NAME)
	surroundSpeaker = surroundSpeaker.split() if surroundSpeaker else False

	BoxInfo.setItem("Can3DSpeaker", surroundSpeaker)

	if surroundSpeaker:
		config.av.surround_3d_speaker = ConfigSelection(default="center", choices=[
			("center", _("Center")),
			("wide", _("Wide")),
			("extrawide", _("Extra wide"))
		])

		def set3DSurroundSpeaker(configElement):
			fileWriteLine("/proc/stb/audio/3d_surround_speaker_position", configElement.value, source=MODULE_NAME)

		config.av.surround_3d_speaker.addNotifier(set3DSurroundSpeaker)
	else:
		config.av.surround_3d_speaker = ConfigNothing()

	autoVolume = fileReadLine("/proc/stb/audio/avl_choices", default=None, source=MODULE_NAME)
	autoVolume = autoVolume.split() if autoVolume else False

	BoxInfo.setItem("CanAutoVolume", autoVolume)

	if autoVolume:
		config.av.autovolume = ConfigSelection(default="none", choices=[
			("none", _("Off")),
			("hdmi", "HDMI"),
			("spdif", "S/PDIF"),
			("dac", "DAC")
		])

		def setAutoVolume(configElement):
			fileWriteLine("/proc/stb/audio/avl", configElement.value, source=MODULE_NAME)

		config.av.autovolume.addNotifier(setAutoVolume)
	else:
		config.av.autovolume = ConfigNothing()

	filename = "/proc/stb/audio/multichannel_pcm"
	multiChannel = exists(filename) and access(filename, W_OK)

	BoxInfo.setItem("supportPcmMultichannel", multiChannel)
	if multiChannel:
		config.av.pcm_multichannel = ConfigYesNo(default=False)

		def setPCMMultichannel(configElement):
			fileWriteLine("/proc/stb/audio/multichannel_pcm", configElement.value and "enable" or "disable", source=MODULE_NAME)
		config.av.pcm_multichannel.addNotifier(setPCMMultichannel)
	config.av.volume_stepsize = ConfigSelectionNumber(min=1, max=10, stepwidth=1, default=5)

	def setVolumeStepSize(configElement):
		eDVBVolumecontrol.getInstance().setVolumeSteps(int(configElement.value))
	config.av.volume_stepsize.addNotifier(setVolumeStepSize)
	config.av.volume_stepsize_fastmode = ConfigSelectionNumber(min=1, max=10, stepwidth=1, default=5)
	config.av.volume_hide_mute = ConfigYesNo(default=True)

	if BoxInfo.getItem("AmlogicFamily"):
		downmixAC3 = True
		BoxInfo.setItem("CanPcmMultichannel", True)
	else:
		downmixAC3 = fileReadLine("/proc/stb/audio/ac3_choices", default=None, source=MODULE_NAME)
		if downmixAC3:
			downmixAC3 = "downmix" in downmixAC3
		else:
			downmixAC3 = False
			BoxInfo.setItem("CanPcmMultichannel", False)

	BoxInfo.setItem("CanDownmixAC3", downmixAC3)
	if downmixAC3:
		if MACHINEBUILD in ("dm900", "dm920", "dm7080", "dm800"):
			config.av.downmix_ac3 = ConfigSelection(default="downmix", choices=[
				("downmix", _("Downmix")),
				("passthrough", _("Pass-through")),
				("multichannel", _("Convert to multi-channel PCM")),
				("hdmi_best", _("Use best / Controlled by HDMI"))
			])

		elif MACHINEBUILD in ("dreamone", "dreamtwo"):
			config.av.downmix_ac3 = ConfigSelection(default="0", choices=[
				("0", _("Downmix")),
				("1", _("Pass-through")),
				("2", _("Use best / Controlled by HDMI"))
			])
		else:
			config.av.downmix_ac3 = ConfigYesNo(default=True)

		def setAC3Downmix(configElement):
			if BoxInfo.getItem("AmlogicFamily"):
				fileWriteLine("/sys/class/audiodsp/digital_raw", configElement.value, source=MODULE_NAME)
			else:
				value = configElement.value and "downmix" or "passthrough"
				if MACHINEBUILD in ("dm900", "dm920", "dm7080", "dm800"):
					value = configElement.value
				fileWriteLine("/proc/stb/audio/ac3", value, source=MODULE_NAME)

			if BoxInfo.getItem("supportPcmMultichannel", False) and not configElement.value:
				BoxInfo.setItem("CanPcmMultichannel", True)
			else:
				BoxInfo.setItem("CanPcmMultichannel", False)
				if multiChannel:
					config.av.pcm_multichannel.setValue(False)

		config.av.downmix_ac3.addNotifier(setAC3Downmix)
	else:
		config.av.downmix_ac3 = ConfigNothing()

	AC3plusTranscode = fileReadLine("/proc/stb/audio/ac3plus_choices", default=None, source=MODULE_NAME)
	AC3plusTranscode = AC3plusTranscode.split() if AC3plusTranscode else False

	BoxInfo.setItem("CanAC3plusTranscode", AC3plusTranscode)

	if AC3plusTranscode:
		if MACHINEBUILD in ("dm900", "dm920", "dm7080", "dm800"):
			choiceList = [
					("use_hdmi_caps", _("Controlled by HDMI")),
					("force_ac3", _("Convert to AC3")),
					("multichannel", _("Convert to multi-channel PCM")),
					("hdmi_best", _("Use best / Controlled by HDMI")),
					("force_ddp", _("Force AC3plus"))
				]
		elif MACHINEBUILD in ("gbquad4k", "gbue4k", "gbx34k"):
			choiceList = [
					("downmix", _("Downmix")),
					("passthrough", _("Pass-through")),
					("force_ac3", _("Convert to AC3")),
					("multichannel", _("Convert to multi-channel PCM")),
					("force_dts", _("Convert to DTS"))
				]
		else:
			choiceList = [
					("use_hdmi_caps", _("Controlled by HDMI")),
					("force_ac3", _("Convert to AC3"))
				]

		config.av.transcodeac3plus = ConfigSelection(default="force_ac3", choices=choiceList)

		def setAC3plusTranscode(configElement):
			fileWriteLine("/proc/stb/audio/ac3plus", configElement.value, source=MODULE_NAME)

		config.av.transcodeac3plus.addNotifier(setAC3plusTranscode)

	dtsHD = fileReadLine("/proc/stb/audio/dtshd_choices", default=None, source=MODULE_NAME)
	dtsHD = dtsHD.split() if dtsHD else False

	BoxInfo.setItem("CanDTSHD", dtsHD)
	if dtsHD:
		if MACHINEBUILD in ("dm7080", "dm820"):
			default = "use_hdmi_caps"
			choiceList = [
				("use_hdmi_caps", _("Controlled by HDMI")),
				("force_dts", _("Convert to DTS"))
			]
		else:
			default = "downmix"
			choiceList = [
				("downmix", _("Downmix")),
				("force_dts", _("Convert to DTS")),
				("use_hdmi_caps", _("Controlled by HDMI")),
				("multichannel", _("Convert to multi-channel PCM")),
				("hdmi_best", _("Use best / Controlled by HDMI"))
			]
		config.av.dtshd = ConfigSelection(default=default, choices=choiceList)

		def setDTSHD(configElement):
			fileWriteLine("/proc/stb/audio/dtshd", configElement.value, source=MODULE_NAME)

		config.av.dtshd.addNotifier(setDTSHD)

	wmaPro = fileReadLine("/proc/stb/audio/wmapro_choices", default=None, source=MODULE_NAME)
	wmaPro = wmaPro.split() if wmaPro else False

	BoxInfo.setItem("CanWMAPRO", wmaPro)
	if wmaPro:

		config.av.wmapro = ConfigSelection(default="downmix", choices=[
			("downmix", _("Downmix")),
			("passthrough", _("Pass-through")),
			("multichannel", _("Convert to multi-channel PCM")),
			("hdmi_best", _("Use best / Controlled by HDMI"))
		])

		def setWMAPro(configElement):
			fileWriteLine("/proc/stb/audio/wmapro", configElement.value, source=MODULE_NAME)

		config.av.wmapro.addNotifier(setWMAPro)

	dtsDownmix = fileReadLine("/proc/stb/audio/dts_choices", default=None, source=MODULE_NAME)
	dtsDownmix = "downmix" in dtsDownmix if dtsDownmix else False

	BoxInfo.setItem("CanDownmixDTS", dtsDownmix)
	if dtsDownmix:
		config.av.downmix_dts = ConfigYesNo(default=True)

		def setDTSDownmix(configElement):
			fileWriteLine("/proc/stb/audio/dts", configElement.value and "downmix" or "passthrough", source=MODULE_NAME)
		config.av.downmix_dts.addNotifier(setDTSDownmix)

	aacDownmix = fileReadLine("/proc/stb/audio/aac_choices", default=None, source=MODULE_NAME)
	aacDownmix = "downmix" in aacDownmix if aacDownmix else False

	BoxInfo.setItem("CanDownmixAAC", aacDownmix)
	if aacDownmix:
		if MACHINEBUILD in ("dm900", "dm920", "dm7080", "dm800"):

			config.av.downmix_aac = ConfigSelection(default="downmix", choices=[
				("downmix", _("Downmix")),
				("passthrough", _("Pass-through")),
				("multichannel", _("Convert to multi-channel PCM")),
				("hdmi_best", _("Use best / Controlled by HDMI"))
			])

		elif MACHINEBUILD in ("gbquad4k", "gbue4k", "gbx34k"):

			config.av.downmix_aac = ConfigSelection(default="downmix", choices=[
				("downmix", _("Downmix")),
				("passthrough", _("Pass-through")),
				("multichannel", _("Convert to multi-channel PCM")),
				("force_ac3", _("Convert to AC3")),
				("force_dts", _("Convert to DTS")),
				("use_hdmi_cacenter", _("Use best / Controlled by HDMI")),
				("wide", _("Wide")),
				("extrawide", _("Extra wide"))
			])

		else:
			config.av.downmix_aac = ConfigYesNo(default=True)

		def setAACDownmix(configElement):
			value = configElement.value if MACHINEBUILD in ("dm900", "dm920", "dm7080", "dm800", "gbquad4k", "gbue4k", "gbx34k") else configElement.value and "downmix" or "passthrough"
			fileWriteLine("/proc/stb/audio/aac", value, source=MODULE_NAME)

		config.av.downmix_aac.addNotifier(setAACDownmix)

	aacplusDownmix = fileReadLine("/proc/stb/audio/aacplus_choices", default=None, source=MODULE_NAME)
	aacplusDownmix = "downmix" in aacplusDownmix if aacplusDownmix else False

	BoxInfo.setItem("CanDownmixAACPlus", aacplusDownmix)
	if aacplusDownmix:
		config.av.downmix_aacplus = ConfigSelection(default="downmix", choices=[
			("downmix", _("Downmix")),
			("passthrough", _("Pass-through")),
			("multichannel", _("Convert to multi-channel PCM")),
			("force_ac3", _("Convert to AC3")),
			("force_dts", _("Convert to DTS")),
			("use_hdmi_cacenter", _("Use best / Controlled by HDMI")),
			("wide", _("Wide")),
			("extrawide", _("Extra wide"))
		])

		def setAACDownmixPlus(configElement):
			fileWriteLine("/proc/stb/audio/aacplus", configElement.value, source=MODULE_NAME)

		config.av.downmix_aacplus.addNotifier(setAACDownmixPlus)

	if exists("/proc/stb/audio/aac_transcode_choices"):
		aacTranscodeAll = [("off", _("Off")), ("ac3", "AC3"), ("dts", "DTS")]
		# The translation text must look exactly like the read value. It is then adjusted with the PO file

		aactranscodeChoices = fileReadLine("/proc/stb/audio/aac_transcode_choices", default=None, source=MODULE_NAME)
		aactranscodeChoices = aactranscodeChoices.split() if aactranscodeChoices else []
		aacTranscode = [(x[0], x[1]) for x in aacTranscodeAll if x[0] in aactranscodeChoices]
		default = aacTranscode[0][0] if aacTranscode else "off"
		print("[AVSwitch] aactranscodeChoices choices=%s, default=%s" % (aactranscodeChoices, default))

	else:
		aacTranscode = False

	BoxInfo.setItem("CanAACTranscode", aacTranscode)

	if aacTranscode:
		def setAACTranscode(configElement):
			fileWriteLine("/proc/stb/audio/aac_transcode", configElement.value, source=MODULE_NAME)

		config.av.transcodeaac = ConfigSelection(default=default, choices=aacTranscode)
		config.av.transcodeaac.addNotifier(setAACTranscode)
	else:
		config.av.transcodeaac = ConfigNothing()

	btAudio = fileReadLine("/proc/stb/audio/btaudio", default=None, source=MODULE_NAME)
	btAudio = btAudio.split() if btAudio else False

	BoxInfo.setItem("CanBTAudio", btAudio)
	if btAudio:
		config.av.btaudio = ConfigOnOff(default=False)

		def setBTAudio(configElement):
			fileWriteLine("/proc/stb/audio/btaudio", "on" if configElement.value else "off", source=MODULE_NAME)

		config.av.btaudio.addNotifier(setBTAudio)
	else:
		config.av.btaudio = ConfigNothing()

	btAudioDelay = fileReadLine("/proc/stb/audio/btaudio_delay", default=None, source=MODULE_NAME)
	btAudioDelay = btAudioDelay.split() if btAudioDelay else False

	BoxInfo.setItem("CanBTAudioDelay", btAudioDelay)
	if btAudioDelay:
		config.av.btaudiodelay = ConfigSelectionNumber(min=-1000, max=1000, stepwidth=5, default=0)

		def setBTAudioDelay(configElement):
			fileWriteLine("/proc/stb/audio/btaudio_delay", format(configElement.value * 90, "x"), source=MODULE_NAME)

		config.av.btaudiodelay.addNotifier(setBTAudioDelay)
	else:
		config.av.btaudiodelay = ConfigNothing()

	if exists("/proc/stb/vmpeg/0/pep_scaler_sharpness"):
		default = 5 if MACHINEBUILD in ("gbquad", "gbquadplus") else 13
		config.av.scaler_sharpness = ConfigSlider(default=default, limits=(0, 26))

		def setScalerSharpness(configElement):
			error = False
			if not fileWriteLine("/proc/stb/vmpeg/0/pep_scaler_sharpness", "%0.8X\n" % configElement.value, source=MODULE_NAME):
				error = True
			if not error and not fileWriteLine("/proc/stb/vmpeg/0/pep_apply", "1", source=MODULE_NAME):
				error = True
			if error:
				print("[AVSwitch] Setting scaler sharpness to '%0.8X' failed!" % configElement.value)
			else:
				print("[AVSwitch] Setting scaler sharpness to '%0.8X'." % configElement.value)

		config.av.scaler_sharpness.addNotifier(setScalerSharpness)
	else:
		config.av.scaler_sharpness = NoSave(ConfigNothing())

	iAVSwitch.setConfiguredMode()


class VideomodeHotplug:
	def __init__(self):
		pass

	def start(self):
		iAVSwitch.on_hotplug.append(self.hotplug)

	def stop(self):
		iAVSwitch.on_hotplug.remove(self.hotplug)

	def hotplug(self, what):
		print("[AVSwitch] Hot-plug detected on port '%s'." % what)
		port = config.av.videoport.value
		mode = config.av.videomode[port].value
		rate = config.av.videorate[mode].value
		if not iAVSwitch.isModeAvailable(port, mode, rate):
			print("[AVSwitch] VideoModeHoyplug: Mode for port '%s', mode '%s', rate '%s' went away." % (port, mode, rate))
			modeList = iAVSwitch.getModeList(port)
			if len(modeList):
				mode = modeList[0][0]
				rate = modeList[0][1]
				# FIXME: The rate needs to be a single value.
				if isinstance(rate, list):
					print("[AVSwitch] ERROR: Rate is a list and needs to be a single value!")
					rate = rate[0]
				print("[AVSwitch] VideoModeHoyplug: Setting mode for port '%s', mode '%s', rate '%s'." % (port, mode, rate))
				iAVSwitch.setMode(port, mode, rate)
			else:
				print("[AVSwitch] VideoModeHoyplug: Sorry, no other mode is available (unplug?). Doing nothing.")


def startHotplug():
	global hotplug
	hotplug = VideomodeHotplug()
	hotplug.start()


def stopHotplug():
	global hotplug
	hotplug.stop()


def InitiVideomodeHotplug(**kwargs):
	startHotplug()


iAVSwitch = AVSwitchBase()  # This should be updated in Screens/InfoBarGenerics.py, Screens/VideoWizard.py and Screens/VideoMode.py.
hotplug = None


# This is a dummy class to stop the constant re-instantiation of the AVSwitchBase class!
#
# NOTE: All code that uses a syntax like AVSwitch().getFramebufferScale() should
# 	be fixed to use avSwitch.getFramebufferScale(), that is use the existing
# 	instantiation of the class rather then creating a new instance!
# 	That is:
# 		from Components.AVSwitch import AVSwitch
# 		...
# 		AVSwitch().getFramebufferScale()
# 	should be changed to:
#		(1, 1)
#
class AVSwitch:
	def setInput(self, input):
		return iAVSwitch.setInput(input)

	def getAspectRatioSetting(self):
		return iAVSwitch.getAspectRatioSetting()

	def setAspectRatio(self, value):
		return iAVSwitch.setAspectRatio(value)

	def getFramebufferScale(self):
		return (1, 1)
