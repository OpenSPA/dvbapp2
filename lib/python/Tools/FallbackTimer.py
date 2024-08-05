from ServiceReference import ServiceReference
from Components.config import config
from Screens.MessageBox import MessageBox
from timer import TimerEntry as TimerObject
from urllib.parse import quote
from xml.etree.ElementTree import fromstring
from json import loads
from requests import get, exceptions
from twisted.internet.threads import deferToThread


class FallbackTimerList():

	def __init__(self, parent, fallbackFunction, fallbackFunctionNOK=None):
		self.fallbackFunction = fallbackFunction
		self.fallbackFunctionNOK = fallbackFunctionNOK or fallbackFunction
		self.parent = parent
		self.password = ""
		self.userid = ""
		if config.usage.remote_fallback_enabled.value and config.usage.remote_fallback_external_timer.value and config.usage.remote_fallback.value:
			self.url = config.usage.remote_fallback.value.rsplit(":", 1)[0]
			if config.usage.remote_fallback_openwebif_customize.value:
				self.url = "%s:%s" % (self.url, config.usage.remote_fallback_openwebif_port.value)
				self.password = config.usage.remote_fallback_openwebif_password.value
				self.userid = config.usage.remote_fallback_openwebif_userid.value
			self.getFallbackTimerList()
		else:
			self.url = None
			self.list = []
			# parent.onLayoutFinish.append(self.fallbackFunction)

	# remove any trailing channel name from the service reference
	def cleanServiceRef(self, service_ref):
		service_ref = str(service_ref)
		if not service_ref.endswith(":"):
			service_ref = service_ref.rsplit("::", 1)[0] + ":"
		return service_ref

	def sendAPIcommand(self, url, timeout=(3.05, 3), headers=None, verify=False):
		def sendUrl(url, timeout, headers, auth):
			try:
				response = get(url, headers=headers or {}, auth=auth, timeout=timeout, verify=verify)
				response.raise_for_status()
				return loads(response.content)
			except exceptions.RequestException as error:
				print("sendAPIcommand", error)

		auth = (self.userid, self.password) if self.password else None
		return deferToThread(lambda: sendUrl(url, timeout, headers, auth))

	def getUrl(self, url):
		print("[FallbackTimer] getURL", url)
		return self.sendAPIcommand(("%s/%s" % (self.url, url)))

	def getFallbackTimerList(self):
		self.list = []
		if self.url:
			try:
				self.getUrl("api/timerlist").addCallback(self.gotFallbackTimerList).addErrback(self.fallback)
			except:
				self.fallback(_("Unexpected error while retrieving fallback tuner's timer information"))
		else:
			self.fallback()

	def gotFallbackTimerList(self, jsondict):
		self.list = []
		self.locations = []
		self.tags = []
		self.default = None
		try:
			if 'result' in jsondict and not jsondict['result']:
				self.fallback(_("Fallback API did not return a valid result."))
			else:
				self.list = [FallbackTimerClass(timer) for timer in jsondict['timers']]
				self.locations = jsondict.get("locations", ["/media/hdd/movie"])
				self.tags = jsondict.get("tags", [])
				self.default = jsondict.get("default")

				self.fallback()

		except Exception as e:
			self.fallback(e)

		print("[FallbackTimer] read %s timers from fallback tuner" % len(self.list))
		self.parent.session.nav.RecordTimer.setFallbackTimerList(self.list)

	def removeTimer(self, timer, fallbackFunction, fallbackFunctionNOK=None):
		self.fallbackFunction = fallbackFunction
		self.fallbackFunctionNOK = fallbackFunctionNOK or fallbackFunction
		self.getUrl("web/timerdelete?sRef=%s&begin=%s&end=%s" % (self.cleanServiceRef(timer.service_ref), timer.begin, timer.end)).addCallback(self.getUrlFallback).addErrback(self.fallback)

	def toggleTimer(self, timer, fallbackFunction, fallbackFunctionNOK=None):
		self.fallbackFunction = fallbackFunction
		self.fallbackFunctionNOK = fallbackFunctionNOK or fallbackFunction
		self.getUrl("web/timertogglestatus?sRef=%s&begin=%s&end=%s" % (self.cleanServiceRef(timer.service_ref), timer.begin, timer.end)).addCallback(self.getUrlFallback).addErrback(self.fallback)

	def cleanupTimers(self, fallbackFunction, fallbackFunctionNOK=None):
		self.fallbackFunction = fallbackFunction
		self.fallbackFunctionNOK = fallbackFunctionNOK or fallbackFunction
		if self.url:
			self.getUrl("web/timercleanup?cleanup=true").addCallback(self.getUrlFallback).addErrback(self.fallback)
		else:
			self.fallback()

	def addTimer(self, timer, fallbackFunction, fallbackFunctionNOK=None):
		self.fallbackFunction = fallbackFunction
		self.fallbackFunctionNOK = fallbackFunctionNOK or fallbackFunction
		url = "web/timeradd?sRef=%s&begin=%s&end=%s&name=%s&description=%s&disabled=%s&justplay=%s&afterevent=%s&repeated=%s&dirname=%s&eit=%s" % (
			self.cleanServiceRef(timer.service_ref),
			timer.begin,
			timer.end,
			quote(timer.name.encode()),
			quote(timer.description.encode()),
			timer.disabled,
			timer.justplay,
			timer.afterEvent,
			timer.repeated,
			quote(timer.dirname),
			timer.eit or 0,
		)
		self.getUrl(url).addCallback(self.getUrlFallback).addErrback(self.fallback)

	def editTimer(self, timer, fallbackFunction, fallbackFunctionNOK=None):
		self.fallbackFunction = fallbackFunction
		self.fallbackFunctionNOK = fallbackFunctionNOK or fallbackFunction
		url = "web/timerchange?sRef=%s&begin=%s&end=%s&name=%s&description=%s&disabled=%s&justplay=%s&afterevent=%s&repeated=%s&channelOld=%s&beginOld=%s&endOld=%s&dirname=%s&eit=%s" % (
			self.cleanServiceRef(timer.service_ref),
			timer.begin,
			timer.end,
			quote(timer.name.encode()),
			quote(timer.description.encode()),
			timer.disabled,
			timer.justplay,
			timer.afterEvent,
			timer.repeated,
			timer.service_ref_prev,
			timer.begin_prev,
			timer.end_prev,
			quote(timer.dirname),
			timer.eit or 0,
		)
		self.getUrl(url).addCallback(self.getUrlFallback).addErrback(self.fallback)

	def getUrlFallback(self, data):
		try:
			root = fromstring(data)
			if root[0].text == 'True':
				self.getFallbackTimerList()
			else:
				self.fallback(root[1].text)
		except:
				self.fallback("Unexpected Error")

	def fallback(self, message=None):
		if message:
			self.parent.session.openWithCallback(self.fallbackNOK, MessageBox, _("Error while retrieving fallback timer information\n%s") % message, MessageBox.TYPE_ERROR)
		else:
			self.fallbackFunction()

	def fallbackNOK(self, answer=None):
		self.fallbackFunctionNOK()


