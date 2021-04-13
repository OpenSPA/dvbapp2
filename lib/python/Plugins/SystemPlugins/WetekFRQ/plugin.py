#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from Screens.Screen import Screen
from Plugins.Plugin import PluginDescriptor
from Components.Console import Console
from Components.Button import Button
from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigList
from Components.config import config, configfile, ConfigSubsection, getConfigListEntry, ConfigSelection
from Components.ConfigList import ConfigListScreen
import Screens.Standby

config.plugins.wetek = ConfigSubsection()

config.plugins.wetek.governor = ConfigSelection(default='interactive', choices=[('hotplug', _('Hotplug')),
('interactive', _('Interactive (default)')),
('conservative', _('Conservative')),
('ondemand', _('Ondemand')),
('performance', _('Performance'))])
config.plugins.wetek.iosd = ConfigSelection(default='2048', choices=[('128', _('128')),
('256', _('256')),
('384', _('384')),
('512', _('512')),
('1024', _('1024')),
('2048', _('2048 (default)')),
('3072', _('3072'))])
config.plugins.wetek.scheduler = ConfigSelection(default='cfq', choices=[('nop', _('NOP')),
('deadline', _('Deadline')),
('cfq', _('CFQ (default)'))])
config.plugins.wetek.workfrq = ConfigSelection(default='1200000', choices=[('96000', _('96MHz')),
('192000', _('192MHz')),
('312000', _('312MHz')),
('408000', _('408MHz')),
('504000', _('504MHz')),
('600000', _('600MHz')),
('696000', _('696MHz')),
('816000', _('816MHz')),
('912000', _('912MHz')),
('1008000', _('1.08GHz')),
('1104000', _('1.104GHz')),
('1200000', _('1.2GHz (default)')),
('1296000', _('1.296GHz')),
('1416000', _('1.416GHz')),
('1512000', _('1.512GHz'))])
config.plugins.wetek.stdbyfrq = ConfigSelection(default='600000', choices=[('96000', _('96MHz')),
('192000', _('192MHz')),
('312000', _('312MHz')),
('408000', _('408MHz')),
('504000', _('504MHz')),
('600000', _('600MHz (default)')),
('696000', _('696MHz')),
('816000', _('816MHz')),
('912000', _('912MHz')),
('1008000', _('1.08GHz')),
('1104000', _('1.104GHz')),
('1200000', _('1.2GHz'))])

def leaveStandby():
    print '[WetekFRQ] Leave Standby'
    initBooster()


def standbyCounterChanged(configElement):
    print '[WetekFRQ] In Standby'
    initStandbyBooster()
    from Screens.Standby import inStandby
    inStandby.onClose.append(leaveStandby)


def initBooster():
    print '[WetekFRQ] initBooster'
    try:
        f = open('/sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq', 'w')
        f.write(config.plugins.wetek.workfrq.getValue())
        f.close()
        f = open('/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor', 'w')
        f.write(config.plugins.wetek.governor.getValue())
        f.close()
        f = open('/sys/block/mmcblk0/queue/scheduler', 'w')
        f.write(config.plugins.wetek.scheduler.getValue())
        f.close()
        f = open('/sys/block/mmcblk0/queue/read_ahead_kb', 'w')
        f.write(config.plugins.wetek.iosd.getValue())
        f.close()
    except:
        pass


def initStandbyBooster():
    print '[WetekFRQ] initStandbyBooster'
    try:
        f = open('/sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq', 'w')
        f.write(config.plugins.wetek.stdbyfrq.getValue())
        f.close()
    except:
        pass


