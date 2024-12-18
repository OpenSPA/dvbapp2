from array import array
from binascii import hexlify
from fcntl import ioctl
from glob import glob
from locale import format_string
from os import stat
from os.path import isfile
from re import search
from socket import AF_INET, SOCK_DGRAM, inet_ntoa, socket
from struct import pack, unpack
from platform import libc_ver
from subprocess import PIPE, Popen
from sys import maxsize, modules, version as pyversion
from time import localtime, strftime
####### OPENSPA [morser] Add getmachineBuild #################
from boxbranding import getMachineBuild
#############################################################

from Components.SystemInfo import BoxInfo
from Tools.Directories import fileReadLine, fileReadLines

MODULE_NAME = __name__.split(".")[-1]

socfamily = BoxInfo.getItem("socfamily")
MODEL = BoxInfo.getItem("model")


def _ifinfo(sock, addr, ifname):
	iface = pack('256s', bytes(ifname[:15], 'utf-8'))
	info = ioctl(sock.fileno(), addr, iface)
	if addr == 0x8927:
		return ''.join(['%02x:' % ord(chr(char)) for char in info[18:24]])[:-1].upper()
	else:
		return inet_ntoa(info[20:24])


def getIfConfig(ifname):
	ifreq = {"ifname": ifname}
	infos = {}
	sock = socket(AF_INET, SOCK_DGRAM)
	# Offsets defined in /usr/include/linux/sockios.h on linux 2.6.
	infos["addr"] = 0x8915  # SIOCGIFADDR
	infos["brdaddr"] = 0x8919  # SIOCGIFBRDADDR
	infos["hwaddr"] = 0x8927  # SIOCSIFHWADDR
	infos["netmask"] = 0x891b  # SIOCGIFNETMASK
	try:
		for k, v in infos.items():
			ifreq[k] = _ifinfo(sock, v, ifname)
	except Exception as ex:
		print("[About] getIfConfig Ex: %s" % str(ex))
		pass
	sock.close()
	return ifreq


def getIfTransferredData(ifname):
	lines = fileReadLines("/proc/net/dev", source=MODULE_NAME)
	if lines:
		for line in lines:
			if ifname in line:
				data = line.split("%s:" % ifname)[1].split()
				rx_bytes, tx_bytes = (data[0], data[8])
				return rx_bytes, tx_bytes


def getVersionString():
	return str(BoxInfo.getItem("imageversion"))


def getImageVersionString():
	return str(BoxInfo.getItem("imageversion"))


def getFlashDateString():
	try:
		tm = localtime(stat("/home").st_ctime)
		if tm.tm_year >= 2011:
			return strftime(_("%Y-%m-%d"), tm)
		else:
			return _("Unknown")
	except:
		return _("Unknown")


def getBuildDateString():
	version = fileReadLine("/etc/version", source=MODULE_NAME)
	if version is None:
		return _("Unknown")
	return "%s-%s-%s" % (version[:4], version[4:6], version[6:8])


def getUpdateDateString():
	build = BoxInfo.getItem("compiledate")
	if build and build.isdigit():
		return "%s-%s-%s" % (build[:4], build[4:6], build[6:])
	return _("Unknown")


def getEnigmaVersionString():
	return str(BoxInfo.getItem("imageversion"))


def getGStreamerVersionString():
	from enigma import getGStreamerVersionString
	return getGStreamerVersionString()


def getFFmpegVersionString():
	lines = fileReadLines("/var/lib/opkg/info/ffmpeg.control", source=MODULE_NAME)
	if lines:
		for line in lines:
			if line[0:8] == "Version:":
				return line[9:].split("+")[0]
	return _("Not Installed")


def getKernelVersionString():
	version = fileReadLine("/proc/version", source=MODULE_NAME)
	if version is None:
		return _("Unknown")
	return version.split(" ", 4)[2].split("-", 2)[0]


def getCPUSerial():
	lines = fileReadLines("/proc/cpuinfo", source=MODULE_NAME)
	if lines:
		for line in lines:
			if line[0:6] == "Serial":
				return line[10:26]
	return _("Undefined")


def _getCPUSpeedMhz():
	if MODEL in ('hzero', 'h8', 'sfx6008', 'sfx6018'):
		return 1200
	elif MODEL in ('dreamone', 'dreamtwo', 'dreamseven'):
		return 1800
	elif MODEL in ('vuduo4k',):
		return 2100
	else:
		return 0


