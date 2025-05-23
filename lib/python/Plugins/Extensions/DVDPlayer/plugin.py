from os.path import exists, join

from Components.Harddisk import harddiskmanager
from Components.Scanner import Scanner, ScanPath
from Plugins.Plugin import PluginDescriptor
from Screens.DVD import DVDPlayer as _DVDPlayer, DVDOverlay as _DVDOverlay
from Tools.Directories import fileExists

detected_DVD = None


def main(session, **kwargs):
	session.open(_DVDPlayer)


def play(session, **kwargs):
	if (exists(join(harddiskmanager.getAutofsMountpoint(harddiskmanager.getCD()), "VIDEO_TS"))
			or exists(join(harddiskmanager.getAutofsMountpoint(harddiskmanager.getCD()), "video_ts"))):
		session.open(DVDPlayer, dvd_device=harddiskmanager.getAutofsMountpoint(harddiskmanager.getCD()))
	else:
		return


def DVDPlayer(*args, **kwargs):  # for backward compatibility with plugins that do "from DVDPlayer.plugin import DVDPlayer"
	return _DVDPlayer(*args, **kwargs)


def DVDOverlay(*args, **kwargs):  # for backward compatibility with plugins that do "from DVDPlayer.plugin import DVDOverlay"
	return _DVDOverlay(*args, **kwargs)


def filescan_open(list, session, **kwargs):
	if len(list) == 1 and list[0].mimetype == "video/x-dvd":
		cd = harddiskmanager.getCD()
		if cd and (exists(join(harddiskmanager.getAutofsMountpoint(cd), "VIDEO_TS"))
				or exists(join(harddiskmanager.getAutofsMountpoint(cd), "video_ts"))):
			print("[DVDplayer] found device /dev/%s", " mount path ", harddiskmanager.getAutofsMountpoint(cd))
			session.open(DVDPlayer, dvd_device="/dev/%s" % (harddiskmanager.getAutofsMountpoint(cd)))
			return
	else:
		dvd_filelist = []
		for x in list:
			if x.mimetype == "video/x-dvd-iso":
				dvd_filelist.append(x.path)
			if x.mimetype == "video/x-dvd":
				dvd_filelist.append(x.path.rsplit('/', 1)[0])
		session.open(DVDPlayer, dvd_filelist=dvd_filelist)


def filescan(**kwargs):

	# Overwrite checkFile to only detect local
	class LocalScanner(Scanner):
		def checkFile(self, file):
			return fileExists(file.path)

	return [
		LocalScanner(mimetypes=["video/x-dvd", "video/x-dvd-iso"],
			paths_to_scan=[
					ScanPath(path="video_ts", with_subdirs=False),
					ScanPath(path="VIDEO_TS", with_subdirs=False),
					ScanPath(path="", with_subdirs=False),
				],
			name="DVD",
			description=_("Play DVD"),
			openfnc=filescan_open,
		)]


def onPartitionChange(action, partition):
	# print("[@] onPartitionChange", action, partition)
	if partition != harddiskmanager.getCD():
		global detected_DVD
		if action == 'remove':
			# print("[DVDplayer] DVD removed")
			detected_DVD = False
		elif action == 'add':
			# print("[DVDplayer] DVD Inserted")
			detected_DVD = None


def menu(menuid, **kwargs):
	if menuid == "mainmenu":
		global detected_DVD
		if detected_DVD is None or detected_DVD:
			cd = harddiskmanager.getCD()
			if cd and (exists(join(harddiskmanager.getAutofsMountpoint(cd), "VIDEO_TS"))
					or exists(join(harddiskmanager.getAutofsMountpoint(cd), "video_ts"))):
				print("[DVDplayer] Mountpoint is present and is", harddiskmanager.getAutofsMountpoint(cd))
				detected_DVD = True
			else:
				detected_DVD = False
			if onPartitionChange not in harddiskmanager.on_partition_list_change:
				harddiskmanager.on_partition_list_change.append(onPartitionChange)
		if detected_DVD:
			return [(_("DVD player"), play, "dvd_player", 46)]
	return []


def Plugins(**kwargs):
	return [PluginDescriptor(where=PluginDescriptor.WHERE_FILESCAN, needsRestart=False, fnc=filescan),
		PluginDescriptor(name=_("DVDPlayer"), description=_("Play DVDs"), where=PluginDescriptor.WHERE_MENU, needsRestart=False, fnc=menu)]