class FallbackTimerDirs(FallbackTimerList):

	def fallback(self, message=None):
		if message:
			self.parent.session.openWithCallback(self.fallbackNOK, MessageBox, _("Error while retrieving fallback timer information\n%s") % message, MessageBox.TYPE_ERROR)
		else:
			self.fallbackFunction(self.locations, self.default, self.tags)


class FallbackTimerClass(TimerObject):
	def __init__(self, timerdict={}):
		self.service_ref = ServiceReference(timerdict.get("serviceref", 0))
		self.service_ref.ref.setName(timerdict.get("servicename", ""))
		eit = timerdict.get("eit", "None")
		self.eit = int(eit) if eit != "None" else 0
		self.name = timerdict.get("name")
		self.disabled = timerdict.get("disabled", 0)
		self.begin = begin = timerdict.get("begin", 0)
		self.end = end = timerdict.get("end", 0)
		self.duration = timerdict.get("duration", 0)
		self.startprepare = timerdict.get("startprepare", 0)
		self.state = timerdict.get("state", 0)
		self.description = timerdict.get("description", "None")
		self.justplay = justplay = timerdict.get("justplay", 0)
		self.afterevent = timerdict.get("afterevent", 0)
		self.dirname = timerdict.get("dirname", None)
		tags = timerdict.get("tags", "")
		self.tags = tags.split(" ") if tags else []
		self.repeated = timerdict.get("repeated", 0)
		self.descramble = timerdict.get("descramble", 1)
		self.record_ecm = timerdict.get("record_ecm", 0)
		self.always_zap = timerdict.get("always_zap", 0)
		self.isAutoTimer = timerdict.get("isAutoTimer", 0)
		self.ice_timer_id = timerdict.get("ice_timer_id", 0)
		if self.ice_timer_id == -1:
			self.ice_timer_id = 0
		marginBefore = timerdict.get("marginBefore", -1)
		marginAfter = timerdict.get("marginAfter", -1)
		if marginBefore == -1:
			marginBefore = (getattr(config.recording, "zap_margin_before" if justplay else "margin_before").value * 60)
		self.marginBefore = marginBefore
		if marginAfter == -1:
			marginAfter = (getattr(config.recording, "zap_margin_after" if justplay else "margin_after").value * 60)
		self.marginAfter = marginAfter
		self.eventBegin = timerdict.get("eventbegin", 0)
		if self.eventBegin == 0:
			self.eventBegin = begin + marginBefore
		self.eventEnd = timerdict.get("eventend", 0)
		if self.eventEnd == 0:
			self.eventEnd = end - marginAfter
		self.hasEndTime = timerdict.get("hasEndTime", False)
		self.rename_repeat = timerdict.get("rename_repeat", True)

		vpsenabled = timerdict.get("vpsplugin_enabled", False)
		vpsoverwrite = timerdict.get("vpsplugin_overwrite", False)
		vpstime = timerdict.get("vpsplugin_time", -1)
		self.vpsplugin_overwrite = vpsoverwrite
		self.vpsplugin_enabled = vpsenabled
		if vpstime and vpstime != "None":
			self.vpsplugin_time = vpstime
		#for log in timerdict.get("logentries", []):
		#	self.log_entries.append((log[0], log[1], log[2]))

		self.findRunningEvent = True
		self.findNextEvent = False

		self.flags = ""
		# self.conflict_detection = True
		self.external = True
		# self.zap_wakeup = False
		# self.pipzap = False
		self.repeatedbegindate = begin
		self.failed = self.state == 4

	def setServiceRef(self, sref):
		self.serviceRef = sref
		self.serviceRefString = sref.ref.toCompareString()

	def getServiceRef(self):
		return self.serviceRef

	service_ref = property(getServiceRef, setServiceRef)
