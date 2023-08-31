from glob import glob
from hashlib import md5
from os import listdir, readlink
from os.path import exists, isfile, join as pathjoin, islink
from subprocess import PIPE, Popen

from enigma import Misc_Options, eDVBResourceManager, eGetEnigmaDebugLvl, eDBoxLCD, eDVBCIInterfaces

from Tools.Directories import SCOPE_LIBDIR, SCOPE_SKINS, isPluginInstalled, fileCheck, fileReadLine, fileReadLines, resolveFilename, fileExists, fileHas, pathExists
from Tools.MultiBoot import MultiBoot

MODULE_NAME = __name__.split(".")[-1]
SOFTCAM = "/etc/.ActiveCamd"  ## OPENSPA [morser] change for softcam detected
#NOEMU = "/etc/enigma2/noemu"

SystemInfo = {}


class BoxInformation:  # To maintain data integrity class variables should not be accessed from outside of this class!
	def __init__(self):
		self.immutableList = []
		self.boxInfo = {}
		self.enigmaInfoList = []
		self.enigmaConfList = []
		lines = fileReadLines(pathjoin(resolveFilename(SCOPE_LIBDIR), "enigma.info"), source=MODULE_NAME)
		if lines:
			modified = self.checkChecksum(lines)
			if modified:
				print("[SystemInfo] WARNING: Enigma information file checksum is incorrect!  File appears to have been modified.")
				self.boxInfo["checksumerror"] = True
			else:
				print("[SystemInfo] Enigma information file checksum is correct.")
				self.boxInfo["checksumerror"] = False
			for line in lines:
				if line.startswith("#") or line.strip() == "":
					continue
				if "=" in line:
					item, value = [x.strip() for x in line.split("=", 1)]
					if item:
						self.immutableList.append(item)
						self.enigmaInfoList.append(item)
						self.boxInfo[item] = self.processValue(value)
			self.enigmaInfoList = sorted(self.enigmaInfoList)
			print("[SystemInfo] Enigma information file data loaded into BoxInfo.")
		else:
			print("[SystemInfo] ERROR: Enigma information file is not available!  The system is unlikely to boot or operate correctly.")
		lines = fileReadLines(pathjoin(resolveFilename(SCOPE_LIBDIR), "enigma.conf"), source=MODULE_NAME)
		if lines:
			print("[SystemInfo] Enigma config override file available and data loaded into BoxInfo.")
			self.boxInfo["overrideactive"] = True
			for line in lines:
				if line.startswith("#") or line.strip() == "":
					continue
				if "=" in line:
					item, value = [x.strip() for x in line.split("=", 1)]
					if item:
						self.enigmaConfList.append(item)
						if item in self.boxInfo:
							print("[SystemInfo] Note: Enigma information value '%s' with value '%s' being overridden to '%s'." % (item, self.boxInfo[item], value))
						self.boxInfo[item] = self.processValue(value)
			self.enigmaConfList = sorted(self.enigmaConfList)
		else:
			self.boxInfo["overrideactive"] = False

	def checkChecksum(self, lines):
		value = "Undefined!"
		data = []
		for line in lines:
			if line.startswith("checksum"):
				item, value = [x.strip() for x in line.split("=", 1)]
			else:
				data.append(line)
		data.append("")
		result = md5(bytearray("\n".join(data), "UTF-8", errors="ignore")).hexdigest()  # NOSONAR
		return value != result

	def processValue(self, value):
		valueTest = value.upper() if value else ""
		if value is None:
			pass
		elif (value.startswith("\"") or value.startswith("'")) and value.endswith(value[0]):
			value = value[1:-1]
		elif value.startswith("(") and value.endswith(")"):
			data = []
			for item in [x.strip() for x in value[1:-1].split(",")]:
				data.append(self.processValue(item))
			value = tuple(data)
		elif value.startswith("[") and value.endswith("]"):
			data = []
			for item in [x.strip() for x in value[1:-1].split(",")]:
				data.append(self.processValue(item))
			value = list(data)
		elif valueTest == "NONE":
			value = None
		elif valueTest in ("FALSE", "NO", "OFF", "DISABLED"):
			value = False
		elif valueTest in ("TRUE", "YES", "ON", "ENABLED"):
			value = True
		elif value.isdigit() or ((value[0:1] == "-" or value[0:1] == "+") and value[1:].isdigit()):
			value = int(value)
		elif valueTest.startswith("0X"):
			try:
				value = int(value, 16)
			except ValueError:
				pass
		elif valueTest.startswith("0O"):
			try:
				value = int(value, 8)
			except ValueError:
				pass
		elif valueTest.startswith("0B"):
			try:
				value = int(value, 2)
			except ValueError:
				pass
		else:
			try:
				value = float(value)
			except ValueError:
				pass
		return value

	def getEnigmaInfoList(self):
		return self.enigmaInfoList

	def getEnigmaConfList(self):
		return self.enigmaConfList

	def getItemsList(self):
		return sorted(list(self.boxInfo.keys()))

	def getItem(self, item, default=None):
		if item in self.boxInfo:
			value = self.boxInfo[item]
		elif item in SystemInfo:
			value = SystemInfo[item]
		else:
			value = default
		return value

	def setItem(self, item, value, immutable=False):
		if item in self.immutableList:
			print("[BoxInfo] Error: Item '%s' is immutable and can not be %s!" % (item, "changed" if item in self.boxInfo else "added"))
			return False
		if immutable:
			self.immutableList.append(item)
		self.boxInfo[item] = value
		SystemInfo[item] = value
		return True

	def deleteItem(self, item):
		if item in self.immutableList:
			print("[BoxInfo] Error: Item '%s' is immutable and can not be deleted!" % item)
		elif item in self.boxInfo:
			del self.boxInfo[item]
			return True
		return False


