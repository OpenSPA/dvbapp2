import struct
from os import mkdir, path
from Components.SystemInfo import SystemInfo
from Screens.HelpMenu import HelpableScreen
from Screens.Screen import Screen
from Screens.Standby import QUIT_REBOOT, TryQuitMainloop
from Screens.MessageBox import MessageBox
from Components.ActionMap import ActionMap
from Plugins.Plugin import PluginDescriptor


class DualBootSelector(Screen, HelpableScreen):
	skinTemplate = """
	<screen title="DualBoot Image Selector" position="center,center" size="%d,%d">
		<widget name="config" position="%d,%d" size="%d,%d" font="Regular;%d" itemHeight="%d" scrollbarMode="showOnDemand" />
		<widget source="options" render="Label" position="%d,e-160" size="%d,%d" font="Regular;%d" halign="center" valign="center" />
		<widget source="description" render="Label" position="%d,e-90" size="%d,%d" font="Regular;%d" />
		<widget source="key_red" render="Label" position="%d,e-50" size="%d,%d" backgroundColor="key_red" font="Regular;%d" foregroundColor="key_text" halign="center" noWrap="1" valign="center" />
		<widget source="key_green" render="Label" position="%d,e-50" size="%d,%d" backgroundColor="key_green" font="Regular;%d" foregroundColor="key_text" halign="center" noWrap="1" valign="center" />
	</screen>"""

	def __init__(self, session, args = 0):
		Screen.__init__(self, session)
                self["actions"] = ActionMap(["OkCancelActions"],
                {
                        "ok": self.restartImage,
                        "cancel": self.close,
                })
                self.onShown.append(self.AndroidBoot)

        def restartImage(self, answer):
                if answer is True:
                        with open('/dev/block/by-name/flag', 'wb') as f:
                                f.write(struct.pack("B", 0))
                        self.session.open(TryQuitMainloop, 2)
                else:
                        self.close()

        def AndroidBoot(self):
                self.onShown.remove(self.AndroidBoot)
                message = _("Do you want to boot up on Android...? ")
                self.session.openWithCallback(self.restartImage, MessageBox, _("\n Do you want to switch Enigma2 with Android...?"))

def DualBootMain(session, **kwargs):
        session.open(DualBootSelector)

def DualBootSetup(menuid, **kwargs):
        if SystemInfo["canDualBoot"]:
	        if menuid == "mainmenu":
		        return [(_("Dual-Boot"), DualBootMain, "dualboot_selector", None)]
                else:
                        return []
	else:
                return []

def Plugins(**kwargs):
	return PluginDescriptor(name=_("Dual-Boot"), description=_("E2 switch to Android"), icon="dualboot.png", where = PluginDescriptor.WHERE_MENU, needsRestart = False, fnc=DualBootSetup)