def getCPUInfoString():
	cpuCount = 0
	cpuSpeedStr = "-"
	cpuSpeedMhz = _getCPUSpeedMhz()
	processor = ""
	lines = fileReadLines("/proc/cpuinfo", source=MODULE_NAME)
	if lines:
		for line in lines:
			line = [x.strip() for x in line.strip().split(":", 1)]
			if not processor and line[0] in ("system type", "model name", "Processor"):
				processor = line[1].split()[0]
			elif not cpuSpeedMhz and line[0] == "cpu MHz":
				cpuSpeedMhz = float(line[1])
			elif line[0] == "processor":
				cpuCount += 1
		if processor.startswith("ARM") and isfile("/proc/stb/info/chipset"):
			processor = "%s (%s)" % (fileReadLine("/proc/stb/info/chipset", "", source=MODULE_NAME).upper(), processor)
		if not cpuSpeedMhz:
			cpuSpeed = fileReadLine("/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq", source=MODULE_NAME)
			if cpuSpeed:
				cpuSpeedMhz = int(cpuSpeed) / 1000
			else:
				try:
					cpuSpeedMhz = int(int(hexlify(open("/sys/firmware/devicetree/base/cpus/cpu@0/clock-frequency", "rb").read()), 16) / 100000000) * 100
				except:
					cpuSpeedMhz = 1500

		temperature = None
		if isfile("/proc/stb/fp/temp_sensor_avs"):
			temperature = fileReadLine("/proc/stb/fp/temp_sensor_avs", source=MODULE_NAME)
		elif isfile("/proc/stb/power/avs"):
			temperature = fileReadLine("/proc/stb/power/avs", source=MODULE_NAME)
#		elif isfile("/proc/stb/fp/temp_sensor"):
#			temperature = fileReadLine("/proc/stb/fp/temp_sensor", source=MODULE_NAME)
#		elif isfile("/proc/stb/sensors/temp0/value"):
#			temperature = fileReadLine("/proc/stb/sensors/temp0/value", source=MODULE_NAME)
#		elif isfile("/proc/stb/sensors/temp/value"):
#			temperature = fileReadLine("/proc/stb/sensors/temp/value", source=MODULE_NAME)
		elif isfile("/sys/devices/virtual/thermal/thermal_zone0/temp"):
			temperature = fileReadLine("/sys/devices/virtual/thermal/thermal_zone0/temp", source=MODULE_NAME)
			if temperature:
				temperature = int(temperature) / 1000
		elif isfile("/sys/class/thermal/thermal_zone0/temp"):
			temperature = fileReadLine("/sys/class/thermal/thermal_zone0/temp", source=MODULE_NAME)
			if temperature:
				temperature = int(temperature) / 1000
		elif isfile("/proc/hisi/msp/pm_cpu"):
			lines = fileReadLines("/proc/hisi/msp/pm_cpu", source=MODULE_NAME)
			if lines:
				for line in lines:
					if "temperature = " in line:
						temperature = int(line.split("temperature = ")[1].split()[0])

		if cpuSpeedMhz and cpuSpeedMhz >= 1000:
			cpuSpeedStr = _("%s GHz") % format_string("%.1f", cpuSpeedMhz / 1000)
		else:
			cpuSpeedStr = _("%d MHz") % int(cpuSpeedMhz)

		if temperature:
			degree = "\u00B0"
			if not isinstance(degree, str):
				degree = degree.encode("UTF-8", errors="ignore")
			if isinstance(temperature, float):
				temperature = format_string("%.1f", temperature)
			else:
				temperature = str(temperature)
			return (processor, cpuSpeedStr, ngettext("%d core", "%d cores", cpuCount) % cpuCount, "%s%s C" % (temperature, degree))
			#return ("%s %s MHz (%s) %s%sC") % (processor, cpuSpeed, ngettext("%d core", "%d cores", cpuCount) % cpuCount, temperature, degree)
		return (processor, cpuSpeedStr, ngettext("%d core", "%d cores", cpuCount) % cpuCount, "")
		#return ("%s %s MHz (%s)") % (processor, cpuSpeed, ngettext("%d core", "%d cores", cpuCount) % cpuCount)

def getSystemTemperature():
	temperature = ""
	if isfile("/proc/stb/sensors/temp0/value"):
		temperature = fileReadLine("/proc/stb/sensors/temp0/value", source=MODULE_NAME)
	elif isfile("/proc/stb/sensors/temp/value"):
		temperature = fileReadLine("/proc/stb/sensors/temp/value", source=MODULE_NAME)
	elif isfile("/proc/stb/fp/temp_sensor"):
		temperature = fileReadLine("/proc/stb/fp/temp_sensor", source=MODULE_NAME)
	if temperature:
		return "%s%s C" % (temperature, "\u00B0")
	return temperature


