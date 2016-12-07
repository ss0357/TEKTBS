from Interface import *
from Globals import *
from afg import Afg
from DVM import DigVoltMeas
from trigger import *
import os
import re

def check_USB_driver():
    def _deco(func):
        def _func(self, *args):
            if not self.has_USB_driver():
                PrintLog('***** operation need insert USB driver *****')
                AbortTest()
            func(self, *args)
        return _func
    return _deco


class TBS2K(Interface):
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

        self.channels = int(self.model[-1])
        self.powerup = self.Query('DEVELOP:NUMPOWERUP')
        self.hor_divs, self.vert_divs = 15, 10
        self.hor_pixels, vert_pixels = 800, 600

        self.InstInfo = InstrumentInfo(self)
        self.BusInfo = Bus(self)
        self.CH1, self.CH2 = Channel(self, 'CH1'), Channel(self, 'CH2')
        self.CH = {'CH1': self.CH1, 'CH2': self.CH2}
        if self.channels > 2:
            self.CH3, self.CH4 = Channel(self, 'CH3'), Channel(self, 'CH4')
            self.CH['CH3'] = self.CH3
            self.CH['CH4'] = self.CH4
        self.REF1, self.REF2 = Channel(self, 'REF1'), Channel(self, 'REF2')
        self.CH['REF1'] = self.REF1
        self.CH['REF2'] = self.REF2
        self.MATH = Math(self, 'MATH')
        self.CH['MATH'] = self.MATH
        self.trigger = Trigger(self)
        self.DVM = DigVoltMeas(self)
        self.AFG = Afg(self)
        self.zoom = Zoom(self)

    def initialize(self):
        self.DUTOptions()
        self.TEKsecure()

    def DUTOptions(self):
        # Print Configuration Information
        PrintLog("-------------------------------------------------------------------------")
        PrintLog("                         Configuration Information")
        PrintLog("")
        PrintLog("Make/Model: {0}/{1}; FV:{2}".format(self.make, self.model, self.fw_ver))
        PrintLog("id: %s" % self.dev_id)
        PrintLog(u"num of power up: {0:s}".format(self.powerup))
        PrintLog("-------------------------------------------------------------------------")
        PrintLog("")

    def TEKsecure(self):
        self.SetandCheck('AUTOSET:ENABLE', 1)
        self.Send('*RST')
        self.Query('*OPC')
        for i in range(1, self.channels + 1):
            self.Send('CH%d:PROBE:GAIN 1' % i)
        self.Send(':DESE 255;*ESE 0;*SRE 0;*PSC 1')
        self.Send('*CLS')
        self.Query('*OPC')

    def SetVerticalGain(self, gain):
        for i in range(1, self.channels + 1):
            self.Send('CH%d:PROBE:GAIN 1' % i)


    def CheckAndClearErrorLog(self):
        PrintLog('CheckAndClearErrorLog')
        return
        self << "PASSWORD INTEKRITY"
        self << "PASSWORD TRESPASS"

        # Print the error log entries
        num_errors = int(self.Query('ERRLOG:NUMENT'))
        if num_errors > 0:
            Warn('{} error(s) was found in the ERROR LOG.'.format(num_errors))
            Error(self.Query("ERRLOG:FIRST"))
            for i in range(1, num_errors):
                Error(self.Query("ERRLOG:NEXT"))

        # Clear the error log
        PrintLog ("Note: Clearing the ERROR LOG")
        self  << "ERRLOG CLEAR"

        # check memory and cpu useage
        self << "CPUMEMTest:CPUTEST"
        self << "CPUMEMTest:MEMTEST"
        time.sleep(3)
        cpu_ulpp = self.Query('CPUMEMTest:CPUULPP')
        cpu_tekapp = self.Query('CPUMEMTest:CPUTEKAPP')
        mem_free = self.Query('CPUMEMTest:MEMFREE').split('K free')[0]

        if float(cpu_ulpp) >= 40:
            Warn('cpu useage of ULPP out of range: ' + cpu_ulpp)
        if float(cpu_tekapp) >= 70:
            Warn('cpu useage of tekapp out of range: ' + cpu_tekapp)
        if float(mem_free) <= 5000:
            Warn('free memory less than 5M: ' + mem_free)

    def ClearInstrumentErrors(self):
        retVal = 0
        esrcount = self.Query('*ESR')
        if esrcount < 0:
            Error ('*ESR? query failed!')
            retVal = esrcount
        elif esrcount > 0:
            allevents = self.Query('Allev')
            if allevents == -1:
                Error ('ALLEV? query failed!')
                retVal = allevents
            else:
                PrintLog ('ALLEV? retrun {}'.format(allevents))
        else:
            retVal = esrcount
        return retVal

    def WaitForOneTrigger(self, delay=0.6):
        for i in list(range(10)):
            sleep(delay)
            if self.trigger_state() == 'TRIGGER':
                return 1
        return 0

    def VerifyNoTrigger(self):
        sleep(0.5)
        for i in list(range(10)):
            sleep(0.2)
            if self.trigger_state() == 'TRIGGER':
                return 0
        return 1

    def TriggerSetupSingle(self, single=1):
        self.SetandCheck(':ACQUIRE:STATE', 0)

        if single == 0:
            self.SetandCheck(':ACQUIRE:STOPAFTER', 'RUNSTOP')
        else:
            self.SetandCheck(':TRIGGER:A:MODE', 'NORMAL')
            self.SetandCheck(':ACQUIRE:STOPAFTER', 'SEQUENCE')
        self.SetandCheck('DESE', 1)
        self.SetandCheck('*ESE', 1)
        self.SetandCheck('*SRE', 32)
        self.Send("*WAI;*CLS;:ACQUIRE:STATE 1;*OPC")

    def TriggerInstrumentSetup(self, horizontal_scale, horizontal_resolution, vertical_scale, vertical_position, cursor_value, probe_gain=-1):
        self << "*RST"
        self << "*CLS"
        self.SetVerticalGain(1.0)
        self.SetandCheck(':HORIZONTAL:MAIN:SCALE', horizontal_scale)
        self.SetandCheck(':HORIZONTAL:RESOLUTION', horizontal_resolution)
        self.SetandCheck(':ZOOM:MODE', 1)
        for channel in range(1, self.channels):
            self.SetandCheck(':SELECT:CH%d' % channel, 1)
            if probe_gain != -1:
                self.SetandCheck(':CH%d:PROBE:GAIN' % channel, probe_gain)
            self.SetandCheck(':CH%d:SCALE' % channel, vertical_scale)
            self.SetandCheck(':CH%d:POSITION' % channel, vertical_position)
            self.Send(':ZOOM:ZOOM:HORIZONTAL:SCALE {}'.format(zoom_scale))
        self.SetandCheck(':MEASUREMENT:MEAS1:TYPE ', 'RISE')
        self.SetandCheck(':MEASUREMENT:MEAS1:STATE ', 1)
        self.SetandCheck(':MEASUREMENT:MEAS2:TYPE', 'FALL')
        self.SetandCheck(':MEASUREMENT:MEAS2:STATE', 1)
        self.SetandCheck(':MEASUREMENT:GATING', 'CURSOR')

        self.Send(':CURSOR:VBARS:POSITION1 {}'.format(-cursor_value))
        self.Send(':CURSOR:VBARS:POSITION2 {}'.format(cursor_value))
        self.SetandCheck(':ACQUIRE:STOPAFTER', 'SEQUENCE')
        self.SetandCheck(':ACQUIRE:STATE', 0)


    def TriggerTestValues(self, trigger_parameters, testing_constraints):
        minimum = trigger_parameters[1]
        maximum = trigger_parameters[2]
        resolution = trigger_parameters[3]

        trigger_list = [minimum,maximum,0]
        for test_cons in testing_constraints:
            key = test_cons[0]
            value = test_cons[1]
            base_value = 0.0
            base_resolution = 1.0
            if key == 'min' or key == 'minimum':
                base_value = minimum
                base_resolution = resolution
            elif key == 'max' or key == 'maximum':
                base_value = maximum
                base_resolution = resolution
            trigger_list.append(base_value+value*base_resolution)
        return trigger_list



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

    def check_udisk(self):
        space = float(self.Query('FILESystem:FREESpace?'))
        if space < 100E6:
            PrintLog(' *** not found USB driver or space < 100M *** ')
            AbortTest()

    def erase_udisk(self):
        self.SetandCheck(':FILESYSTEM:CWD', '\"{}\"'.format(self.InstInfo['USB_driver']))
        self.Send(':FILESYSTEM:DELETE \'*.*\'')
        self.Query('*OPC')
        sleep(1)
        filelist = self << 'FILESystem:dir?'
        if filelist != '\"\"':
            PrintLog(' *** delete all files on USB driver failed *** ')
            AbortTest()

    def check_erase_udisk(self):
        self.SetandCheck(':FILESYSTEM:CWD', '\"{}\"'.format(self.InstInfo['USB_driver']))
        self.check_udisk()
        self.erase_udisk()

    def check_file_exist(self, filename):
        filelist = self << 'FILESystem:dir?'
        filelist = filelist.split(',')
        filelist = [x.strip('\"') for x in filelist]
        return (filename in filelist)

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

    def turn_knob(self, knob, times=1, single=True):
        if single:
            self << ":FPANEL:TURN {},{}".format(knob, times)
            time.sleep(1)
        else:
            click = int(times / abs(times))
            for i in range(abs(times)):
                self.Send(":FPANEL:TURN {},{}".format(knob, click))
                sleep(0.1)

    def query_esr(self):
        esr = int(self.Query('*ESR'))
        allev = self.Query('ALLEV')
        allev2 = re.findall('\d+,\".*?\"', allev)
        allev = {}
        for event in allev2:
            ret = re.match('(\d+),\"(.*)\"', event)
            key = ret.group(1)
            value = ret.group(2)
            allev[key] = value
        return allev

    def save_setup(self, num):
        if type(num) is int:
            self << [':SAVE:SETUP {}'.format(num), '*OPC?']
        else:
            self << [':SAVE:SETUP \"{}\"'.format(num), '*OPC?']

    def recall_setup(self, num):
        if type(num) is int:
            self << [':RECALL:SETUP {}'.format(num), '*OPC?']
        else:
            self << [':RECALL:SETUP \"{}\"'.format(num), '*OPC?']

    def get_setup(self, group=[]):
        setup = {}
        set = self << 'SET?'
        for section in set.split(';:')[1:]:
            header = section.split(';')[0].split(' ')[0].split(':')[0]
            if group and header not in group:
                continue
            for config in section.split(';'):
                key, value = config.split(' ')
                if config.startswith(header):
                    setup[':'+key] = value
                else:
                    setup[':'+header+':'+key] = value
        self.setup = setup
        return setup

    def save_waveform(self, src, dst):
        if dst.upper().endswith('CSV'):
            self << ':SAVE:WAVEFORM:FILEFORMAT SPREADSheet'
            dst = '\'' + dst + '\''
        if dst.upper().endswith('ISF'):
            self << ':SAVE:WAVEFORM:FILEFORMAT INTERNAL'
            dst = '\'' + dst + '\''
        self << [':SAVE:WAVEFORM {},{}'.format(src, dst), '*OPC?']

    def recall_waveform(self, src, dst):
        if src.upper().endswith('CSV') or src.upper().endswith('ISF'):
            src = '\'' + src + '\''
        self << [':RECALL:WAVEFORM {},{}'.format(src, dst), '*OPC?']

    def get_volt(self, chan, **kargs):
        self.Send('DATA:SOURCE '+chan)
        self.Send(':DATA:ENCDG ASCII')
        ymult = float(self.Query(':WFMOUTPRE:YMULT'))

        if 'time' in kargs:
            xzero = float(self.Query(':WFMOUTPRE:XZERO'))
            xincr = float(self.Query(':WFMOUTPRE:XINCR'))
            point = int((kargs['time']-xzero)/xincr)
        if 'point' in kargs:
            point = kargs['point']

        self.Send('DATA:START '+ str(point))
        self.Send('DATA:STOP '+ str(point))
        return int(self.Query(':CURVE?'))*ymult

    def reboot(self):
        pass

    def curve(self, source, **kargs):
        self.SetandCheck(':SELECT:{}'.format(source), 1)
        self.SetandCheck(':DATA:ENCDG', 'ASCII')
        self.SetandCheck(':DATA:SOURCE', source)
        if 'start' in kargs:
            self.SetandCheck(':DATA:START', kargs['start'])
        if 'stop' in kargs:
            self.SetandCheck(':DATA:STOP', kargs['stop'])
        if 'stop' in kargs:
            self.SetandCheck(':DATA:STOP', kargs['stop'])
        if 'encdg' in kargs:
            self.SetandCheck(':DATA:encdg', kargs['encdg'])
        if 'width' in kargs:
            self.SetandCheck(':DATA:WIDTH', kargs['WIDTH'])
        data = self << 'curve?'
        data = [int(x) for x in data.split(',')]
        return data

    @property
    def hor_scale(self):
        return float(self.Query(':HORIZONTAL:SCALE'))

    @hor_scale.setter
    def hor_scale(self, value):
        self.Send(':HORIZONTAL:SCALE ' + str(value))

    @property
    def hor_delay(self):
        return float(self.Query(':HORIZONTAL:DELAY:TIME'))

    @hor_delay.setter
    def hor_delay(self, value):
        self.Send(':HORIZONTAL:DELAY:TIME ' + str(value))

    @property
    def acq_mode(self):
        return self.Query(':ACQUIRE:MODE')

    @acq_mode.setter
    def acq_mode(self, value):
        self.Send(':ACQUIRE:MODE ' + str(value))

    @property
    def acq_rec_len(self):
        return int(self.Query(':horizontal:recordlength'))

    @acq_rec_len.setter
    def acq_rec_len(self, value):
        self.Send(':horizontal:recordlength ' + str(value))

    @property
    def acq_state(self):
        return self.Query(':ACQUIRE:STATE')

    @acq_state.setter
    def acq_state(self, value):
        self.Send(':ACQUIRE:STATE ' + str(value))

    @property
    def acq_stopafter(self):
        return self.Query(':ACQUIRE:STOPAFTER')

    @acq_stopafter.setter
    def acq_stopafter(self, value):
        self.Send(':ACQUIRE:STOPAFTER ' + str(value))

    def trigger_state(self):
        return self.Query('TRIGGER:STATE')

    def run_single(self, timeout=10):
        self.acq_state = 0
        self.acq_stopafter = 'SEQUENCE'
        self.acq_state = 1
        self.Query('*OPC', timeout=timeout)

    @property
    def display_format(self):
        return self.Query(':DISPLAY:FORMAT')

    @display_format.setter
    def display_format(self, value):
        self.SetandCheck(':DISPLAY:FORMAT', value)

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
        return 'TBS2K: {}; {}'.format(self.resource_expr, self.dev_id)


