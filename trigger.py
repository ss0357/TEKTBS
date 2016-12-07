import time

class Trigger(object):
    '''
    usage:
        trigger.source = 'CH1'
        trigger.level = 0.5
        trigger.type = 'WIDTH'
        trigger.settings = dict(type='EDGE', source='CH2', threshold='0.3')
        trigger.settings = {'slope': 'RISE', 'source': 'CH2', 'threshold': '0.0E+0', 'type': 'EDGE'}
    '''
    def __init__(self, scope):
        self.DUT = scope
        self.scope = scope

    def config(self, **kargs):
        for att in kargs:
            cmd = 'self.{} = kargs[att]'.format(att)
            exec(cmd)
            time.sleep(0.5)

    def TriggerGetTypes(self, trigger_event, trigger_event_list = 1):
        if trigger_event_list == 1:
            trigger_event_list = self.DUT.IntrInfo['trigger_event_list']
        trigger_types_list = []

        for trigger_list in trigger_event_list:
            #PrintLog ('trigger list:{}'.format(trigger_list))
            if trigger_event in trigger_list:
                trigger_types_list.append(trigger_list)

        return trigger_types_list

    def TriggerSetupEventType(self,trigger_event, trigger_class, trigger_type, bus=['B1']):
        PrintLog('trigger_event:{0};trigger_class:{1};trigger_type:{2};bus:{3}'.format(trigger_event,trigger_class,trigger_type,bus))
        if trigger_type == 'EDGE':
            self.DUT.SetandCheck(':TRIGGER:{}:TYPE'.format(trigger_event), trigger_type)
        elif trigger_type == "CAN":
            self.DUT.SetandCheck(':TRIGGER:{}:TYPE'.format(trigger_event), trigger_class)
            self.DUT.SetandCheck(':BUS:{}:TYPE'.format(bus),trigger_type)
        elif trigger_type == "COMMUNICATION":
            self.DUT.SetandCheck(':TRIGGER:{}:TYPE'.format(trigger_event), trigger_type)
        elif trigger_type == "GLITCH":
            self.DUT.SetandCheck(':TRIGGER:{}:TYPE'.format(trigger_event), trigger_class)
            self.DUT.SetandCheck(':TRIGGER:{}:TYPE'.format(trigger_event), trigger_type)
        elif trigger_type == "I2C":
            self.DUT.SetandCheck(':TRIGGER:{}:TYPE'.format(trigger_event), trigger_class)
            self.DUT.SetandCheck(':BUS:{}:TYPE'.format(bus),trigger_type)
        elif trigger_type == "LOGIC":
            self.DUT.SetandCheck(':TRIGGER:{}:TYPE'.format(trigger_event), trigger_class)
            self.DUT.SetandCheck(':TRIGGER:{0}:{1}:CLASS'.format(trigger_event,trigger_class),trigger_type)
        elif trigger_type == "RS232" or trigger_type == "RS232C":
            self.DUT.SetandCheck(':TRIGGER:{}:TYPE'.format(trigger_event), trigger_class)
            self.DUT.SetandCheck(':BUS:{}:TYPE'.format(bus),trigger_type)
        elif trigger_type == "RUNT":
            self.DUT.SetandCheck(':TRIGGER:{}:TYPE'.format(trigger_event), trigger_class)
            self.DUT.SetandCheck(':TRIGGER:{0}:{1}:CLASS'.format(trigger_event,trigger_class),trigger_type)
        elif trigger_type == "SERIAL":
            self.DUT.SetandCheck(':TRIGGER:{}:TYPE'.format(trigger_event), trigger_class)
            self.DUT.SetandCheck(':TRIGGER:{0}:{1}:CLASS'.format(trigger_event,trigger_class),trigger_type)
        elif trigger_type == "SETHOLD":
            self.DUT.SetandCheck(':TRIGGER:{}:TYPE'.format(trigger_event), trigger_class)
            self.DUT.SetandCheck(':TRIGGER:{0}:{1}:CLASS'.format(trigger_event,trigger_class),trigger_type)
        elif trigger_type == "SPI":
            self.DUT.SetandCheck(':TRIGGER:{}:TYPE'.format(trigger_event), trigger_class)
            self.DUT.SetandCheck(':BUS:{}:TYPE'.format(bus),trigger_type)
        elif trigger_type == "TIMEOUT":
            self.DUT.SetandCheck(':TRIGGER:{}:TYPE'.format(trigger_event), trigger_class)
            self.DUT.SetandCheck(':TRIGGER:{0}:{1}:CLASS'.format(trigger_event,trigger_class),trigger_type)
        elif trigger_type == "TRANSITION":
            self.DUT.SetandCheck(':TRIGGER:{}:TYPE'.format(trigger_event), trigger_class)
            self.DUT.SetandCheck(':TRIGGER:{0}:{1}:CLASS'.format(trigger_event,trigger_class),trigger_type)
        elif trigger_type == "WIDTH":
            self.DUT.SetandCheck(':TRIGGER:{}:TYPE'.format(trigger_event), trigger_class)
            self.DUT.SetandCheck(':TRIGGER:{0}:{1}:CLASS'.format(trigger_event,trigger_class),trigger_type)
        else:
            Error ('Trigger Type is not supported, type is {}'.format(trigger_type))
            AbortTest

    def _generate_cmd_list(self):
        cmd_list = {}
        source = self.source
        cmd_list['EDGE'] = {
            'source': ':TRIGGER:A:EDGE:SOURCE',
            'slope': ':TRIGGER:A:EDGE:SLOPE',
            'threshold': ':TRIGGER:A:level'
        }
        cmd_list['WIDTH'] = {
            'source': ':TRIGGER:A:EDGE:SOURCE',
            'polarity': ':TRIGGER:A:PULSEWIDTH:POLARITY',
            'when': ':TRIGGER:A:PULSEWIDTH:WHEN',
            'width': ':TRIGGER:A:PULSEWIDTH:WIDTH',
            'lowlimit': ':TRIGGER:A:PULSEWIDTH:LOWLIMIT',
            'highlimit': ':TRIGGER:A:PULSEWIDTH:HIGHLIMIT',
        }
        cmd_list['RUNT'] = {
            'source': ':TRIGger:A:RUNT:SOUrce',
            'polarity': ':TRIGGER:A:RUNT:POLARITY',
            'when': ':TRIGGER:A:RUNT:WHEN',
            'width': ':TRIGGER:A:RUNT:WIDTH',
            'upperthreshold': ':TRIGGER:A:UPPERTHRESHOLD:'+source,
            'lowerthreshold': ':TRIGGER:A:lowerthreshold:'+source,
        }
        self.cmd_list = cmd_list

    def _update_handle(self, type):
        if type=='TRANSITION':
            self.DUT.trigger = Trigger_TRANSITION(self.scope)
        elif type=='EDGE':
            self.DUT.trigger = Trigger_EDGE(self.scope)
        elif type=='SETHOLD':
            self.DUT.trigger = Trigger_SETHOLD(self.scope)

    @property
    def type(self):
        mtype = self.DUT.Query(':TRIGger:A:TYPE')
        stype = self.DUT.Query(':TRIGger:A:PULse:CLAss')
        if mtype=='PULSE' or mtype=='LOGIC':
            return stype
        else:
            return mtype

    @type.setter
    def type(self, value):
        if value in ['WIDTH', 'RUNT', 'TRANSITION']:
            self.DUT.Send('TRIGger:A:TYPE PULSE')
            self.DUT.Send(':TRIGger:A:PULse:CLAss '+value)
        elif value in ['SETHOLD', 'BUS']:
            self.DUT.Send('TRIGger:A:TYPE LOGIC')
            self.DUT.Send(':TRIGger:A:LOGIC:CLAss '+value)
        else:
            self.DUT.Send(':TRIGger:A:TYPE '+value)
        self._update_handle(value)

    @property
    def state(self):
        return str(self.DUT.Query('TRIGger:state'))

    @property
    def level(self):
        return float(self.DUT.Query('TRIGger:A:level:'+self.source))

    @level.setter
    def level(self, value):
        self.DUT.Send('TRIGger:A:level:'+self.source+' '+str(value))

    @property
    def lower_threshold(self):
        return float(self.DUT.Query('TRIGger:A:lowerthreshold:'+self.source))

    @lower_threshold.setter
    def lower_threshold(self, value):
        self.DUT.Send('TRIGger:A:lowerthreshold:'+self.source+' '+str(value))

    @property
    def upper_threshold(self):
        return float(self.DUT.Query('TRIGger:A:upperthreshold:'+self.source))

    @upper_threshold.setter
    def upper_threshold(self, value):
        self.DUT.Send('TRIGger:A:upperthreshold:'+self.source+' '+str(value))

    @property
    def settings(self):
        self._generate_cmd_list()
        ret = {}
        type = self.type
        ret['type'] = type
        for key in self.cmd_list[type]:
            ret[key] = self.DUT << self.cmd_list[type][key]+'?'
        return ret

    @settings.setter
    def settings(self, kargs):
        self._generate_cmd_list()
        self.type = type = kargs.pop('type')
        for key in kargs:
            self.DUT << self.cmd_list[type][key]+'  '+ str(kargs[key])