def getChipSetString():
	return str(BoxInfo.getItem("ChipsetString"))

def getCPUBrand():
	if BoxInfo.getItem("AmlogicFamily"):
		return _("Amlogic")
	elif BoxInfo.getItem("HiSilicon"):
		return _("HiSilicon")
	elif socfamily.startswith("smp"):
		return _("Sigma Designs")
	elif socfamily.startswith("bcm") or BoxInfo.getItem("brand") == "rpi":
		return _("Broadcom")
	print("[About] No CPU brand?")
	return _("Undefined")


def getCPUArch():
	if BoxInfo.getItem("ArchIsARM64"):
		return _("ARM64")
	elif BoxInfo.getItem("ArchIsARM"):
		return _("ARM")
	return _("Mipsel")


def getFlashType():
	if BoxInfo.getItem("SmallFlash"):
		return _("Small - Tiny image")
	elif BoxInfo.getItem("MiddleFlash"):
		return _("Middle - Lite image")
	return _("Normal - Standard image")


def getDriverInstalledDate():

	def extractDate(value):
		match = search('[0-9]{8}', value)
		if match:
			return match[0]
		else:
			return value

	filenames = glob("/var/lib/opkg/info/*dvb-modules*.control")
	if filenames:
		lines = fileReadLines(filenames[0], source=MODULE_NAME)
		if lines:
			for line in lines:
				if line[0:8] == "Version:":
					return extractDate(line)
	filenames = glob("/var/lib/opkg/info/*dvb-proxy*.control")
	if filenames:
		lines = fileReadLines(filenames[0], source=MODULE_NAME)
		if lines:
			for line in lines:
				if line[0:8] == "Version:":
					return extractDate(line)
	filenames = glob("/var/lib/opkg/info/*platform-util*.control")
	if filenames:
		lines = fileReadLines(filenames[0], source=MODULE_NAME)
		if lines:
			for line in lines:
				if line[0:8] == "Version:":
					return extractDate(line)
	return _("Unknown")

######### OPENSPA [morser] Add missing functions for openspa Plugins ##################################################
def getHardwareTypeString():
	try:
		if os.path.isfile("/proc/stb/info/boxtype"):
			return open("/proc/stb/info/boxtype").read().strip().upper()
		if os.path.isfile("/proc/stb/info/azmodel"):
			return "AZBOX " + open("/proc/stb/info/azmodel").read().strip().upper() + "(" + open("/proc/stb/info/version").read().strip().upper() + ")" 
		if os.path.isfile("/proc/stb/info/vumodel"):
			return "VU+" + open("/proc/stb/info/vumodel").read().strip().upper() + "(" + open("/proc/stb/info/version").read().strip().upper() + ")" 
		if os.path.isfile("/proc/stb/info/model"):
			return open("/proc/stb/info/model").read().strip().upper()
	except:
		pass
	return _("unavailable")

def getIsBroadcom():
	try:
		file = open('/proc/cpuinfo', 'r')
		lines = file.readlines()
		for x in lines:
			splitted = x.split(': ')
			if len(splitted) > 1:
				splitted[1] = splitted[1].replace('\n','')
				if splitted[0].startswith("Hardware"):
					system = splitted[1].split(' ')[0]
				elif splitted[0].startswith("system type"):
					if splitted[1].split(' ')[0].startswith('BCM'):
						system = 'Broadcom'
		file.close()
		if 'Broadcom' in system:
			return True
		else:
			return False
	except:
		return False

def getImageTypeString():
	try:
		return open("/etc/issue").readlines()[-2].capitalize().strip()[:-6]
	except:
		pass
	return _("undefined")

