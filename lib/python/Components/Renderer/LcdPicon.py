import os
import re
import unicodedata
from Components.Renderer.Renderer import Renderer
from enigma import ePixmap, ePicLoad
from Tools.Alternatives import GetWithAlternative
from Tools.Directories import pathExists, SCOPE_GUISKIN, resolveFilename
from Components.Harddisk import harddiskmanager
from ServiceReference import ServiceReference
from Components.SystemInfo import BoxInfo
from Components.config import config

searchPaths = []
lastLcdPiconPath = None
DISPLAYTYPE = BoxInfo.getItem("displaytype")


def initLcdPiconPaths():
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
		if DISPLAYTYPE in ('bwlcd255', 'bwlcd140') and not BoxInfo.getItem("grautec") or os.path.isdir(mountpoint + 'piconlcd'):
			path = os.path.join(mountpoint, 'piconlcd') + '/'
			if os.path.isdir(path) and path not in searchPaths:
				for fn in os.listdir(path):
					if fn.endswith('.png'):
						print("[LcdPicon] adding path: %s" % path)
						searchPaths.append(path)
						break
		else:
			path = os.path.join(mountpoint, 'XPicons') + '/'
			if os.path.isdir(path) and path not in searchPaths:
				for fn in os.listdir(path):
					if fn.endswith('.png'):
						print("[Picon] adding path:", path)
						searchPaths.append(path)
						break
			path = os.path.join(mountpoint, 'picon/XPicons') + '/'
			if os.path.isdir(path) and path not in searchPaths:
				for fn in os.listdir(path):
					if fn.endswith('.png'):
						print("[Picon] adding path:", path)
						searchPaths.append(path)
						break
			path = os.path.join(mountpoint, 'XPicons/picon') + '/'
			if os.path.isdir(path) and path not in searchPaths:
				for fn in os.listdir(path):
					if fn.endswith('.png'):
						print("[Picon] adding path:", path)
						searchPaths.append(path)
						break
			path = os.path.join(mountpoint, 'picon') + '/'
			if os.path.isdir(path) and path not in searchPaths:
				for fn in os.listdir(path):
					if fn.endswith('.png'):
						print("[Picon] adding path:", path)
						searchPaths.append(path)
						break
			path = mountpoint
			if os.path.isdir(path) and path not in searchPaths:
				for fn in os.listdir(path):
					if fn.endswith('.png'):
						print("[Picon] adding path:", path)
						searchPaths.append(path)
						break
	except Exception as ex:
		print("[LcdPicon] Failed to investigate %s:%s" % (mountpoint, str(ex)))
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


def findLcdPicon(serviceName):
	global lastLcdPiconPath
	if lastLcdPiconPath is not None:
		pngname = lastLcdPiconPath + serviceName + ".png"
		if pathExists(pngname):
			return pngname
	######## OPENSPA [morser] Find picon in all search paths ######################
	pngname = ""
	for path in searchPaths:
		if pathExists(path):
			pngname = path + serviceName + ".png"
			if pathExists(pngname):
				lastLcdPiconPath = path
				break
	if pathExists(pngname):
		return pngname
	else:
		return ""
	#################################################################################


def getLcdPiconName(serviceName):
	#remove the path and name fields, and replace ':' by '_'
	sname = '_'.join(GetWithAlternative(serviceName).split(':', 10)[:10])
	pngname = findLcdPicon(sname)
	if not pngname:
		fields = sname.split('_', 3)
		if len(fields) > 2 and fields[2] != '1':  # fallback to 1 for services with different service types
			fields[2] = '1'
		if len(fields) > 0 and fields[0] != '1':  # fallback to 1 for IPTV streams
			fields[0] = '1'
		pngname = findLcdPicon('_'.join(fields))
	if not pngname:  # picon by channel name
		name = ServiceReference(serviceName).getServiceName()
		name = unicodedata.normalize('NFKD', name)
		name = re.sub('[^a-z0-9]', '', name.replace('&', 'and').replace('+', 'plus').replace('*', 'star').lower())
		if len(name) > 0:
			pngname = findLcdPicon(name)
			if not pngname and len(name) > 2 and name.endswith('hd'):
				pngname = findLcdPicon(name[:-2])
	return pngname


class LcdPicon(Renderer):
	def __init__(self):
		Renderer.__init__(self)
		self.PicLoad = ePicLoad()
		self.PicLoad.PictureData.get().append(self.updatePicon)
		self.piconsize = (0, 0)
		self.pngname = ""
		self.lastPath = None
		if DISPLAYTYPE in ('bwlcd255', 'bwlcd140') and not BoxInfo.getItem("grautec"):
			pngname = findLcdPicon("lcd_picon_default")
		else:
			pngname = findLcdPicon("picon_default")
		self.defaultpngname = None
		if not pngname:
			if DISPLAYTYPE in ('bwlcd255', 'bwlcd140') and not BoxInfo.getItem("grautec"):
				tmp = resolveFilename(SCOPE_GUISKIN, "lcd_picon_default.png")
			else:
				tmp = resolveFilename(SCOPE_GUISKIN, "picon_default.png")
			if pathExists(tmp):
				pngname = tmp
			else:
				if DISPLAYTYPE in ('bwlcd255', 'bwlcd140') and not BoxInfo.getItem("grautec"):
					pngname = resolveFilename(SCOPE_GUISKIN, "lcd_picon_default.png")
				else:
					pngname = resolveFilename(SCOPE_GUISKIN, "picon_default.png")
		if os.path.getsize(pngname):
			self.defaultpngname = pngname

	def addPath(self, value):
		if pathExists(value):
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
				pngname = getLcdPiconName(self.source.text)
				if not pathExists(pngname):  # no picon for service found
					pngname = self.defaultpngname
				if self.pngname != pngname:
					if pngname:
						self.PicLoad.setPara((self.piconsize[0], self.piconsize[1], 0, 0, 1, 1, "#FF000000"))
						self.PicLoad.startDecode(pngname)
					else:
						self.instance.hide()
					self.pngname = pngname


harddiskmanager.on_partition_list_change.append(onPartitionChange)
initLcdPiconPaths()
