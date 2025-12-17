import threading
from os import listdir, mkdir, remove, walk
from os.path import basename, dirname, exists, join
from re import match
from shutil import move, rmtree
from tempfile import mkdtemp
from json import loads
from enigma import eDVBDB, eEPGCache
from Screens.MessageBox import MessageBox
from Components.config import config
from Tools.Notifications import AddNotificationWithID
from urllib.error import URLError, HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen
from xml.etree.ElementTree import fromstring
from base64 import encodebytes
from time import sleep

supportfiles = ('lamedb', 'blacklist', 'whitelist', 'alternatives.', 'iptosat')
channelslistpath = "/etc/enigma2"
login = True


class ImportChannels():
	DIR_ENIGMA2 = "/etc/enigma2/"
	DIR_HDD = "/media/hdd/"
	DIR_USB = "/media/usb/"
	DIR_TMP = "/tmp/"

	def __init__(self):
		self.remoteEPGpath = None
		if config.usage.remote_fallback_enabled.value and config.usage.remote_fallback_import.value and config.usage.remote_fallback.value and "ChannelsImport" not in [x.name for x in threading.enumerate()]:
			self.header = None
			if config.usage.remote_fallback_enabled.value and config.usage.remote_fallback_import.value and config.usage.remote_fallback_import_url.value != "same" and config.usage.remote_fallback_import_url.value:
				self.url = config.usage.remote_fallback_import_url.value.rsplit(":", 1)[0]
			else:
				self.url = config.usage.remote_fallback.value.rsplit(":", 1)[0] if "@" not in config.usage.remote_fallback.value and "root" not in config.usage.remote_fallback.value else config.usage.remote_fallback.value.split("root")[0] + config.usage.remote_fallback.value.split("@")[1].split(":")[0]
			if config.usage.remote_fallback_openwebif_customize.value:
				self.url = f"{self.url}:{config.usage.remote_fallback_openwebif_port.value}"
				if config.usage.remote_fallback_openwebif_userid.value and config.usage.remote_fallback_openwebif_password.value:
					self.header = "Basic " + str(encodebytes((f"{config.usage.remote_fallback_openwebif_userid.value}:{config.usage.remote_fallback_openwebif_password.value}").encode("UTF-8"))).strip()
			self.remote_fallback_import = config.usage.remote_fallback_import.value
			self.thread = threading.Thread(target=self.threaded_function, name="ChannelsImport")
			self.thread.start()

	def getUrl(self, url, timeout=5):
		request = Request(url)
		if self.header:
			request.add_header("Authorization", self.header)
		try:
			result = urlopen(request, timeout=timeout)
		except URLError as err:
			if "[Errno -3]" in str(err):
				print("[ImportChannels] Network is not up yet, delay 5 seconds")
				# network not up yet
				sleep(5)
				return self.getUrl(url, timeout)
			print("[ImportChannels]", err)
			result = {}
		return result

	def getFallbackSettings(self):
		try:
			return self.getUrl(self.url + "/api/settings")
		except HTTPError as err:
			self.ImportChannelsNotDone(True, f"{err}")
			return

	def getFallbackSettingsValue(self, settings, e2settingname):
		if isinstance(settings, bytes):
			root = fromstring(settings)
			for e2setting in root:
				if e2settingname in e2setting[0].text:
					return e2setting[1].text
			return ""

	def getTerrestrialRegion(self, settings):
		if settings:
			description = ""
			descr = self.getFallbackSettingsValue(settings, ".terrestrial")
			if descr and "Europe" in descr:
				description = "fallback DVB-T/T2 Europe"
			if descr and "Australia" in descr:
				description = "fallback DVB-T/T2 Australia"
			config.usage.remote_fallback_dvbt_region.value = description

	def getRemoteAddress(self):
		self.url = config.usage.remote_fallback.value.rsplit(":", 1)[0] if "@" not in config.usage.remote_fallback.value and "root" not in config.usage.remote_fallback.value else config.usage.remote_fallback.value.split("root")[0] + config.usage.remote_fallback.value.split("@")[1].split(":")[0]
		return self.url.replace("http://", "")

	def downloadEPG(self):
		global login
		print("[ImportChannels] downloadEPG Force EPG save on remote receiver...")
		self.forceSaveEPGonRemoteReceiver()
		print("[ImportChannels] downloadEPG Searching for epg.dat...")
		result = self.FTPdownloadFile(self.DIR_ENIGMA2, "settings", "settings")
		if result:
			self.checkEPGCallback()
		else:
			if login:
				if not exists(self.DIR_ENIGMA2 + "epg.dat") and not exists(self.DIR_HDD + "epg.dat") and not exists(self.DIR_USB + "epg.dat"):
					self.ImportChannelsNotDone(True, _("1. Tune to an imported channel with at least EPG EIT.\n2. Restart enigma2.\n3. Now try to download EPG cache from the reserve receiver."))
				else:
					self.ImportChannelsNotDone(True, _("Change the cache directory to Internal Flash in EPG Settings on both receivers."))

	def forceSaveEPGonRemoteReceiver(self):
		url = f"{self.url}/api/saveepg"
		print(f"[ImportChannels] saveEPGonRemoteReceiver URL: {self.url}")
		try:
			req = Request(url)
			response = urlopen(req)
			print("[ImportChannels] saveEPGonRemoteReceiver Response:" + response.getcode(), response.read().strip().replace("\r", "").replace("\n", ""))
		except HTTPError as err:
			print(f"[ImportChannels] saveEPGonRemoteReceiver ERROR: {err}")
		except URLError as err:
			print(f"[ImportChannels] saveEPGonRemoteReceiver ERROR: {err}")
		except Exception:
			print('[ImportChannels] saveEPGonRemoteReceiver undefined error')

	def FTPdownloadFile(self, sourcefolder, sourcefile, destfile):
		global login
		print(f"[ImportChannels] Downloading remote file {sourcefile}")
		try:
			from ftplib import FTP
			ftp = FTP()
			ftp.set_pasv(True)
			ftp.connect(host=self.getRemoteAddress(), port=21, timeout=5)
			ftp.login(user="root", passwd=str(config.usage.remote_fallback_openwebif_password.value))
			ftp.cwd(sourcefolder)
			with open(self.DIR_TMP + destfile, 'wb') as f:
				result = ftp.retrbinary(f"RETR {sourcefile}", f.write)
				ftp.quit()
				if result.startswith("226"):
					return True
			return False
		except Exception as err:
			print("[ImportChannels] FTPdownloadFile Error:", err)
			if "Login incorrect" in str(err):
				self.ImportChannelsNotDone(True, _("Incorrect password: Change the password in the OpenWebIF setting in the reserve tuner settings.\nYou must enter the password of the reserve receiver."))
				login = False
			return False

	def removeFiles(self, targetdir, target):
		targetLen = len(target)
		for root, dirs, files in walk(targetdir):
			for name in files:
				if target in name[:targetLen]:
					remove(join(root, name))

	def checkEPGCallback(self):
		self.remoteEPGfile = "epg"
		self.remoteEPGfile = f"{self.remoteEPGfile.replace('.dat', '')}.dat"
		try:
			self.remoteEPGpath = self.DIR_ENIGMA2
			print(f"[ImportChannels] Remote EPG filename. {self.remoteEPGpath}{self.remoteEPGfile}")
			result = self.FTPdownloadFile(self.remoteEPGpath, self.remoteEPGfile, "epg.dat")
			if result:
				self.importEPGCallback()
			else:
				print("[ImportChannels] Remote EPG filename not path in internal flash")
		except Exception as err:
			print(f"[ImportChannels] cannot save EPG {err}")
		try:
			self.remoteEPGpath = self.DIR_HDD
			print(f"[ImportChannels] Remote EPG filename. {self.remoteEPGpath}{self.remoteEPGfile}")
			result = self.FTPdownloadFile(self.remoteEPGpath, self.remoteEPGfile, "epg.dat")
			if result:
				self.importEPGCallback()
			else:
				print("[ImportChannels] Remote EPG filename not path in HDD")
		except Exception as err:
			print(f"[ImportChannels] cannot save EPG {err}")
		try:
			self.remoteEPGpath = self.DIR_USB
			print(f"[ImportChannels] Remote EPG filename. {self.remoteEPGpath}{self.remoteEPGfile}")
			result = self.FTPdownloadFile(self.remoteEPGpath, self.remoteEPGfile, "epg.dat")
			if result:
				self.importEPGCallback()
			else:
				print("[ImportChannels] Remote EPG filename not path in USB")
		except Exception as err:
			print(f"[ImportChannels] cannot save EPG {err}")

	def importEPGCallback(self):
		print(f"[ImportChannels] importEPGCallback {self.remoteEPGpath}{self.remoteEPGfile} downloaded successfully from server.")
		print("[ImportChannels] importEPGCallback Removing current EPG data...")
		try:
			remove(config.misc.epgcache_filename.value)
		except OSError:
			pass
		if self.remoteEPGpath == self.DIR_HDD:
			config.misc.epgcachepath.value = self.DIR_HDD
		elif self.remoteEPGpath == self.DIR_USB:
			config.misc.epgcachepath.value = self.DIR_USB
		elif self.remoteEPGpath == self.DIR_ENIGMA2:
			config.misc.epgcachepath.value = self.DIR_ENIGMA2
		config.misc.epgcachepath.save()
		move(self.DIR_TMP + "epg.dat", config.misc.epgcache_filename.value)
		self.removeFiles(self.DIR_TMP, "epg.dat")
		eEPGCache.getInstance().load()
		print("[ImportChannels] importEPGCallback New EPG data loaded...")
		print("[ImportChannels] importEPGCallback Closing importer.")
		self.ImportChannelsDone(True, _("EPG imported successfully from") + f" {self.url}")

	def threaded_function(self):
		settings = self.getFallbackSettings()
		self.getTerrestrialRegion(settings)
		self.tmp_dir = mkdtemp(prefix="ImportChannels_")
		if "epg" in config.usage.remote_fallback_import.value:
			if config.usage.remote_fallback_import_restart.value or config.usage.remote_fallback_import_standby.value:
				print("[ImportChannels] Starting to load epg.dat files and channels from server box")
				if "channels_epg" in self.remote_fallback_import:
					self.importChannelsCallback()
				try:
					urlopen(self.url + "/api/saveepg")
				except Exception as err:
					print(f"[ImportChannels] {err}")
					self.ImportChannelsNotDone(True, _("Access not available:\nCheck HTTP authentication not is active in OpenWebIF on the receiver fallback or check data entered in settings."))
					return
				print("[ImportChannels] Get EPG Location")
				try:
					searchPaths = ["/etc/enigma2", "/media/hdd"]
					for epg in searchPaths:
						epgdatfile = join(epg, "epg.dat")
						files = [file for file in loads(urlopen(f"{self.url}/file?dir={dirname(epgdatfile)}", timeout=5).read())["files"] if basename(file).startswith("epg.dat")]
						if not files:
							epgdatfile = join("/media/usb/", "epg.dat")
							files = [file for file in loads(urlopen(f"{self.url}/file?dir={dirname(epgdatfile)}", timeout=5).read())["files"] if basename(file).startswith("epg.dat")]
						epg_location = files[0] if files else None
						if epg_location:
							print("[ImportChannels] EPG imported successfully: Copy EPG file...")
							try:
								try:
									mkdir("/tmp/epgdat")
								except Exception:
									print("[ImportChannels] epgdat folder exists in tmp")
								epgdattmp = "/tmp/epgdat"
								epgdatserver = "/tmp/epgdat/epg.dat"
								open(f"{epgdattmp}/{basename(epg_location)}", "wb").write(urlopen(f"{self.url}/file?file={epg_location}", timeout=5).read())
								if "epg.dat" in epgdatserver:
									move(f"{epgdatserver}", f"{config.misc.epgcache_filename.value}")
									eEPGCache.getInstance().load()
									rmtree(epgdattmp)
									return self.ImportChannelsDone(True, _("EPG imported successfully from") + f" {self.url}")
							except Exception as err:
								print(f"[ImportChannels] cannot save EPG {err}")
				except Exception as err:
					print(f"[ImportChannels] {err}")
					return (self.downloadEPG(), self.importChannelsCallback()) if "channels_epg" in self.remote_fallback_import else self.downloadEPG()
		return self.importChannelsCallback()

	def ImportGetFilelist(self, remote=False, *files):
		result = []
		for file in files:
			# read the contents of the file
			try:
				if remote:
					try:
						content = self.getUrl(f"{self.url}/file?file={channelslistpath}/{quote(file)}").readlines()
						content = map(lambda x: x.decode('utf-8', 'replace'), content)
					except Exception as err:
						print(f"[ImportChannels] Exception: {err}")
						self.ImportChannelsNotDone(True, _("Access not available:\nCheck HTTP authentication not is active in OpenWebIF on the receiver fallback or check data entered in settings.\n") + _("Read failled") + f" {channelslistpath}/{file} " + _("From :") + f" {self.url}")
						return
				else:
					with open(f"{channelslistpath}/{file}", "r") as f:
						content = f.readlines()
			except Exception as e:
				# for the moment just log and ignore
				print(f"[ImportChannels] {e}")
				continue

			# check the contents for more bouquet files
			for line in content:
				# print ("[ImportChannels] %s" % line)
				# check if it contains another bouquet reference, first tv type then radio type
				r = match('#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "(.*)" ORDER BY bouquet', line) or match('#SERVICE 1:7:2:0:0:0:0:0:0:0:FROM BOUQUET "(.*)" ORDER BY bouquet', line)
				if r:
					# recurse
					result.extend(self.ImportGetFilelist(remote, r.group(1)))
			# add add the file itself
			result.append(file)

		# return the file list
		return result

	def importChannelsCallback(self):
		if "channels" in self.remote_fallback_import:
			print("[ImportChannels] Enumerate remote files")
			files = self.ImportGetFilelist(True, 'bouquets.tv', 'bouquets.radio')
			print("[ImportChannels] Enumerate remote support files")
			for file in loads(self.getUrl(f"{self.url}/file?dir={channelslistpath}").read())["files"]:
				if basename(file).startswith(supportfiles) and "opkg" not in file:
					files.append(file.replace(channelslistpath, ''))
			print("[ImportChannels] Fetch remote files")
			for file in files:
				if exists(file):
					print(f"[ImportChannels] Downloading {file}...")
				try:
					open(join(self.tmp_dir, basename(file)), "wb").write(self.getUrl(f"{self.url}/file?file={channelslistpath}/{quote(file)}").read())
				except Exception:
					if "epg" not in self.remote_fallback_import:
						self.ImportChannelsNotDone(True, _("Access not available:\nCheck HTTP authentication not is active in OpenWebIF on the receiver fallback or check data entered in settings.\n") + _("Failed to download") + f" {channelslistpath}/{file} " + _("From :") + f" {self.url}")
					return
			print("[ImportChannels] Enumerate local files")
			files = self.ImportGetFilelist(False, 'bouquets.tv', 'bouquets.radio')
			print("[ImportChannels] Removing files...")
			for file in files:
				if exists(join(channelslistpath, file)):
					remove(join(channelslistpath, file))
			print("[ImportChannels] Updating files...")
			files = [x for x in listdir(self.tmp_dir)]
			for file in files:
				print(f"- Moving {file}...")
				move(join(self.tmp_dir, file), join(channelslistpath, file))
			from Screens.InfoBar import InfoBar
			eDVBDB.getInstance().reloadBouquets()
			eDVBDB.getInstance().reloadServicelist()
			InfoBar.instance.servicelist.showAllServices()
			InfoBar.instance.servicelist.showFavourites()
			self.ImportChannelsDone(True, _("Channels imported successfully from") + f" {self.url}")
			if not files:
				from Components.ChannelsImporter import ChannelsImporter  # resource to import channels from ChannelsImporter
				ChannelsImporter()

	def ImportChannelsDone(self, flag, message=None):
		if hasattr(self, "tmp_dir") and exists(self.tmp_dir):
			rmtree(self.tmp_dir, True)
		if config.usage.remote_fallback_ok.value:
			AddNotificationWithID("ChannelsImportOK", MessageBox, _(message), type=MessageBox.TYPE_INFO, timeout=5)

	def ImportChannelsNotDone(self, flag, message=None):
		if hasattr(self, "tmp_dir") and exists(self.tmp_dir):
			rmtree(self.tmp_dir, True)
		if config.usage.remote_fallback_nok.value:
			AddNotificationWithID("ChannelsImportNOK", MessageBox, _(message), type=MessageBox.TYPE_ERROR, timeout=15)