class Trigger_EDGE(Trigger):

    cmd_source = ':TRIGGER:A:EDGE:SOURCE'
    cmd_slope = ':TRIGGER:A:EDGE:SLOPE'

    @property
    def source(self):
        return (self.scope << self.cmd_source+'?')
    @source.setter
    def source(self, value):
        self.scope << self.cmd_source+' '+str(value)

    @property
    def slope(self):
        return (self.scope << self.cmd_slope+'?')
    @slope.setter
    def slope(self, value):
        self.scope << self.cmd_slope+' '+str(value)


class Trigger_TRANSITION(Trigger):
    '''
    usage:
        trigger.source = 'CH1'
        trigger.slope = ''
        trigger.when = 'WIDTH'
        trigger.threshold_high = 5
        trigger.threshold_low = 1
    '''
    cmd_source = ':TRIGGER:A:TRANSITION:SOURCE'
    cmd_slope = ':TRIGGER:A:TRANSITION:POLARITY'
    cmd_when = ':TRIGGER:A:TRANSITION:WHEN'
    cmd_deltatime = ':TRIGGER:A:TRANSITION:DELTATIME'

    @property
    def source(self):
        return (self.scope << self.cmd_source+'?')
    @source.setter
    def source(self, value):
        self.scope << self.cmd_source+' '+str(value)

    @property
    def slope(self):
        return (self.scope << self.cmd_slope+'?')
    @slope.setter
    def slope(self, value):
        self.scope << self.cmd_slope+' '+str(value)

    @property
    def when(self):
        return (self.scope << self.cmd_when+'?')
    @when.setter
    def when(self, value):
        self.scope << self.cmd_when+' '+str(value)

    @property
    def deltatime(self):
        return (self.scope << self.cmd_deltatime+'?')
    @deltatime.setter
    def deltatime(self, value):
        self.scope << self.cmd_deltatime+' '+str(value)


