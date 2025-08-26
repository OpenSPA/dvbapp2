from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest
from Components.Sources.StaticText import StaticText
from Components.Sources.List import List
from Components.ActionMap import ActionMap
from Screens.Screen import Screen
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Screens.Console import Console
from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import resolveFilename, SCOPE_CURRENT_SKIN
from os import system

menuid = 0

class Ipkuninstall(Screen):
	skin = """
		<screen name="Ipkuninstall" position="center,center" size="530,400" title="Ipk Uninstaller - Main Menu" >
			<widget source="list" render="Listbox" position="10,50" size="510,380" zPosition="1" scrollbarMode="showOnDemand">
				<convert type="TemplatedMultiContent">
					{"template": [
									MultiContentEntryText(pos = (110, 2), size = (440, 26), font=0, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text = 0), # index 2 is the description
									MultiContentEntryText(pos = (110, 28), size = (440, 26), font=1, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text = 2), # index 2 is the description
									MultiContentEntryPixmapAlphaTest(pos = (2, 1), size = (100, 50), png = 3), # index 4 is the status pixmap
									MultiContentEntryPixmapAlphaTest(pos = (0, 54), size = (510, 2), png = 4), # index 4 is the div pixmap
							],
					"fonts": [gFont("Regular", 24),gFont("Regular", 16)],
					"itemHeight": 58
					}
				</convert>
			</widget>
			<widget source="info" render="Label" position="150,10" size="450,25" zPosition="1" font="Regular;22" foregroundColor="#ffffff" transparent="1" halign="left" valign="center" />
		</screen>"""

	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		self.skinName = "Ipkuninstall"

		self['actions'] = ActionMap(['OkCancelActions'],
		{
			'ok': self.okPressed,
			'cancel': self.exit
		}, -1)
		self['info'] = StaticText(_("Please select a category."))
		self.list = []
		self['list'] = List(self.list)
		self.onLayoutFinish.append(self.createMenu)

	def createMenu(self):
		self.mylist = []
		divpng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, 'skin_default/div-h.png'))
		self.mylist.append((_('Cams'), 'CamSelectMenu', _('Delete cams previous installed.'), LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, 'skin_default/icons/ipkgcam.png')), divpng))
		self.mylist.append((_('Drivers'), 'DriversSelectMenu', _('Delete drivers previous installed.'), LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, 'skin_default/icons/ipkgpdrivers.png')), divpng))
		self.mylist.append((_('Extensions'), 'ExtSelectMenu', _('Delete extensions previous installed.'), LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, 'skin_default/icons/ipkgextensions.png')), divpng))
		self.mylist.append((_('SystemPlugins'), 'SysSelectMenu', _('Delete systemplugins previous installed.'), LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, 'skin_default/icons/ipkgsystemplugins.png')), divpng))
		self.mylist.append((_('Skins'), 'SkinSelectMenu', _('Delete skins previous installed.'), LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, 'skin_default/icons/ipkgskins.png')), None))
		self['list'].setList(self.mylist)

	def okPressed(self):
		cur = self['list'].getCurrent()
		if cur:
			name = cur[0]
			menu = cur[1]
			global menuid
			if menu == 'CamSelectMenu':
				print('[IPKUninstall] open menu %s linked to %s ' % (menu, name))
				menuid = 1
				self.session.open(IpkuninstallList)
			elif menu == 'DriversSelectMenu':
				print('[IPKUninstall] open menu %s linked to %s ' % (menu, name))
				menuid = 2
				self.session.open(IpkuninstallList)
			elif menu == 'ExtSelectMenu':
				menuid = 3
				print('[IPKUninstall] open menu %s linked to %s ' % (menu, name))
				self.session.open(IpkuninstallList)
			elif menu == 'SysSelectMenu':
				menuid = 4
				print('[IPKUninstall] open menu %s linked to %s ' % (menu, name))
				self.session.open(IpkuninstallList)
			elif menu == 'SkinSelectMenu':
				menuid = 5
				print('[IPKUninstall] open menu %s linked to %s ' % (menu, name))
				self.session.open(IpkuninstallList)
			else:
				menuid = 0
				message = '[IPKUninstall] no menu linked to ' + name
				self.session.open(MessageBox, message, MessageBox.TYPE_INFO, timeout=5)

	def exit(self):
		self.close()

def Command(command):
	import shlex
	import subprocess
	comm = command.strip().split("| ")
	old = None
	out = ""
	for cmd in comm:
#		open("/tmp/prueba","a").write(str(cmd)+"\n")
		cmd = shlex.split(cmd.strip())
		process = subprocess.Popen(cmd, stdin=old, stdout=subprocess.PIPE)
		old=process.stdout
	for ex in old:
		out = out + ex.decode("utf-8")
	return out.rstrip("\n")

class IpkuninstallList(Screen):
	skin = """
		<screen name="IpkuninstallList" position="center,center" size="530,400" title="Ipk Uninstaller - List installed packages" >
			<widget name="list" position="10,50" size="510,360" zPosition="1" scrollbarMode="showOnDemand" />
			<widget source="info" render="Label" position="center,10" size="450,25" zPosition="1" font="Regular;22" foregroundColor="#ffffff" transparent="1" halign="left" valign="center" />
		</screen>"""

	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		self.skinName = "IpkuninstallList"

		self['actions'] = ActionMap(['OkCancelActions'],
		{
			'ok': self.okClicked,
			'cancel': self.cancel
		}, -1)
		self['info'] = StaticText()
		self['info'].setText(_("Please select the package to delete."))
		self['list'] = MenuList([])
		self.onShown.append(self.startSession)

	def startSession(self):
		self.ipklist = []
		self.ipklist1 = []
		if menuid == 1:
			cmd = 'opkg list_installed | grep cam'
		elif menuid == 2:
			cmd = 'opkg list_installed | grep enigma2-plugin-drivers'
		elif menuid == 3:
			cmd = 'opkg list_installed | grep enigma2-plugin-extensions'
		elif menuid == 4:
			cmd = 'opkg list_installed | grep enigma2-plugin-systemplugins'
		elif menuid == 5:
			cmd = 'opkg list_installed | grep -e enigma2-plugin-skins -e skin'
		com = Command(cmd)
		line=com.split('\n')
		for filename in line:
			self.ipklist.append(filename[:-1].split(' - ')[0])
			self.ipklist1.append(filename[:-1])

		self['list'].setList(self.ipklist)

	def okClicked(self):
		ires = self["list"].getSelectionIndex()
		if ires is not None:
			self.ipk = self.ipklist1[ires]
			n1 = self.ipk.find("_", 0)
			self.ipk = self.ipk[:n1]
			self.session.openWithCallback(self.delete, ChoiceBox, title=_("Select method?"), list=[(_("Remove"), "rem"), (_("Force Depends"), "force-depends"), (_("Force Remove"), "force-remove")])
		else:
			return

	def cancel(self):
		self.close()

	def delete(self, answer):
		cmd = " "
		title = " "
		if answer is not None:
			if answer[1] == "rem":
				cmd = "opkg remove " + self.ipk
				title = (_("Removing ipk %s") % (self.ipk))
			elif answer[1] == "force-depens":
				cmd = "opkg remove --autoremove --force-depends " + self.ipk
				title = (_("Removing Depends of ipk %s") % (self.ipk))
			elif answer[1] == "force-remove":
				cmd = "opkg remove --force-remove " + self.ipk
				title = (_("Force Removing ipk %s") % (self.ipk))

			self.session.open(Console,_(title),[cmd])
			self.close()
