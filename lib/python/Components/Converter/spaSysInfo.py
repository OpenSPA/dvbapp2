from Components.Converter.Converter import Converter
from Components.Element import cached
from Components.Harddisk import harddiskmanager
from Poll import Poll
from boxbranding import getImageVersion, getImageBuild, getMachineBrand, getMachineName
from os import path, statvfs

class spaSysInfo(Poll, Converter, object):
    HDD = -2
    DISKS = -1
    DISKSLEEP = -3
    FLASH = 0
    MEMTOTAL = 1
    MEMTOTALLONG = 2
    VERSION = 3
    CPUUSAGE = 4
    NET = 5

    def __init__(self, type):
        Converter.__init__(self, type)
        Poll.__init__(self)
        self.type = self.VERSION
        self.percentlist = []
        self.pfmt = '%3d%%'
        self.sfmt = '$0'
        self.cpuUsageMonitorSPA = None
        if type == 'DiskAll':
            self.type = self.DISKS
            self.poll_enabled = True
            self.poll_interval = 10200
        if type == 'DiskAllSleep':
            self.type = self.DISKSLEEP
            self.poll_enabled = True
            self.poll_interval = 10200
        elif type == 'HDD':
            self.type = self.HDD
            self.poll_enabled = False
        elif type == 'Flash':
            self.type = self.FLASH
        elif type == 'MemTotal':
            self.type = self.MEMTOTAL
            self.poll_interval = 1200
            self.poll_enabled = True
        elif type == 'MemTotalLong':
            self.type = self.MEMTOTALLONG
            self.poll_interval = 10000
            self.poll_enabled = True
        elif type == 'CpuUsage':
            self.type = self.CPUUSAGE
            self.poll_interval = 1500
            self.poll_enabled = True
            self.cpuUsageMonitorSPA = spaCpuUsageMonitor()
        elif type == 'Version':
            self.type = self.VERSION
            self.pol_enabled = False
        elif type == 'Net':
            self.poll_interval = 10000
            self.type = self.NET
            self.poll_enabled = True
        return

    def doSuspend(self, suspended):
        pass

    def gotPercentage(self, list):
        pass

    @cached
    def getText(self):
        text = ''
        if self.type == self.DISKS or self.type == self.DISKSLEEP:
            text = '' + devDiskInfo('/', 'Flash') + '\n' + devDiskInfo('/hdd/', 'HDD', self.type == self.DISKSLEEP)
            latemp = getTemperatura()
            if not latemp == '':
                text = text + ' - ' + latemp
        elif self.type == self.FLASH:
            text = '' + devDiskInfo('/', 'Flash')
        elif self.type == self.HDD:
            text = devDiskInfo('/hdd/', 'HDD')
        elif self.type == self.MEMTOTAL or self.type == self.MEMTOTALLONG:
            freemem, totmem = getMemoria()
            if totmem > 0:
                ocupada = totmem - freemem
                porcentaje = int(freemem * 100 / totmem)
                if self.type == self.MEMTOTAL:
                    porcentaje = int(ocupada * 100 / totmem)
                    text = 'RAM ' + Humanizer(totmem * 1024) + ', ' + str(porcentaje) + '% ' + _('used')
                else:
                    text = _('RAM Memory') + ' ' + Humanizer(totmem * 1024, 0) + ' - ' + _('free') + ': ' + Humanizer(freemem * 1024, 0) + ' (' + str(porcentaje) + '%)'
                    latemp = getTemperatura()
                    if not latemp == '':
                        text = text + ' :: ' + latemp
        elif self.type == self.VERSION:
            maquina = getMachineBrand() + ' ' + getMachineName()
            text = ' Modelo Receptor: ' + maquina
        elif self.type == self.CPUUSAGE:
            self.percentlist = self.cpuUsageMonitorSPA.pollx()
            res = self.sfmt[:]
            if not self.percentlist:
                self.percentlist = [0] * 3
            for i in range(len(self.percentlist)):
                res = res.replace('$' + str(i), self.pfmt % self.percentlist[i])

            res = res.replace('$?', '%d' % (len(self.percentlist) - 1))
            if res == '0%':
                res = '1%'
            text = 'CPU: ' + res
        elif self.type == self.NET:
            text = getInfoNet()
        return text

    text = property(getText)

    @cached
    def getValue(self):
        valor = None
        if self.type == self.MEMTOTAL:
            freemem, totmem = getMemoria()
            ocupada = totmem - freemem
            valor = int(ocupada * 100 / totmem)
            pos = valor
            len = 100
            valor = pos * 10000 / len
        elif self.type == self.CPUUSAGE:
            i = 0
            try:
                value = self.percentlist[i]
            except IndexError:
                value = 0

            len = 100
            if value == 0:
                value = 1
            valor = value * 10000 / len
        return valor

    range = 10000
    value = property(getValue)

    def changed(self, what):
        if what[0] != self.CHANGED_SPECIFIC or what[1] == self.type:
            Converter.changed(self, what)


