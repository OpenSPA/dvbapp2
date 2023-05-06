from os import listdir
from os.path import join, isdir, getsize, exists
from re import sub
import unicodedata
from Components.Renderer.Renderer import Renderer
from enigma import ePixmap, ePicLoad
from Tools.Alternatives import GetWithAlternative
from Tools.Directories import pathExists, SCOPE_SKINS, SCOPE_GUISKIN, resolveFilename
from Components.Harddisk import harddiskmanager
from ServiceReference import ServiceReference
from Components.config import config, ConfigText, ConfigYesNo

config.misc.picon_path = ConfigText(default = "/usr/share/enigma2/picon/")
config.misc.picon_search_hdd = ConfigYesNo (default = False)

searchPaths = []
lastPiconPath = None


def initPiconPaths():
	global searchPaths
	searchPaths = []
	######## OPENSPA [morser] Add picon path in config ######################
	path = str(config.misc.picon_path.value)
	for mp in ('/usr/share/enigma2/', '/', path):
		onMountpointAdded(mp)
	for part in harddiskmanager.getMountedPartitions():
		if not part.mountpoint.startswith("/media/hdd") or config.misc.picon_search_hdd.value == True: 
			onMountpointAdded(part.mountpoint)


def onMountpointAdded(mountpoint):
	global searchPaths
	######## OPENSPA [morser] Add others folders ######################
	try:
		path = join(mountpoint, 'XPicons') + '/'
		if isdir(path) and path not in searchPaths:
			for fn in listdir(path):
				if fn.endswith('.png'):
					print("[Picon] adding path:", path)
					searchPaths.append(path)
					break
		path = join(mountpoint, 'picon/XPicons') + '/'
		if isdir(path) and path not in searchPaths:
			for fn in listdir(path):
				if fn.endswith('.png'):
					print("[Picon] adding path:", path)
					searchPaths.append(path)
					break
		path = join(mountpoint, 'XPicons/picon') + '/'
		if isdir(path) and path not in searchPaths:
			for fn in listdir(path):
				if fn.endswith('.png'):
					print("[Picon] adding path:", path)
					searchPaths.append(path)
					break
		path = join(mountpoint, 'picon') + '/'
		if isdir(path) and path not in searchPaths:
			for fn in listdir(path):
				if fn.endswith('.png'):
					print("[Picon] adding path:", path)
					searchPaths.append(path)
					break
		path = mountpoint
		if isdir(path) and path not in searchPaths:
			for fn in listdir(path):
				if fn.endswith('.png'):
					print("[Picon] adding path:", path)
					searchPaths.append(path)
					break
	except Exception as ex:
		print("[Picon] Failed to investigate %s:" % mountpoint, ex)
	#################################################################################


def onMountpointRemoved(mountpoint):
	global searchPaths
	######## OPENSPA [morser] Delete All folders in mountpoint ######################
	for x in searchPaths:
		if mountpoint in x:
			try:
				searchPaths.remove(x)
				print("[Picon] removed path: %s" % x)
			except:
				pass
	#################################################################################


def onPartitionChange(why, part):
	if why == 'add':
		onMountpointAdded(part.mountpoint)
	elif why == 'remove':
		onMountpointRemoved(part.mountpoint)


def findPicon(serviceName):
	global lastPiconPath
	if lastPiconPath is not None:
		pngname = lastPiconPath + serviceName + ".png"
		if exists(pngname):
			return pngname
	######## OPENSPA [morser] Find picon in all search paths ######################
	pngname = ""
	for path in searchPaths:
		if exists(path):
			pngname = path + serviceName + ".png"
			if exists(pngname):
				lastPiconPath = path
				return pngname
	return ""
	#################################################################################

def getPiconName(serviceName):
	#remove the path and name fields, and replace ':' by '_'
	fields = GetWithAlternative(serviceName).split(':', 10)[:10]
	if not fields or len(fields) < 10:
		return ""
	pngname = findPicon('_'.join(fields))
	if not pngname and not fields[6].endswith("0000"):
		#remove "sub-network" from namespace
		fields[6] = fields[6][:-4] + "0000"
		pngname = findPicon('_'.join(fields))
	if not pngname and fields[0] != '1':
		#fallback to 1 for other reftypes
		fields[0] = '1'
		pngname = findPicon('_'.join(fields))
	if not pngname and fields[2] != '1':
		#fallback to 1 for services with different service types
		fields[2] = '1'
		pngname = findPicon('_'.join(fields))
	if not pngname: # picon by channel name
		name = ServiceReference(serviceName).getServiceName()
		name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode()
		name = sub('[^a-z0-9]', '', name.replace('&', 'and').replace('+', 'plus').replace('*', 'star').lower())
		if len(name) > 0:
			pngname = findPicon(name)
			if not pngname and len(name) > 2 and name.endswith('hd'):
				pngname = findPicon(name[:-2])
	return pngname


class Picon(Renderer):
	def __init__(self):
		Renderer.__init__(self)
		self.PicLoad = ePicLoad()
		self.PicLoad.PictureData.get().append(self.updatePicon)
		self.piconsize = (0, 0)
		self.pngname = ""
		self.lastPath = None
		pngname = findPicon("picon_default")
		self.defaultpngname = None
		if not pngname:
			tmp = resolveFilename(SCOPE_GUISKIN, "picon_default.png")
			if exists(tmp):
				pngname = tmp
			else:
				pngname = resolveFilename(SCOPE_SKINS, "skin_default/picon_default.png")
		self.nopicon = resolveFilename(SCOPE_SKINS, "skin_default/picon_default.png")
		if getsize(pngname):
			self.defaultpngname = pngname
			self.nopicon = pngname

	def addPath(self, value):
		if exists(value):
			global searchPaths
			if not value.endswith('/'):
				value += '/'
			if value not in searchPaths:
				searchPaths.append(value)

	def applySkin(self, desktop, parent):
		attribs = self.skinAttributes[:]
		for (attrib, value) in self.skinAttributes:
			if attrib == "path":
				self.addPath(value)
				attribs.remove((attrib, value))
			elif attrib == "size":
				self.piconsize = value
		self.skinAttributes = attribs
		return Renderer.applySkin(self, desktop, parent)

	GUI_WIDGET = ePixmap

	def postWidgetCreate(self, instance):
		self.changed((self.CHANGED_DEFAULT,))

	def updatePicon(self, picInfo=None):
		ptr = self.PicLoad.getData()
		if ptr is not None:
			self.instance.setPixmap(ptr.__deref__())
			self.instance.show()

	def changed(self, what):
		if self.instance:
			pngname = ""
			if what[0] == 1 or what[0] == 3:
				pngname = getPiconName(self.source.text)
				if not exists(pngname): # no picon for service found
					pngname = self.defaultpngname
				if not config.usage.showpicon.value:
					pngname = self.nopicon
				if self.pngname != pngname:
					if pngname:
						self.instance.setScale(1)
						self.instance.setPixmapFromFile(pngname)
						self.instance.show()
					else:
						self.instance.hide()
					self.pngname = pngname
			elif what[0] == 2:
				self.pngname = ""
				self.instance.hide()

###OPENSPA [morser] for Picon Path change
def setPiconPath():
	global lastPiconPath
	lastPiconPath = None
	initPiconPaths()
#####################################

harddiskmanager.on_partition_list_change.append(onPartitionChange)
initPiconPaths()