BoxInfo = BoxInformation()

ARCHITECTURE = BoxInfo.getItem("architecture")
BRAND = BoxInfo.getItem("brand")
MODEL = BoxInfo.getItem("model")
SOC_FAMILY = BoxInfo.getItem("socfamily")
DISPLAYTYPE = BoxInfo.getItem("displaytype")
MTDROOTFS = BoxInfo.getItem("mtdrootfs")
DISPLAYMODEL = BoxInfo.getItem("displaymodel")
DISPLAYBRAND = BoxInfo.getItem("displaybrand")
MACHINEBUILD = BoxInfo.getItem("machinebuild")


def getBoxDisplayName():  # This function returns a tuple like ("BRANDNAME", "BOXNAME")
	return (DISPLAYBRAND, DISPLAYMODEL)


# Parse the boot commandline.
# cmdline = fileReadLine("/proc/cmdline", source=MODULE_NAME)
# cmdline = {k: v.strip('"') for k, v in findall(r'(\S+)=(".*?"|\S+)', cmdline)}

def getDemodVersion():
	version = None
	if exists("/proc/stb/info/nim_firmware_version"):
		version = fileReadLine("/proc/stb/info/nim_firmware_version")
	return version and version.strip()


def getNumVideoDecoders():
	numVideoDecoders = 0
	while fileExists("/dev/dvb/adapter0/video%d" % numVideoDecoders, "f"):
		numVideoDecoders += 1
	return numVideoDecoders


def countFrontpanelLEDs():
	numLeds = fileExists("/proc/stb/fp/led_set_pattern") and 1 or 0
	while fileExists("/proc/stb/fp/led%d_pattern" % numLeds):
		numLeds += 1
	return numLeds


#def haveInitCam():
#	for cam in listdir("/etc/init.d"):
#		if cam.startswith("softcam.") and not cam.endswith("None"):
#			return True
#		elif cam.startswith("cardserver.") and not cam.endswith("None"):
#			return True
#	return False


def getRCFile(ext):
	filename = resolveFilename(SCOPE_SKINS, pathjoin("hardware", "%s.%s" % (BoxInfo.getItem("rcname"), ext)))
	if not isfile(filename):
		filename = resolveFilename(SCOPE_SKINS, pathjoin("hardware", "dmm1.%s" % ext))
	return filename

