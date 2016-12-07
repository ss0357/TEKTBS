from Interface import *

class TDS2K(Interface):
    def __init__(self, visaResourceName):
        Interface.__init__(self, visaResourceName)
        self.Send("PASSWORD PITBULL")
        self.Send("PASSWORD INTEKRITY")
        self.Send(":HEADER OFF;:VERBOSE ON")
        dev_id = self.Query("*IDN").split(',')
        self.dev_id = dev_id
        self.make, self.model, self.serial = tuple(dev_id[0:3])
        self.fw_ver = dev_id[-1].split(' ')[1].split(':')[1]
        self.cf = dev_id[-1].split(' ')[0].split(':')[1]

        if self.model[-1] in 'ABCD':
            self.channels = int(self.model[-2])
        else:
            self.channels = int(self.model[-1])

        self.InstInfo = InstrumentInfo(self)
        self.CH1, self.CH2 = Channel(self, 'CH1'), Channel(self, 'CH2')
        self.CH = {'CH1': self.CH1, 'CH2': self.CH2}
        if self.channels > 2:
            self.CH3, self.CH4 = Channel(self, 'CH3'), Channel(self, 'CH4')
            self.CH['CH3'] = self.CH3
            self.CH['CH4'] = self.CH4
        self.trigger = Trigger(self)

        self.defaultsetup()
        self << [':SELECT:CH1 1', ':CH1:PROBE 1', ':CH1:POSITION 0']
        self << [':SELECT:CH2 1', ':CH2:PROBE 1', ':CH2:POSITION 0']

    def Is2CH(self):
        return self.channels == 2

    def Is4CH(self):
        return self.channels == 4

    def Is200MHz(self):
        return int(self.model[-3]) == 2

    def Is100MHz(self):
        return int(self.model[-3]) == 1

    def Is70MHz(self):
        return int(self.model[-2]) == 7

    def autoset(self):
        self.Send(':AUTOSET EXEC')
        self.Query('*OPC')
        sleep(1)

    def defaultsetup(self):
        self.Send('*RST')
        self.Query('*OPC')
        sleep(1)

    def press_button(self, button, times=1):
        for i in range(times):
            self.Send(":FPANEL:PRESS " + button)
            sleep(1)

    def turn_knob(self, knob, times):
        click = int(times / abs(times))
        for i in range(abs(times)):
            self.Send(":FPANEL:TURN {},{}".format(knob, click))
            sleep(0.1)

    def query_esr(self):
        esr = int(self.Query('*ESR'))
        allev = self.Query('ALLEV')
        allev2 = allev.split(',')
        allev = {}
        for key, value in zip(allev2[::2], allev2[1::2]):
            allev[int(key)] = value

    def get_measurement(self, src, mtype, src2=''):
        self << 'MEASUrement:IMMed:SOUrce ' + src
        self << 'MEASUrement:IMMed:TYPe ' + mtype
        time.sleep(2)
        return float(self << 'MEASUrement:IMMed:VALue?')

    def config_limit_test(self, tol_vert, tol_hor):
        PrintLog('config limit test on TDS:')

        self.Send('LIMit:SOUrce ', 'CH1')
        self.Send('LIMit:TEMPLate:SOUrce ' + 'CH2')
        self.Send('LIMit:TEMPLate:DESTination ' + 'REFA')
        self.Send('LIMit:TEMPLate:TOLerance:HORizontal ' + str(tol_hor))
        self.Send('LIMit:TEMPLate:TOLerance:VERTical ' + str(tol_vert))
        self << ['LIMit:TEMPLate APPLY', '*OPC']
        self.Send(':SELECT:REFA ' + '1')

    def run_limit_test(self, tt=10):
        self << 'LIMIT:STATE ON'
        time.sleep(tt)
        self << 'LIMIT:STATE OFF'
        time.sleep(1)
        result = self << ':LIMIT:RESULT?'
        return [int(x) for x in result.split(';')]



    @property
    def hor_scale(self):
        return float(self.Query(':HORIZONTAL:SCALE'))

    @hor_scale.setter
    def hor_scale(self, value):
        self.Send(':HORIZONTAL:SCALE ' + str(value))

    def __lshift__(self, args):
        if type(args) == str:
            args = (args,)
        for cmd in args:
            if cmd[-1] == '?':
                #sleep(self.query_delay)
                ret = self.Query(cmd)
            else:
                ret = self.Send(cmd)
        return ret

    def __repr__(self):
        return 'TDS2K: {}; {}'.format(self.resource_expr, self.dev_id)

    def __del__(self):
        self.close()


class InstrumentInfo(object):
    info = {}

    def __init__(self, scope):
        self.DUT = scope
        self.info['acqmode_list'] = ['SAMPLE', 'PEAKDETECT', 'AVERAGE']
        self.info['channel_list'] = []
        self.info['reclength_list'] = [2000, 20e3, 200e3, 2e6, 20e6]

    def __getitem__(self, key):
        return self.info[key]


class Channel(object):

    def __init__(self, scope, name):

        self.DUT = scope
        self.name = name

    @property
    def onoff(self):
        return float(self.DUT.Query(':SELECT:' + self.name))

    @onoff.setter
    def onoff(self, value):
        self.DUT.Send(":SELECT:{} {}".format(self.name, value))

    @property
    def scale(self):
        return float(self.DUT.Query(self.name + ":SCALE"))

    @scale.setter
    def scale(self, value):
        self.DUT.Send(":{}:SCALE {}".format(self.name, value))

    @property
    def position(self):
        return float(self.DUT.Query(self.name + ":POSITION"))

    @position.setter
    def position(self, value):
        self.DUT.Send(":{}:POSITION {}".format(self.name, value))


class Trigger(object):

    def __init__(self, scope):

        self.DUT = scope

    @property
    def source(self):
        return self.DUT.Query('TRIGger:A:EDGE:SOUrce')

    @source.setter
    def source(self, value):
        self.DUT.Send('TRIGger:A:EDGE:SOUrce ' + str(value))

    @property
    def level(self):
        return float(self.DUT.Query('TRIGger:MAIN:level'))

    @level.setter
    def level(self, value):
        self.DUT.Send('TRIGger:MAIN:level ' + str(value))

