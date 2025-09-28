from Screens.Screen import Screen
from Components.ActionMap import NumberActionMap
from Components.Pixmap import Pixmap
from Components.Label import Label
from Components.MenuList import MenuList
from os import path, walk
from enigma import eEnv

class LCDClockSelector(Screen):
	skin = """
		<screen name="LCDClockSelector" position="center,center" size="700,350" title="LCD Clock-Selector" >
			<widget name="lab1" position="50,30" size="250,26" zPosition="1"  font="Regular;22" halign="left" transparent="1" />
			<widget name="lab2" position="380,30" size="250,26" zPosition="1" font="Regular;22" halign="left" transparent="1" />
			<widget name="ClockList" position="50,85" size="270,210" enableWrapAround="1" scrollbarMode="showOnDemand" itemHeight="30" />
			<widget name="Preview" position="380,80" size="280,210" zPosition="2" backgroundColor="background" transparent="0" alphatest="on" />
			<widget name="lab3" position="0,315" halign="center" size="700,30" zPosition="1" foregroundColor="#FFE500" font="Regular;22" transparent="1" />
		</screen> """

	clocklist = []
	root = eEnv.resolve("${datadir}/enigma2/display/clock_skin/")

	def __init__(self, session, args = None):

		Screen.__init__(self, session)
		self.clocklist = []
		self.previewPath = ""
		self.find()
		self.clocklist.sort()
		self["ClockList"] = MenuList(self.clocklist)
		self["Preview"] = Pixmap()
		self["lab1"] = Label(_("Select LCD clock:"))
		self["lab2"] = Label(_("Preview:"))
		self["lab3"] = Label(_("Select your LCD clock and press OK to activate the selected clock."))

		self["actions"] = NumberActionMap(["WizardActions", "InputActions", "EPGSelectActions"],
		{
			"ok": self.ok,
			"back": self.close,
			"up": self.up,
			"down": self.down,
			"left": self.left,
			"right": self.right,
		}, -1)

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		try:
			what = open(self.root+'active','r').read()
		except Exception:
			what = "clock_lcd_analog.xml"
		tmp = what
		if tmp in self.clocklist:
			idx = 0
			for skin in self.clocklist:
				if skin == tmp:
					break
				idx += 1
			if idx < len(self.clocklist):
				self["ClockList"].moveToIndex(idx)
		else:
			idx = 0
			self["ClockList"].moveToIndex(idx)
		self.loadPreview()

	def up(self):
		self["ClockList"].up()
		self.loadPreview()

	def down(self):
		self["ClockList"].down()
		self.loadPreview()

	def left(self):
		self["ClockList"].pageUp()
		self.loadPreview()

	def right(self):
		self["ClockList"].pageDown()
		self.loadPreview()

	def find(self):
		for directory, dirnames, filenames in walk(self.root):
			for x in filenames:
				if x.startswith("clock_lcd") and x.endswith(".xml"):
					skinname = x
					self.clocklist.append(skinname)

	def ok(self):
		clockfile = self["ClockList"].getCurrent()
		fp = open(self.root+'active','w')
		fp.write(clockfile)
		fp.close()
		self.close()

	def loadPreview(self):
		pngpath = self["ClockList"].getCurrent()
		try:
			pngpath = pngpath.replace(".xml", "_prev.png")
			pngpath = self.root+pngpath
		except Exception:
			pngpath = "usr/share/enigma2/display/clock_skin/noprev.png"
		if not path.exists(pngpath):
			pngpath = eEnv.resolve("${datadir}/enigma2/display/clock_skin/noprev.png")
		if self.previewPath != pngpath:
			self.previewPath = pngpath

		self["Preview"].instance.setPixmapFromFile(self.previewPath)