class Trigger_SETHOLD(Trigger):

    cmd_clock_source = 'TRIGger:A:SETHold:CLOCk:SOUrce'
    cmd_clock_threshold = 'TRIGger:A:SETHold:CLOCk:THReshold'
    cmd_data_source = 'TRIGger:A:SETHold:DATa:SOUrce'
    cmd_data_threshold = 'TRIGger:A:SETHold:DATa:THReshold'
    cmd_holdtime = 'TRIGger:A:SETHold:HOLDTime'
    cmd_settime = 'TRIGger:A:SETHold:SETTime'
    cmd_slope = 'TRIGger:A:SETHold:CLOCk:EDGE'

    @property
    def slope(self):
        return (self.scope << self.cmd_slope+'?')
    @slope.setter
    def slope(self, value):
        self.scope << self.cmd_slope+' '+str(value)

    @property
    def clock_source(self):
        return (self.scope << self.cmd_clock_source+'?')
    @clock_source.setter
    def clock_source(self, value):
        self.scope << self.cmd_clock_source+' '+str(value)

    @property
    def data_source(self):
        return (self.scope << self.cmd_data_source+'?')
    @data_source.setter
    def data_source(self, value):
        self.scope << self.cmd_data_source+' '+str(value)

    @property
    def holdtime(self):
        return float(self.scope << self.cmd_holdtime+'?')
    @holdtime.setter
    def holdtime(self, value):
        self.scope << self.cmd_holdtime+' '+str(value)

    @property
    def settime(self):
        return float(self.scope << self.cmd_settime+'?')
    @settime.setter
    def settime(self, value):
        self.scope << self.cmd_settime+' '+str(value)

    @property
    def clock_threshold(self):
        return float(self.scope << self.cmd_clock_threshold+'?')
    @clock_threshold.setter
    def clock_threshold(self, value):
        self.scope << self.cmd_clock_threshold+' '+str(value)

    @property
    def data_threshold(self):
        return float(self.scope << self.cmd_data_threshold+'?')
    @data_threshold.setter
    def data_threshold(self, value):
        self.scope << self.cmd_data_threshold+' '+str(value)


def test_lib(DUT):
    DUT.trigger.type = 'EDGE'
    print(DUT.trigger.source)
    print(DUT.trigger.level)
    print(DUT.trigger.slope)
    DUT.trigger.source = 'CH2'
    DUT.trigger.level = 1.23
    DUT.trigger.slope = 'FALL'
    DUT.trigger.lower_threshld = 3.3
    DUT.trigger.upper_threshld = 0.3

    DUT.trigger.type = 'TRANSITION'
    print(DUT.trigger.source)
    print(DUT.trigger.slope)
    print(DUT.trigger.when)
    DUT.trigger.source = 'CH2'
    DUT.trigger.slope = 'FALL'
    DUT.trigger.when = 'edwed'

    DUT.trigger.type = 'SETHOLD'
    print(DUT.trigger.clock_source)
    print(DUT.trigger.clock_threshold)
    print(DUT.trigger.data_source)
    print(DUT.trigger.data_threshold)
    print(DUT.trigger.settime)
    print(DUT.trigger.holdtime)
    print(DUT.trigger.slope)
    DUT.trigger.clock_source = 'CH2'
    DUT.trigger.clock_threshold = 3
    DUT.trigger.data_source = 'CH1'
    DUT.trigger.data_threshold = 2
    DUT.trigger.settime = 100E-9
    DUT.trigger.holdtime = 200E-9
    DUT.trigger.slope = 'FALL'