def getCPUSpeedString():
	if getMachineBuild() in ('u41', 'u42', 'u43', 'u45'):
		return (1000, "1,0 GHz")
	elif getMachineBuild() in ('wetekplay', 'hzero', 'h8', 'sfx6008', 'sfx6018',):
		return (1200, "1,2 GHz")
	elif getMachineBuild() in ('dags72604', 'vusolo4k', 'vuultimo4k', 'vuzero4k', 'gb72604', 'vuduo4kse'):
		return (1500, "1,5 GHz")
	elif getMachineBuild() in ('formuler1tc', 'formuler1', 'triplex', 'tiviaraplus'):
		return (1300, "1,3 GHz")
	elif getMachineBuild() in ('dagsmv200', 'gbmv200', 'u51', 'u52', 'u53', 'u532', 'u533', 'u54', 'u55', 'u56', 'u57', 'u571', 'u5', 'u5pvr', 'h9', 'i55se', 'h9se', 'h9combose', 'h9combo', 'h10', 'h11', 'cc1', 'sf8008', 'sf8008m', 'sf8008opt', 'sx988', 'hd60', 'hd61', 'pulse4k', 'pulse4kmini', 'i55plus', 'ustym4kpro', 'ustym4kottpremium', 'beyonwizv2', 'viper4k', 'multibox', 'multiboxse'):
		return (1600, "1,6 GHz")
	elif getMachineBuild() in ('vuuno4kse', 'vuuno4k', 'dm900', 'dm920', 'gb7252', 'dags7252', 'xc7439', '8100s'):
		return (1700, "1,7 GHz")
	elif getMachineBuild() in ('alien5'):
		return (2000, "2,0 GHz")
	elif getMachineBuild() in ('vuduo4k',):
		return (2100, "2,1 GHz")
	elif getMachineBuild() in ('hd51', 'hd52', 'sf4008', 'vs1500', 'et1x000', 'h7', 'et13000', 'sf5008', 'osmio4k', 'osmio4kplus', 'osmini4k'):
		try:
			from binascii import hexlify
			f = open('/sys/firmware/devicetree/base/cpus/cpu@0/clock-frequency', 'rb')
			clockfrequency = f.read()
			f.close()
			CPUSpeed_Int = round(int(hexlify(clockfrequency), 16) / 1000000, 1)
			if CPUSpeed_Int >= 1000:
				return (CPUSpeed_Int, _("%s GHz") % str(round(CPUSpeed_Int / 1000, 1)))
			else:
				return (CPUSpeed_Int, _("%s MHz") % str(round(CPUSpeed_Int, 1)))
		except:
			return (1700, "1,7 GHz")
	else:
		try:
			file = open('/proc/cpuinfo', 'r')
			lines = file.readlines()
			for x in lines:
				splitted = x.split(': ')
				if len(splitted) > 1:
					splitted[1] = splitted[1].replace('\n', '')
					if splitted[0].startswith("cpu MHz"):
						mhz = float(splitted[1].split(' ')[0])
						if mhz and mhz >= 1000:
							mhz = (mhz, _("%s GHz") % str(round(mhz / 1000, 1)))
						else:
							mhz = (mhz, _("%s MHz") % str(round(mhz, 1)))
			file.close()
			return mhz
		except IOError:
			return _("unavailable")

def getCPUString():
	if getMachineBuild() in ('vuduo4k', 'vuduo4kse', 'osmio4k', 'osmio4kplus', 'osmini4k', 'dags72604', 'vuuno4kse', 'vuuno4k', 'vuultimo4k', 'vusolo4k', 'vuzero4k', 'hd51', 'hd52', 'sf4008', 'dm900', 'dm920', 'gb7252', 'gb72604', 'dags7252', 'vs1500', 'et1x000', 'xc7439', 'h7', '8100s', 'et13000', 'sf5008'):
		return "Broadcom"
	elif getMachineBuild() in ('dagsmv200', 'gbmv200', 'u41', 'u42', 'u43', 'u45', 'u51', 'u52', 'u53', 'u532', 'u533', 'u54', 'u55', 'u56', 'u57', 'u571', 'u5', 'u5pvr', 'h9', 'i55se', 'h9se', 'h9combose', 'h9combo', 'h10', 'h11', 'cc1', 'sf8008', 'sf8008m', 'sf8008opt', 'sx988', 'hd60', 'hd61', 'hd66se', 'pulse4k', 'pulse4kmini', 'i55plus', 'ustym4kpro', 'ustym4kottpremium', 'beyonwizv2', 'viper4k', 'multibox', 'multiboxse', 'hzero', 'h8', 'og2ott4k', 'sfx6008'):
		return "Hisilicon"
	elif getMachineBuild() in ('alien5', 'wetekplay', 'wetekplay2'):
		return "AMlogic"
	else:
		try:
			system = "unknown"
			file = open('/proc/cpuinfo', 'r')
			lines = file.readlines()
			for x in lines:
				splitted = x.split(': ')
				if len(splitted) > 1:
					splitted[1] = splitted[1].replace('\n', '')
					if splitted[0].startswith("system type"):
						system = splitted[1].split(' ')[0]
					elif splitted[0].startswith("Processor"):
						system = splitted[1].split(' ')[0]
			file.close()
			return system
		except IOError:
			return _("unavailable")