class WetekFRQ(ConfigListScreen, Screen):

    def __init__(self, session, args=None):
        self.skin = '\n\t\t\t<screen position="150,150" size="500,210" title="Wetek CPU Frequency Setup" >\n\t\t\t\t<widget name="config" position="20,15" size="460,150" scrollbarMode="showOnDemand" />\n\t\t\t\t<ePixmap position="40,165" size="140,40" pixmap="skin_default/buttons/green.png" alphatest="on" />\n\t\t\t\t<ePixmap position="180,165" size="140,40" pixmap="skin_default/buttons/red.png" alphatest="on" />\n\t\t\t\t<widget name="key_green" position="40,165" size="140,40" font="Regular;20" backgroundColor="#1f771f" zPosition="2" transparent="1" shadowColor="black" shadowOffset="-1,-1" />\n\t\t\t\t<widget name="key_red" position="180,165" size="140,40" font="Regular;20" backgroundColor="#9f1313" zPosition="2" transparent="1" shadowColor="black" shadowOffset="-1,-1" />\n\t\t\t</screen>'
        Screen.__init__(self, session)
        self.onClose.append(self.abort)
        self.onChangedEntry = []
        self.list = []
        ConfigListScreen.__init__(self, self.list, session=self.session, on_change=self.changedEntry)
        self.createSetup()
        self.Console = Console()
        self['key_red'] = Button(_('Cancel'))
        self['key_green'] = Button(_('Save'))
        self['key_yellow'] = Button(_('Test'))
        self['setupActions'] = ActionMap(['SetupActions', 'ColorActions'], {'save': self.save,
         'cancel': self.cancel,
         'ok': self.save,
         'yellow': self.Test}, -2)

    def createSetup(self):
        self.editListEntry = None
        self.list = []
        self.list.append(getConfigListEntry(_('OpenSPA Max CPU frequency'), config.plugins.wetek.workfrq))
        self.list.append(getConfigListEntry(_('Standby Max CPU frequency'), config.plugins.wetek.stdbyfrq))
        self.list.append(getConfigListEntry(_('Scaling Governor'), config.plugins.wetek.governor))
        self.list.append(getConfigListEntry(_('I/O Scheduler'), config.plugins.wetek.scheduler))
        self.list.append(getConfigListEntry(_('I/O Read ahead'), config.plugins.wetek.iosd))
        self['config'].list = self.list
        self['config'].l.setList(self.list)

    def changedEntry(self):
        for x in self.onChangedEntry:
            x()

        self.newConfig()

    def newConfig(self):
        print self['config'].getCurrent()[0]
        if self['config'].getCurrent()[0] == _('Start Boot Frequency'):
            self.createSetup()

    def abort(self):
        print 'aborting'

    def save(self):
        for x in self['config'].list:
            x[1].save()

        configfile.save()
        initBooster()
        self.close()

    def cancel(self):
        initBooster()
        for x in self['config'].list:
            x[1].cancel()

        self.close()

    def Test(self):
        self.createSetup()
        initBooster()


class WETEK_Booster:

    def __init__(self, session):
        print '[WetekFRQ] initializing'
        self.session = session
        self.service = None
        self.onClose = []
        self.Console = Console()
        initBooster()

    def shutdown(self):
        self.abort()

    def abort(self):
        print '[WetekFRQ] aborting'

    config.misc.standbyCounter.addNotifier(standbyCounterChanged, initial_call=False)


def main(menuid):
    if menuid != 'system':
        return []
    return [(_('Wetek CPU Control'),
      startBooster,
      'Wetek CPU Control',
      None)]


def startBooster(session, **kwargs):
    session.open(WetekFRQ)


wbooster = None
gReason = -1
mySession = None

def wetekbooster():
    global wbooster
    global mySession
    global gReason
    if gReason == 0 and mySession != None and wbooster == None:
        print '[WetekFRQ] Starting !!'
        wbooster = WETEK_Booster(mySession)
    elif gReason == 1 and wbooster != None:
        print '[WetekFRQ] Stopping !!'
        wbooster = None


def sessionstart(reason, **kwargs):
    global mySession
    global gReason
    print '[WetekFRQ] sessionstart'
    if kwargs.has_key('session'):
        mySession = kwargs['session']
    else:
        gReason = reason
    wetekbooster()


def Plugins(**kwargs):
    return [PluginDescriptor(where=[PluginDescriptor.WHERE_AUTOSTART, PluginDescriptor.WHERE_SESSIONSTART], fnc=sessionstart), PluginDescriptor(name='Wetek FRQ Setup', description='Set CPU Speed Settings', where=PluginDescriptor.WHERE_MENU, fnc=main)]