class InstrumentInfo(object):
    info = {}

    def __init__(self, scope):
        self.DUT = scope
        self.info['acqmode_list'] = ['SAMPLE', 'PEAKDETECT', 'HIRES''AVERAGE']
        self.info['total_channels'] = self.DUT.channels
        self.info['channel_list'] = ['CH'+str(i) for i in range(1, self.DUT.channels+1)]
        self.info['ref_list'] = ['REF1', 'REF2']
        self.info['reclength_list'] = [2000, 20e3, 200e3, 2e6, 20e6]
        self.info['horizontal_scale'] = [100.0, 40.0, 20.0, 10.0, 4.0, 2.0, 1.0, 400e-3, 200e-3, 100e-3, 40e-3,
                                         20e-3, 10e-3, 4e-3, 2e-3, 1e-3, 400e-6, 200e-6, 100e-6, 40e-6, 20e-6,
                                        10e-6, 4e-6, 2e-6, 1e-6, 400e-9, 200e-9, 100e-9, 40e-9, 20e-9, 10e-9, 4e-9]
        if self.DUT.Is200MHz:
            self.info['horizontal_scale'].append(2e-9)

        if self.DUT.model.startswith('TBS2'):
            self.info['USB_driver'] = 'usb0/'
        elif self.DUT.model.startswith('MDO'):
            self.info['USB_driver'] = 'E:/'


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