class spaCpuUsageMonitor(Poll, object):

    def __init__(self):
        Poll.__init__(self)
        self.__callbacks = []
        self.__curr_info = self.getCpusInfo()
        self.poll_interval = 90000

    def getCpusCount(self):
        return len(self.__curr_info) - 1

    def getCpusInfo(self):
        res = []
        try:
            fd = open('/proc/stat', 'r')
            for l in fd:
                if l.find('cpu') == 0:
                    total = busy = 0
                    tmp = l.split()
                    for i in range(1, len(tmp)):
                        tmp[i] = int(tmp[i])
                        total += tmp[i]

                    busy = total - tmp[4] - tmp[5]
                    res.append([tmp[0], total, busy])

            fd.close()
        except:
            pass

        return res

    def poll(self):
        pass

    def pollx(self):
        prev_info, self.__curr_info = self.__curr_info, self.getCpusInfo()
        info = []
        for i in range(len(self.__curr_info)):
            try:
                p = 100 * (self.__curr_info[i][2] - prev_info[i][2]) / (self.__curr_info[i][1] - prev_info[i][1])
            except ZeroDivisionError:
                p = 0

            if p == 0:
                p = 1
            info.append(p)

        return info

    def connectCallback(self, func):
        return
        if func not in self.__callbacks:
            self.__callbacks.append(func)
        if not self.poll_enabled:
            self.poll()
            self.poll_enabled = True

    def disconnectCallback(self, func):
        return
        if func in self.__callbacks:
            self.__callbacks.remove(func)
        if not len(self.__callbacks) and self.poll_enabled:
            self.poll_enabled = False


def getMemoria():
    try:
        out_lines = file('/proc/meminfo').readlines()
        totmem = 0
        freemem = 0
        for lidx in range(len(out_lines) - 1):
            tstLine = out_lines[lidx].split()
            if 'MemTotal:' in tstLine:
                MemTotal = out_lines[lidx].split()
                totmem = int(MemTotal[1])
            if 'MemFree:' in tstLine:
                MemFree = out_lines[lidx].split()
                freemem = int(MemFree[1])

        if totmem > 0:
            return (freemem, totmem)
    except:
        return (0, 0)


def getTemperatura():
    tempinfo = ''
    cret = ''
    try:
        if path.exists('/proc/stb/sensors/temp0/value'):
            f = open('/proc/stb/sensors/temp0/value', 'r')
            tempinfo = f.read()
            f.close()
        elif path.exists('/proc/stb/fp/temp_sensor'):
            f = open('/proc/stb/fp/temp_sensor', 'r')
            tempinfo = f.read()
            f.close()
        if tempinfo and int(tempinfo.replace('\n', '')) > 0:
            mark = str('\xc2\xb0')
            cret += _('System') + ': ' + tempinfo.replace('\n', '').replace(' ', '') + mark + 'C'
        tempinfo = ''
        if path.exists('/proc/stb/fp/temp_sensor_avs'):
            f = open('/proc/stb/fp/temp_sensor_avs', 'r')
            tempinfo = f.read()
            f.close()
        if tempinfo and int(tempinfo.replace('\n', '')) > 0:
            mark = str('\xc2\xb0')
            cret += _('Processor') + ': ' + tempinfo.replace('\n', '').replace(' ', '') + mark + 'C'
    except:
        pass

    if cret == '':
        cret = getTempSensor()
        if str(cret) == '0':
            cret = ''
        else:
            mark = str('\xc2\xb0')
            cret = _('System') + ': ' + str(cret) + mark + 'C'
    return cret