def getChipsetString():
	if MODEL in ("dm7080", "dm820"):
		return "7435"
	elif MODEL in ("dm520", "dm525"):
		return "73625"
	elif MODEL in ("dm900", "dm920", "et13000"):
		return "7252S"
	elif MODEL in ("hd51", "vs1500", "h7"):
		return "7251S"
	elif MODEL in ('dreamone', 'dreamonetwo', 'dreamseven'):
		return "S922X"
	chipset = fileReadLine("/proc/stb/info/chipset", default=_("Undefined"), source=MODULE_NAME)
	return str(chipset.lower().replace("\n", "").replace("bcm", "").replace("brcm", "").replace("sti", ""))


def getModuleLayout():
	modulePath = BoxInfo.getItem("enigmamodule")
	if modulePath:
		process = Popen(("/sbin/modprobe", "--dump-modversions", modulePath), stdout=PIPE, stderr=PIPE, universal_newlines=True)
		stdout, stderr = process.communicate()
		if process.returncode == 0:
			for detail in stdout.split("\n"):
				if "module_layout" in detail:
					return detail.split("\t")[0]
	return None

# OPENSPA [morser] change for openspa softcam detected
#def hasSoftcamEmu():
#	if isfile(NOEMU):
#		return False
#	else:
#		return len(glob("/etc/*.emu")) > 0


#def hasSoftcam():
#	if not isfile(NOEMU):
#		for cam in listdir("/etc/init.d"):
#			if (cam.startswith('softcam.') or cam.startswith('cardserver.')) and not cam.endswith('None'):
#				return True
#	return False


def getSysSoftcam():
	if isfile(SOFTCAM):
		cams = open(SOFTCAM).read()
		return cams.lower()
	return ""

def updateSysSoftCam():
	BoxInfo.setItem("ShowOscamInfo", "oscam" in getSysSoftcam(), False)
	BoxInfo.setItem("ShowCCCamInfo", "ccam" in getSysSoftcam(), False)
	BoxInfo.setItem("ShowNCamInfo", "ncam" in getSysSoftcam(), False)
#	BoxInfo.setItem("HasSoftcamEmu", hasSoftcamEmu(), False)
######################################################


def getBoxName():
	box = MACHINEBUILD
	machinename = DISPLAYMODEL.lower()
	if box in ('uniboxhd1', 'uniboxhd2', 'uniboxhd3'):
		box = "ventonhdx"
	elif box == "odinm6":
		box = machinename
	elif box == "inihde" and machinename == "hd-1000":
		box = "sezam-1000hd"
	elif box == "ventonhdx" and machinename == "hd-5000":
		box = "sezam-5000hd"
	elif box == "ventonhdx" and machinename == "premium twin":
		box = "miraclebox-twin"
	elif box == "xp1000" and machinename == "sf8 hd":
		box = "sf8"
	elif box.startswith('et') and box not in ('et8000', 'et8500', 'et8500s', 'et10000'):
		box = box[0:3] + 'x00'
	elif box == "odinm9":
		box = "maram9"
	elif box.startswith('sf8008m'):
		box = "sf8008m"
	elif box.startswith('sf8008'):
		box = "sf8008"
	elif box.startswith('ustym4kpro'):
		box = "ustym4kpro"
	elif box.startswith('twinboxlcdci'):
		box = "twinboxlcd"
	elif box == "sfx6018":
		box = "sfx6008"
	elif box == "sx888":
		box = "sx88v2"
	return box


def getWakeOnLANType(fileName):
	value = ""
	if fileName:
		value = fileReadLine(fileName)
	onOff = ("off", "on")
	return onOff if value in onOff else ("disable", "enable")


BoxInfo.setItem("DebugLevel", eGetEnigmaDebugLvl())
BoxInfo.setItem("InDebugMode", eGetEnigmaDebugLvl() >= 4)
BoxInfo.setItem("ModuleLayout", getModuleLayout(), immutable=True)

BoxInfo.setItem("RCImage", getRCFile("png"))
BoxInfo.setItem("RCMapping", getRCFile("xml"))
BoxInfo.setItem("RemoteEnable", MACHINEBUILD in ("dm800",))
if MACHINEBUILD in ('maram9', 'classm', 'axodin', 'axodinc', 'starsatlx', 'genius', 'evo', 'galaxym6'):
	repeat = 400