class Math(object):

    def __init__(self, scope, name):

        self.DUT = scope
        self.name = name

    @property
    def onoff(self):
        return float(self.DUT.Query(':SELECT:' + self.name))

    @onoff.setter
    def onoff(self, value):
        self.DUT.Send(":SELECT:{} {}".format(self.name, value))



class Zoom(object):

    cmd_onoff = ':ZOOM:STATE'
    cmd_scale = ':ZOOM:ZOOM1:SCALE'
    cmd_factor = ':ZOOM:ZOOM1:FACTOR'
    cmd_position = 'ZOOM:ZOOM1:POSITION'

    def __init__(self, scope):
        self.DUT = scope

    @property
    def onoff(self):
        return int(self.DUT.Query(self.cmd_onoff))

    @onoff.setter
    def onoff(self, value):
        self.DUT.Send(self.cmd_onoff+' '+str(value))

    @property
    def scale(self):
        return int(self.DUT.Query(self.cmd_scale))

    @scale.setter
    def scale(self, value):
        self.DUT.Send(self.cmd_scale + ' ' + str(value))

    @property
    def position(self):
        return float(self.DUT.Query(self.cmd_position))

    @position.setter
    def position(self, value):
        self.DUT.Send(self.cmd_position + ' ' + str(value))

    @property
    def factor(self):
        return float(self.DUT.Query(self.cmd_factor))

    @factor.setter
    def factor(self, value):
        self.scale = self.DUT.hor_scale/float(value)