def getCpuCoresString():
	try:
		file = open('/proc/cpuinfo', 'r')
		lines = file.readlines()
		for x in lines:
			splitted = x.split(': ')
			if len(splitted) > 1:
				splitted[1] = splitted[1].replace('\n', '')
				if splitted[0].startswith("processor"):
					if getMachineBuild() in ('dagsmv200', 'gbmv200', 'u51', 'u52', 'u53', 'u532', 'u533', 'u54', 'u55', 'u56', 'u57', 'u571', 'vuultimo4k', 'u5', 'u5pvr', 'h9', 'i55se', 'h9se', 'h9combose', 'h9combo', 'h10', 'h11', 'alien5', 'cc1', 'sf8008', 'sf8008m', 'sf8008opt', 'sx988', 'hd60', 'hd61', 'hd66se', 'pulse4k', 'pulse4kmini', 'i55plus', 'ustym4kpro', 'ustym4kottpremium', 'beyonwizv2', 'viper4k', 'vuduo4k', 'vuduo4kse', 'multibox', 'multiboxse', 'og2ott4k'):
						cores = 4
					elif getMachineBuild() in ('u41', 'u42', 'u43', 'u45'):
						cores = 1
					elif int(splitted[1]) > 0:
						cores = 2
					else:
						cores = 1
		file.close()
		return cores
	except IOError:
		return _("unavailable")

def getEnigmaDateString():
	process = Popen(["opkg", "info", "enigma2"], stdout=PIPE, stderr=PIPE, universal_newlines=True)
	stdout, stderr = process.communicate()
	if process.returncode == 0:
		for line in stdout.split("\n"):
			if line.startswith("Installed-Time"):
				data = line.split(":")[1]
				if len(data)>0:
					from datetime import datetime
					data = datetime.fromtimestamp(int(data))
					return data.strftime("%Y-%m-%d")
	return _("Unknown")


#########################################################################################################################

def GetIPsFromNetworkInterfaces():
	structSize = 40 if maxsize > 2 ** 32 else 32
	sock = socket(AF_INET, SOCK_DGRAM)
	maxPossible = 8  # Initial value.
	while True:
		_bytes = maxPossible * structSize
		names = array("B")
		for index in range(_bytes):
			names.append(0)
		outbytes = unpack("iL", ioctl(sock.fileno(), 0x8912, pack("iL", _bytes, names.buffer_info()[0])))[0]  # 0x8912 = SIOCGIFCONF
		if outbytes == _bytes:
			maxPossible *= 2
		else:
			break
	ifaces = []
	for index in range(0, outbytes, structSize):
		ifaceName = names.tobytes()[index:index + 16].decode().split("\0", 1)[0]
		if ifaceName != "lo":
			ifaces.append((ifaceName, inet_ntoa(names[index + 20:index + 24])))
	return ifaces


def getBoxUptime():
	upTime = fileReadLine("/proc/uptime", source=MODULE_NAME)
	if upTime is None:
		return "-"
	secs = int(upTime.split(".")[0])
	times = []
	if secs > 86400:
		days = secs // 86400
		secs = secs % 86400
		times.append(ngettext("%d Day", "%d Days", days) % days)
	h = secs // 3600
	m = (secs % 3600) // 60
	times.append(ngettext("%d Hour", "%d Hours", h) % h)
	times.append(ngettext("%d Minute", "%d Minutes", m) % m)
	return " ".join(times)


def getGlibcVersion():
	try:
		return libc_ver()[1]
	except:
		print("[About] Get glibc version failed.")
	return _("Unknown")

def getGccVersion():
	try:
		return pyversion.split("[GCC ")[1].replace("]", "")
	except:
		print("[About] Get gcc version failed.")
	return _("Unknown")

def getPythonVersionString():
	try:
		return pyversion.split(' ')[0]
	except:
		return _("Unknown")

def getopensslVersionString():
	lines = fileReadLines("/var/lib/opkg/info/openssl.control", source=MODULE_NAME)
	if lines:
		for line in lines:
			if line[0:8] == "Version:":
				return line[9:].split("+")[0]
	return _("Not Installed")

# For modules that do "from About import about"
about = modules[__name__]