else:
	repeat = 100
BoxInfo.setItem("RemoteRepeat", repeat)
BoxInfo.setItem("RemoteDelay", 200 if repeat == 400 else 700)

BoxInfo.setItem("HDMI-PreEmphasis", fileExists("/proc/stb/hdmi/preemphasis"))

try:
	branch = getE2Rev()
	if "+" in branch:
		branch = branch.split("+")[1]
	branch = "?sha=%s" % branch
except Exception as err:
	branch = ""
commitLogs = [
	("OpenSPA Enigma2", "https://github.com/OpenSPA/dvbapp2/commits%s" % branch),
	("OE-Alliance Plugins", "https://api.github.com/repos/oe-alliance/oe-alliance-plugins/commits"),
	("Enigma2 Plugins", "https://api.github.com/repos/oe-alliance/enigma2-plugins/commits"),
	("OpenWebif", "https://api.github.com/repos/E2OpenPlugins/e2openplugin-OpenWebif/commits")
]
BoxInfo.setItem("InformationCommitLogs", commitLogs)
# NOTE: Return the welcome text back to Information.py until SystemInfo can process translation requests.
#
# welcome = [
# 	_("Welcome to %s") % BoxInfo.getItem("displaydistro", "Enigma2")
# ]
# BoxInfo.setItem("InformationDistributionWelcome", welcome)