class Bus(object):

    businfo = {}
    def __init__(self,scope):
        self.DUT = scope
        self.businfo['total_digital_channels'] = 16
        self.businfo['total_bus'] = 2
        self.businfo['bus_list'] = ['B1','B2']
        self.businfo['bus_display_types'] = ['BUS', 'BOTH']

        self.businfo['default_bitrate'] = 500000
        self.businfo['default_sample_pt'] = 50
        self.businfo['default_probe_pt'] = 'CANH'

        self.businfo['can_bit_rates_default'] = 50000
        self.businfo['can_bit_rates_list'] = [50000, 62500, 83330, 92240, 100000, 125000, 250000, 500000, 800000, 1000000]
        self.businfo['can_probe_types_list'] = ['CANL', 'RX', 'TX', 'CANH', 'DIFFERENTIAL']
        self.businfo['can_frame_types_list'] = ['DATA', 'REMOTE', 'ERROR', 'OVERLOAD']


        self.businfo['trigger_can_identifier_mode_list'] = ['STANDARD', 'EXTENDED']


    def InvertBit(self, pattern):
        inverted_pattern = ''
        string_length = len(pattern)
        for index in list(range(string_length)):
            bit = pattern[index]
            if bit == '1':
                invert_bit = '0'
            elif bit == '0':
                invert_bit = '1'
            else:
                Error ('Unknown bit: {}; expect 1 or 0'.format(bit))
                AbortTest()
            inverted_pattern = inverted_pattern+invert_bit
        return inverted_pattern

    def build_can_waveform_marker(self, output_file,pattern,pad_bit):
        AFG3K = Interfaces['WVGEN']
        pattern = AFG3K.AFGPatternPad(pattern, 0, pad_bit, 200)
        AFG3K.AFGGeneraterBusFile(output_file,pattern)
        return len(pattern)

    def SaveAndRetrieveEventTable(self, bus,  destination_filename):
        '''################################################################################
        #
        #  Procedure: SaveAndRetrieveEventTable
        #
        #  Description:
        #      Attempts to save the event table for the specified bus waveform to
        #      a file on the first available instrument media slot. If no media is
        #      installed or the save operation fails, -1 is returned.
        #
        #      Once the event table is saved to instrument media, it is then transferred
        #      to the specified file in REGRESSION_TEST_LOGS.
        #
        #      Upon success, the full path name to the saved local file is returned.
        #      If unable to save the event table, -1 is returned.
        #
        #  Return:
        #      Full path to saved event table or -1 if error.
        #
        ################################################################################'''
        instrument_file = '{}.CSV'.format(bus)
        self.DUT.SetandCheck('BUS:{}:state'.format(bus), 1)
        self.DUT.Send(':SAVE:EVENTTABLE:BUS{0} \"{1}\"'.format(bus[1], instrument_file))
        sleep(6)
        self.DUT.SaveTimeout(30)
        self.DUT.Send(':FILESYSTEM:READFILE \"{0}\"'.format(instrument_file))
        destination_filename_root = destination_filename
        PrintLog ('destination_filename_root:{}'.format(destination_filename_root))
        self.DUT.Read(file=destination_filename_root)
        self.DUT.RestoreTimeout()
        if os.path.isfile(destination_filename_root):
            return destination_filename_root
        else:
            return -1

    def ParseCANPacket(self, eventRecord):
        '''#################################################################################
        #
        #  FUNCTION NAME: CANBusVerifyDecodedData
        #
        #  DESCRIPTION:
        #      This procedure will retrieve the decoded data from the scope and
        #      compare it to the desired data entered as an argument
        #
        #  ARGUMENTS: Takes the Hexadecimal desired value as an argument
        #
        #  RETURN:  Returns 1 for succes 0 for failure
        #
        #  CAN event table output:
        #
        #   "Tektronix MDO3102, version v0.02048, serial number PQ000022"
        #  "Bus Definition: CAN"
        # Time, Identifier, DLC, Data, CRC, Missing Ack
        # -1.200000e-06, 18181818, 7, F1  F2  F3  F4  F5  F6  F7 , 5F9B,
        #
        #
        #################################################################################'''
        time_stamp,identifier,DLC,data,CRC,missing_ack_flag = eventRecord.split(',')
        time_stamp = re.sub('[\t+]| +', '',time_stamp)
        identifier = re.sub('[\t+]| +', '',identifier)
        DLC = re.sub('[\t+]| +', '',DLC)
        data = re.sub('[\t+]| +', '',data)
        CRC =  re.sub('[\t+]| +', '',CRC)
        missing_ack_flag = re.sub('[\t+]| +', '',missing_ack_flag)
        PrintLog('ParseCANPacket:{0},{1},{2},{3},{4},{5}'.format(time_stamp,identifier,DLC,data,CRC,missing_ack_flag))
        return [time_stamp, identifier, DLC, data, CRC, missing_ack_flag]



    def ReadFirstEventRecord(self, event_table_filepath, bus_type):
        '''################################################################################
        #
        #  Procedure: ReadFirstEventRecord
        #
        #  Description:
        #      Open the Event table stored in the filepath passed in return the
        #      first data record. Also checks if the PC event table is the one
        #      we intended
        #
        #  Sample contents of Event table:
        #
        #     "Tektronix MSO4054, version v1.36005, serial number PQ10005"
        #     "Bus Definition: PARALLEL"
        #     Time, Data
        #     -5.000000e-04, C
        #     -4.960000e-04, 4
        #     -4.959000e-04, 6
        #     .
        #     .
        #     .
        #     4.540000e-04, 1
        #     4.541000e-04, 9
        #     4.790000e-04, 8
        #     4.791000e-04, C
        #
        #  Return:
        #      Time of the matching packet
        #
        ################################################################################'''
        event_record = ''
        event_time = ''
        read_status = "data-read"
        try:
            file_id = open(event_table_filepath, 'r')
        except IOError:
            Error ("Could not open: {0}".format(event_table_filepath))
            read_status = 'unable-open-file'
            # Skip first line
        if read_status == "data-read":

            event_record = file_id.readline()
            PrintLog('EV_rec:{}'.format(event_record))
            # Second line is checked for correct Bus type
            event_record = file_id.readline()
            PrintLog('EV_rec:{0},{1}'.format(event_record,bus_type))
            # Verfiy passed in $bus_type is found in second line
            if re.search(bus_type,event_record) is not None:
                # Get Header line for this bus type, FOR now this is skipped
                event_record = file_id.readline()
                PrintLog('EV_rec:{}'.format(event_record))
                # Get first line of event table data
                event_record = file_id.readline()
                PrintLog('EV_rec:{}'.format(event_record))
                if event_record == '':
                    file_id.close()
                    read_status = 'no-data'
                else:
                    fields = event_record.split(',')
                    event_time = fields[0]
                    read_status = 'data-read'
            else:
                read_status = 'wrong-bus-type'
        return [read_status, event_time, event_record]

    def CANBusVerifyDecodedData(self, event_table_filepath, desired_data_values):
        '''#################################################################################
        #
        #  FUNCTION NAME: CANBusVerifyDecodedData
        #
        #  DESCRIPTION:
        #      This procedure will retrieve the decoded data from the scope and
        #      compare it to the desired data entered as an argument
        #
        #  ARGUMENTS: Takes the Hexadecimal desired value as an argument
        #
        #  RETURN:  Returns 1 for succes 0 for failure
        #
        #  CAN event table output:
        #
        #   "Tektronix MDO3102, version v0.02048, serial number PQ000022"
        #  "Bus Definition: CAN"
        # Time, Identifier, DLC, Data, CRC, Missing Ack
        # -1.200000e-06, 18181818, 7, F1  F2  F3  F4  F5  F6  F7 , 5F9B,
        #
        #
        ############################################################################   '''
        match_status = 0
        expected_time_stamp, expected_identifier, expected_DLC, expected_data, expected_CRC, expected_missing_ack_flag  = self.ParseCANPacket (desired_data_values)
        read_status, event_time, event_record = self.ReadFirstEventRecord(event_table_filepath, "CAN")
        PrintLog('pkt: read_status:{0}, event_time{1},event_record{2}'.format(read_status, event_time, event_record))
        if read_status == 'data-read':
            actual_time_stamp,actual_identifier,actual_DLC,actual_data,actual_CRC,actual_missing_ack_flag = self.ParseCANPacket(event_record)
            match_status = 1
            if expected_identifier != actual_identifier:
                match_status = 0
                PrintLog('Identifier mismatch: expected_identifier{0} != actual_identifier {1}'.format(expected_identifier,actual_identifier))
            if expected_DLC != actual_DLC:
                match_status = 0
                PrintLog('DLC mismatch: expected_DLC {0} != actual_DLC {1}'.format(expected_DLC,actual_DLC))
            if expected_data != actual_data:
                match_status = 0
                PrintLog('Data mismatch: expected_data {0} !=  actual_data {1}'.format(expected_data,actual_data))
            if expected_CRC != actual_CRC:
                match_status = 0
                PrintLog('CRC mismatch: expected_CRC {0}!= actual_CRC {1}'.format(expected_CRC,actual_CRC))
            #if expected_missing_ack_flag != actual_missing_ack_flag:
            #    match_status = 0
            #    PrintLog('Missing ACK flag mismatch: expected_missing_ack_flag {0} != actual_missing_ack_flag {1}'.format(expected_missing_ack_flag,actual_missing_ack_flag))
        else:
            PrintLog('Event table reading error:{}'.format(read_status))
        return match_status













    def __getitem__(self, key):
        return self.businfo[key]