def devDiskInfo(ruta='/', txtini='', sidormido=False):
    if not txtini == '':
        txtini = txtini + ': '
    if sidormido and ruta == '/hdd/':
        try:
            cadret = ''
            if harddiskmanager.HDDCount():
                for hdd in harddiskmanager.HDDList():
                    if ('pci' in hdd[1].phys_path or 'ahci' in hdd[1].phys_path) and hdd[1].isSleeping() and hdd[1].max_idle_time:
                        cadret = _('Sleep')
                        break

            if not cadret == '':
                return txtini + '(' + cadret + ')'
        except:
            return ''

    try:
        stat = statvfs(ruta)
    except OSError:
        return ''

    try:
        percent = '(' + str(100 * stat.f_bavail // stat.f_blocks) + '%)'
        total = stat.f_bsize * stat.f_blocks
        free = stat.f_bfree * stat.f_bsize
        if total == 0:
            return ''
        return txtini + Humanizer(total) + ', ' + Humanizer(free) + ' ' + percent + ' ' + _('free')
    except:
        return ''


def Humanizer(size, ndec=2):
    if size < 1024:
        humansize = str(size) + ' bytes'
    elif size < 1048576:
        if ndec == 0:
            humansize = '%d Kb' % (float(size) / 1024)
        else:
            humansize = '%.2f Kb' % (float(size) / 1024)
    elif size < 1073741824:
        if ndec == 0:
            humansize = '%d Mb' % (float(size) / 1048576)
        else:
            humansize = '%.2f Mb' % (float(size) / 1048576)
    elif ndec == 0:
        humansize = '%d Gb' % (float(size) / 1073741824)
    else:
        humansize = '%.2f Gb' % (float(size) / 1073741824)
    return humansize


def ddevcaos():
    return 'kv'


def getInfoNet():
    ret = ''
    from Components.Network import iNetwork
    adapters = [(iNetwork.getFriendlyAdapterName(x), x) for x in iNetwork.getAdapterList()]
    if not adapters:
        return ''
    else:
        default_gw = None
        num_configured_if = len(iNetwork.getConfiguredAdapters())
        if num_configured_if < 2 and path.exists('/etc/default_gw'):
            unlink('/etc/default_gw')
        if path.exists('/etc/default_gw'):
            fp = file('/etc/default_gw', 'r')
            result = fp.read()
            fp.close()
            default_gw = result
        if len(adapters) == 0:
            ret = ''
        else:
            for x in adapters:
                if x[1] == default_gw:
                    default_int = True
                else:
                    default_int = False
                if iNetwork.getAdapterAttribute(x[1], 'up') is True:
                    active_int = True
                else:
                    active_int = False
                if active_int:
                    iNetwork.loadNameserverConfig()
                    ret = 'IP: ' + str(iNetwork.getAdapterAttribute(x[1], 'ip')) + ''
                    if iNetwork.getAdapterAttribute(x[1], 'dhcp'):
                        ret = ret + ' (DHCP)'
                    ippub = ''
                    if len(ippub) > 8:
                        ippub = ' - ' + _('Public IP') + ': ' + ippub + ''
                    ret = ret + ippub
                    break

        return ret.replace('[', '').replace(']', '').replace(',', '.').replace('. ', '.')


def getTempSensor():
    AktTemp = 0
    try:
        AktTemp = CurrTemp()
    except:
        return ''

    if AktTemp > 0:
        cret = '%d' % AktTemp
        return str(cret)
    else:
        return ''


def CurrTemp():
    from Components.Sensors import sensors
    m1 = 0.1
    m2 = 0.1
    ti = [0,
     0,
     0,
     0,
     0,
     0,
     0,
     0,
     0,
     0]
    templist = sensors.getSensorsList(sensors.TYPE_TEMPERATURE)
    tempcount = len(templist)
    for count in range(tempcount):
        tt = sensors.getSensorValue(count)
        ti[count] = tt
        if m1 < tt:
            mi = count
            m1 = tt

    for count in range(tempcount):
        if m2 < ti[count] and count != mi:
            m2 = ti[count]

    if m2 == 0.1:
        m2 = m1
    return (m1 + m2) / 2.0