BoxInfo.setItem("12V_Output", Misc_Options.getInstance().detected_12V_output())  #FIXME : Do we need this?
BoxInfo.setItem("3DMode", fileCheck("/proc/stb/fb/3dmode") or fileCheck("/proc/stb/fb/primary/3d"))
BoxInfo.setItem("3DZNorm", fileCheck("/proc/stb/fb/znorm") or fileCheck("/proc/stb/fb/primary/zoffset"))
BoxInfo.setItem("7segment", DISPLAYTYPE in ("7segment",))
BoxInfo.setItem("AmlogicFamily", SOC_FAMILY.startswith(("aml", "meson")) or exists("/proc/device-tree/amlogic-dt-id") or exists("/usr/bin/amlhalt") or exists("/sys/module/amports"))
BoxInfo.setItem("ArchIsARM64", ARCHITECTURE == "aarch64" or "64" in ARCHITECTURE)
BoxInfo.setItem("ArchIsARM", ARCHITECTURE.startswith(("arm", "cortex")))
BoxInfo.setItem("Blindscan", isPluginInstalled("Blindscan"))
BoxInfo.setItem("BoxName", getBoxName())
BoxInfo.setItem("CanMeasureFrontendInputPower", eDVBResourceManager.getInstance().canMeasureFrontendInputPower())
BoxInfo.setItem("canMultiBoot", MultiBoot.getBootSlots())
BoxInfo.setItem("HasKexecMultiboot", fileHas("/proc/cmdline", "kexec=1"))
BoxInfo.setItem("cankexec", BoxInfo.getItem("kexecmb") and (fileExists("/usr/bin/kernel_auto.bin") and fileExists("/usr/bin/STARTUP.cpio.gz") and not BoxInfo.getItem("HasKexecMultiboot")) or (fileExists("/STARTUP.cpio.gz") and fileExists("/usr/bin/kernel_auto.bin") and fileExists("/STARTUP")))
BoxInfo.setItem("CanNotDoSimultaneousTranscodeAndPIP", MODEL in ("vusolo4k", "gbquad4k", "gbue4k"))
BoxInfo.setItem("canRecovery", MODEL in ("hd51", "vs1500", "h7", "8100s") and ("disk.img", "mmcblk0p1") or MODEL in ("xc7439", "osmio4k", "osmio4kplus", "osmini4k") and ("emmc.img", "mmcblk1p1") or MODEL in ("gbmv200", "sf8008", "sf8008m", "sx988", "ip8", "ustym4kpro", "ustym4kottpremium", "ustym4ks2ottx", "beyonwizv2", "viper4k", "og2ott4k", "og2s4k", "sx88v2", "sx888") and ("usb_update.bin", "none"))
BoxInfo.setItem("CanUse3DModeChoices", fileExists("/proc/stb/fb/3dmode_choices") and True or False)
BoxInfo.setItem("ChipsetString", getChipsetString(), immutable=True)
BoxInfo.setItem("CIHelper", fileExists("/usr/bin/cihelper"))
BoxInfo.setItem("DeepstandbySupport", MODEL != 'dm800')
BoxInfo.setItem("DefaultDisplayBrightness", MACHINEBUILD in ("dm900", "dm920") and 8 or 5)
BoxInfo.setItem("FBLCDDisplay", fileCheck("/proc/stb/fb/sd_detach"))
BoxInfo.setItem("Fan", fileCheck("/proc/stb/fp/fan"))
BoxInfo.setItem("FanPWM", BoxInfo.getItem("Fan") and fileCheck("/proc/stb/fp/fan_pwm"))
BoxInfo.setItem("ForceLNBPowerChanged", fileCheck("/proc/stb/frontend/fbc/force_lnbon"))
BoxInfo.setItem("ForceToneBurstChanged", fileCheck("/proc/stb/frontend/fbc/force_toneburst"))
BoxInfo.setItem("FrontpanelDisplay", fileExists("/dev/dbox/oled0") or fileExists("/dev/dbox/lcd0"))
BoxInfo.setItem("GBWOL", fileExists("/usr/bin/gigablue_wol"))
BoxInfo.setItem("grautec", fileExists("/tmp/usbtft"))
BoxInfo.setItem("GraphicLCD", MACHINEBUILD in ("vuultimo", "xpeedlx3", "et10000", "mutant2400", "quadbox2400", "sezammarvel", "atemionemesis", "mbultra", "beyonwizt4", "osmio4kplus"))
BoxInfo.setItem("HasExternalPIP", MODEL not in ("et9x00", "et6x00", "et5x00") and fileCheck("/proc/stb/vmpeg/1/external"))
BoxInfo.setItem("HasFullHDSkinSupport", MACHINEBUILD not in ("et4000", "et5000", "sh1", "hd500c", "hd1100", "xp1000", "lc", "iziboxecohd", "jdhdduo"))
BoxInfo.setItem("HasHiSi", pathExists("/proc/hisi"))
BoxInfo.setItem("hasPIPVisibleProc", fileCheck("/proc/stb/vmpeg/1/visible"))
BoxInfo.setItem("HasMMC", fileHas("/proc/cmdline", "root=/dev/mmcblk") or MultiBoot.canMultiBoot() and fileHas("/proc/cmdline", "root=/dev/sda"))
BoxInfo.setItem("HasSDmmc", MultiBoot.canMultiBoot() and "sd" in MultiBoot.getBootSlots()["2"] and "mmcblk" in MTDROOTFS)
BoxInfo.setItem("HasSDswap", MODEL in ("h9", "i55plus") and pathExists("/dev/mmcblk0p1"))
BoxInfo.setItem("HaveCISSL", fileCheck("/etc/ssl/certs/customer.pem") and fileCheck("/etc/ssl/certs/device.pem"))
BoxInfo.setItem("HAVEEDIDDECODE", fileCheck("/proc/stb/hdmi/raw_edid") and fileCheck("/usr/bin/edid-decode"))
BoxInfo.setItem("HaveID", fileCheck("/etc/.id"))
#BoxInfo.setItem("HAVEINITCAM", haveInitCam())
BoxInfo.setItem("HaveTouchSensor", MACHINEBUILD in ("dm520", "dm525", "dm900", "dm920"))
BoxInfo.setItem("HDMICEC", fileExists("/dev/hdmi_cec") or fileExists("/dev/misc/hdmi_cec0"))
BoxInfo.setItem("HDMIin", BoxInfo.getItem("hdmifhdin") or BoxInfo.getItem("hdmihdin"))
BoxInfo.setItem("HDMIinPiP", BoxInfo.getItem("HDMIin") and BRAND != "dreambox")
BoxInfo.setItem("HiSilicon", SOC_FAMILY.startswith("hisi") or exists("/proc/hisi") or exists("/usr/bin/hihalt") or exists("/usr/lib/hisilicon"))
BoxInfo.setItem("VuplusVFD", MODEL in ('vuduo2', ))
BoxInfo.setItem("LcdDisplay", fileExists("/dev/dbox/lcd0"))
BoxInfo.setItem("LcdLiveTV", fileCheck("/proc/stb/fb/sd_detach") or fileCheck("/proc/stb/lcd/live_enable"))
BoxInfo.setItem("LcdLiveTVPiP", fileCheck("/proc/stb/lcd/live_decoder"))
BoxInfo.setItem("LCDMiniTV", fileExists("/proc/stb/lcd/mode"))
BoxInfo.setItem("LCDMiniTVPiP", BoxInfo.getItem("LCDMiniTV") and MACHINEBUILD not in ("gb800ueplus", "gbquad4k", "gbue4k"))
BoxInfo.setItem("LCDSKINSetup", fileExists("/usr/share/enigma2/display") and not fileExists("/usr/lib/enigma2/python/Plugins/Extensions/LCD4linux/plugin.py") or BoxInfo.getItem("VuplusVFD"))
BoxInfo.setItem("LCDClockSetup",fileExists("/usr/share/enigma2/display") and DISPLAYTYPE not in ('textlcd','7segment') and not fileExists("/usr/lib/enigma2/python/Plugins/Extensions/LCD4linux/plugin.py"))
BoxInfo.setItem("LEDButtons", MACHINEBUILD == "vuultimo")
BoxInfo.setItem("LEDColorControl", fileExists("/proc/stb/fp/led_color"))
BoxInfo.setItem("LEDPowerColor", fileExists("/proc/stb/fp/ledpowercolor"))
BoxInfo.setItem("LEDStandbyColor", fileExists("/proc/stb/fp/ledstandbycolor"))
BoxInfo.setItem("LEDSuspendColor", fileExists("/proc/stb/fp/ledsuspendledcolor"))
BoxInfo.setItem("MiddleFlash", BoxInfo.getItem("middleflash") and not BoxInfo.getItem("smallflash"))
BoxInfo.setItem("MiniTV", fileCheck("/proc/stb/fb/sd_detach") or fileCheck("/proc/stb/lcd/live_enable"))
BoxInfo.setItem("need_dsw", MACHINEBUILD not in ("osminiplus", "osmega"))
BoxInfo.setItem("NumFrontpanelLEDs", countFrontpanelLEDs())
BoxInfo.setItem("NumVideoDecoders", getNumVideoDecoders())
BoxInfo.setItem("OledDisplay", fileExists("/dev/dbox/oled0") or MACHINEBUILD in ("osminiplus",))
BoxInfo.setItem("PIPAvailable", BoxInfo.getItem("NumVideoDecoders", 1) > 1)
BoxInfo.setItem("Power4x7On", fileExists("/proc/stb/fp/power4x7on"))
BoxInfo.setItem("Power4x7Standby", fileExists("/proc/stb/fp/power4x7standby"))
BoxInfo.setItem("Power4x7Suspend", fileExists("/proc/stb/fp/power4x7suspend"))
BoxInfo.setItem("PowerLed", fileExists("/proc/stb/power/powerled"))
BoxInfo.setItem("PowerLed2", fileExists("/proc/stb/power/powerled2"))
BoxInfo.setItem("RecoveryMode", fileCheck("/proc/stb/fp/boot_mode") or MODEL in ("dreamone", "dreamtwo"))
BoxInfo.setItem("Satfinder", isPluginInstalled("Satfinder"))
BoxInfo.setItem("SmallFlash", BoxInfo.getItem("smallflash"))
#BoxInfo.setItem("SoftCam", hasSoftcam())
BoxInfo.setItem("StandbyPowerLed", fileExists("/proc/stb/power/standbyled"))
BoxInfo.setItem("STi", SOC_FAMILY.startswith("sti"))
BoxInfo.setItem("SuspendPowerLed", fileExists("/proc/stb/power/suspendled"))
BoxInfo.setItem("USETunersetup", BoxInfo.getItem("ForceLNBPowerChanged") or BoxInfo.getItem("ForceToneBurstChanged"))
BoxInfo.setItem("VFD_scroll_repeats", eDBoxLCD.getInstance().get_VFD_scroll_repeats())
BoxInfo.setItem("VFD_scroll_delay", eDBoxLCD.getInstance().get_VFD_scroll_delay())
BoxInfo.setItem("VFD_initial_scroll_delay", eDBoxLCD.getInstance().get_VFD_initial_scroll_delay())
BoxInfo.setItem("VFD_final_scroll_delay", eDBoxLCD.getInstance().get_VFD_final_scroll_delay())
BoxInfo.setItem("VideoDestinationConfigurable", fileExists("/proc/stb/vmpeg/0/dst_left"))
BoxInfo.setItem("WakeOnLAN", fileCheck("/proc/stb/power/wol") or fileCheck("/proc/stb/fp/wol"))
BoxInfo.setItem("WakeOnLANType", getWakeOnLANType(BoxInfo.getItem("WakeOnLAN")))
BoxInfo.setItem("XcoreVFD", MODEL in ("xc7346", "xc7439"))
BoxInfo.setItem("ZapMode", fileCheck("/proc/stb/video/zapmode") or fileCheck("/proc/stb/video/zapping_mode"))

BoxInfo.setItem("VFDSymbolsPoll1", MACHINEBUILD in ('osninopro', 'osnino', 'osninoplus', 'tmtwin4k', 'mbmicrov2', 'revo4k', 'force3uhd', 'mbmicro', 'e4hd', 'e4hdhybrid', 'dm7020hd', 'dm7020hdv2', '9910lx', '9911lx', '9920lx', 'dual') or MODEL in ('dags7362', 'dags73625', 'dags5', 'ustym4kpro', 'ustym4ks2ottx', 'beyonwizv2', 'viper4k', 'sf8008', 'sf8008m', 'gbmv200', 'sfx6008', 'sx88v2', 'sx888'))
BoxInfo.setItem("VFDSymbols", BoxInfo.getItem("VFDSymbolsPoll1") or MODEL in ("u41",) or BRAND in ("fulan",) or MACHINEBUILD in ("alphatriple", "spycat4kmini", "osminiplus", "osmega", "sf3038", "spycat", "et7500", "maram9", "uniboxhd1", "uniboxhd2", "uniboxhd3", "sezam5000hd", "mbtwin", "sezam1000hd", "mbmini", "atemio5x00", "beyonwizt3"))

BoxInfo.setItem("DisplaySetup", MODEL not in ("dreamone",))

# dont't sort
BoxInfo.setItem("ConfigDisplay", BoxInfo.getItem("FrontpanelDisplay") and DISPLAYTYPE not in ("7segment",))
BoxInfo.setItem("dFlash", exists("/usr/lib/enigma2/python/Plugins/Extensions/dFlash"))
BoxInfo.setItem("dBackup", not BoxInfo.getItem("dFlash") and exists("/usr/lib/enigma2/python/Plugins/Extensions/dBackup"))
BoxInfo.setItem("ImageBackup", not BoxInfo.getItem("dFlash") and not BoxInfo.getItem("dBackup"))

SystemInfo["SeekStatePlay"] = False
SystemInfo["StatePlayPause"] = False
SystemInfo["StandbyState"] = False
SystemInfo["FastChannelChange"] = False
SystemInfo["FCCactive"] = False

SystemInfo["CommonInterface"] = eDVBCIInterfaces.getInstance().getNumOfSlots()
SystemInfo["CommonInterfaceCIDelay"] = fileCheck("/proc/stb/tsmux/rmx_delay")
for cislot in range(0, SystemInfo["CommonInterface"]):
	SystemInfo["CI%dSupportsHighBitrates" % cislot] = fileCheck("/proc/stb/tsmux/ci%d_tsclk" % cislot)
	SystemInfo["CI%dRelevantPidsRoutingSupport" % cislot] = fileCheck("/proc/stb/tsmux/ci%d_relevant_pids_routing" % cislot)

updateSysSoftCam()
