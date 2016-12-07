from pprint import pprint
from Common import *
import time

class Afg(object):
    """
    """
    def __init__(self, scope):
        self.scope = scope
        self.load_list = ['HIGHZ', 'FIFTY']
        self.func_list = ['SINE', 'SQUARE', 'PULSE', 'RAMP', 'NOISE', 'DC', 'SINC',
                          'GAUSSIAN', 'LORENTZ', 'ERISE', 'EDECAY', 'HAVERSINE', 'CARDIAC', 'ARBITRARY']
        self.parameters = {
            # ampl min, max, resolutin; freq min, max, resolution
            'SINE':     dict(ampl=[0.02, 5, 0.001], freq=[0.1, 50E6, 0.1],
                             offset=[-2.5, 2.5, 0.001], phase=[-180, 180, 0.1]),
            'SQUARE':   dict(ampl=[0.02, 5, 0.001], freq=[0.1, 25E6, 0.1], duty=[10, 90, 0.1],
                             offset=[-2.5, 2.5, 0.001], phase=[-180, 180, 0.1]),
            'PULSE':    dict(ampl=[0.02, 5, 0.001], freq=[0.1, 25E6, 0.1], width=[1E-10, ],
                             offset=[-2.5, 2.5, 0.001], phase=[-180, 180, 0.1]),
            'RAMP':     dict(ampl=[0.02, 5, 0.001], freq=[0.1, 500E3, 0.1], symm=[0, 100, 0.1],
                             offset=[-2.5, 2.5, 0.001], phase=[-180, 180, 0.1]),

            'NOISE':    dict(),
            'DC':       dict(offset=[-2.5, 2.5, 0.001]),

            'SINC':     dict(ampl=[0.02, 3, 0.001], freq=[0.1, 2E6, 0.1],
                             offset = [-2.5, 2.5, 0.001], phase = [-180, 180, 0.1]),
            'GAUSSIAN': dict(ampl=[0.02, 2.5, 0.001], freq=[0.1, 5E6, 0.1],
                             offset=[-2.5, 2.5, 0.001], phase=[-180, 180, 0.1]),
            'ERISE':    dict(ampl=[0.02, 2.5, 0.001], freq=[0.1, 5E6, 0.1],
                             offset=[-2.5, 2.5, 0.001], phase=[-180, 180, 0.1]),
            'EDECAY':   dict(ampl=[0.02, 2.5, 0.001], freq=[0.1, 5E6, 0.1],
                             offset=[-2.5, 2.5, 0.001], phase=[-180, 180, 0.1]),

            'LORENTZ':      dict(ampl=[0.02, 2.4, 0.001], freq=[0.1, 5E5, 0.1],
                                 offset=[-2.5, 2.5, 0.001], phase=[-180, 180, 0.1]),
            'HAVERSINE':    dict(ampl=[0.02, 2.4, 0.001], freq=[0.1, 5E5, 0.1],
                                 offset=[-2.5, 2.5, 0.001], phase=[-180, 180, 0.1]),

            'CARDIAC':      dict(ampl=[0.02, 5, 0.001], freq=[0.1, 5E5, 0.1]),
            'ARBITRARY':    dict(ampl=[0.02, 5, 0.001], freq=[0.1, 25E6, 0.1]),
        }

    @property
    def ampl(self):
        return float(self.scope.Query(':AFG:AMPL'))

    @ampl.setter
    def ampl(self, value):
        self.scope.SetandCheck(':AFG:AMPL', value)

    @property
    def freq(self):
        return float(self.scope.Query(':AFG:FREQ'))

    @freq.setter
    def freq(self, value):
        self.scope.SetandCheck(':AFG:FREQ', value)

    @property
    def func(self):
        return self.scope.Query(':AFG:FUNC')

    @func.setter
    def func(self, value):
        self.scope.SetandCheck(':AFG:FUNC', value.upper())

    @property
    def highlevel(self):
        return float(self.scope.Query(':AFG:HIGHLEVEL'))

    @highlevel.setter
    def highlevel(self, value):
        self.scope.SetandCheck(':AFG:HIGHLEVEL', value)

    @property
    def lowlevel(self):
        return float(self.scope.Query(':AFG:LOWLEVEL'))

    @lowlevel.setter
    def lowlevel(self, value):
        self.scope.SetandCheck(':AFG:LOWLEVEL', value)

    @property
    def offset(self):
        return float(self.scope.Query(':AFG:OFFSET'))

    @offset.setter
    def offset(self, value):
        self.scope.SetandCheck(':AFG:OFFSET', value)

    @property
    def period(self):
        return float(self.scope.Query(':AFG:PERIOD'))

    @period.setter
    def period(self, value):
        self.scope.SetandCheck(':AFG:PERIOD', value)

    @property
    def phase(self):
        return float(self.scope.Query(':AFG:PHASE'))

    @phase.setter
    def phase(self, value):
        self.scope.SetandCheck(':AFG:PHASE', value)

    @property
    def onoff(self):
        return self.scope.Query(':AFG:OUTPUT:STATE')

    @onoff.setter
    def onoff(self, value):
        self.scope.SetandCheck(':AFG:OUTPUT:STATE', value)

    @property
    def out_load(self):
        return self.scope.Query(':AFG:OUTPUT:LOAd:IMPEDance')

    @out_load.setter
    def out_load(self, value):
        self.scope.SetandCheck(':AFG:OUTPUT:LOAd:IMPEDance', value)

    @property
    def noise_onoff(self):
        return int(self.scope.Query('AFG:NOISEAdd:STATE'))

    @noise_onoff.setter
    def noise_onoff(self, value):
        self.scope.SetandCheck('AFG:NOISEAdd:STATE', value)

    @property
    def noise_percent(self):
        return float(self.scope.Query('AFG:NOISEAdd:PERCent'))

    @noise_percent.setter
    def noise_percent(self, value):
        self.scope.SetandCheck('AFG:NOISEAdd:PERCent', value)

    @property
    def pulse_width(self):
        return float(self.scope.Query('AFG:PULse:WIDth'))

    @pulse_width.setter
    def pulse_width(self, value):
        self.scope.SetandCheck('AFG:PULse:WIDth', value)

    @property
    def ramp_symm(self):
        return float(self.scope.Query('AFG:RAMP:SYMmetry'))

    @ramp_symm.setter
    def ramp_symm(self, value):
        self.scope.SetandCheck('AFG:RAMP:SYMmetry', value)

    @property
    def square_duty(self):
        return float(self.scope.Query('AFG:SQUare:DUty'))

    @square_duty.setter
    def square_duty(self, value):
        self.scope.SetandCheck('AFG:SQUare:DUty', value)

    def config(self, *pargs, **kargs):
        if not kargs:
            output = self.scope << ['header 1', ':AFG?']
            self.scope.SetandCheck('header', 0)
            pprint(output.split(';'))
        else:
            for att in kargs:
                cmd = 'self.{} = kargs[att]'.format(att)
                exec(cmd)
                time.sleep(0.5)

    @property
    def emem_numpoints(self):
        return int(self.scope << 'AFG:ARBitrary:EMEM:NUMPoints?')

    def get_emem_data(self):
        self.scope.SetandCheck('AFG:ARBitrary:EMEM:POINTS:ENCdg', 'ASCII')
        data = self.scope << 'AFG:ARBitrary:EMEM:POINTS?'
        data = [float(x) for x in data.split(',')]
        return data

    def emem_clear(self):
        self.scope.SetandCheck('AFG:ARBitrary:EMEM:POINTS:ENCdg', 'ASCII')
        self.scope.SetandCheck('AFG:ARBitrary:EMEM:POINTS', '0,0')


def test_args_range(cmd, min, max, step):
    DUT = Interfaces['DUT']
    PrintLog('test parameters range for cmd {}: min {} max {} resolution {}'.format(cmd, min, max, step))
    DUT.SetandCheck(cmd, min)
    DUT << cmd + ' ' + str(min - step)
    DUT.QueryResponse(cmd, min)
    DUT.SetandCheck(cmd, round(min+step, 10))

    DUT.SetandCheck(cmd, max)
    DUT << cmd + ' ' + str(max + step)
    DUT.QueryResponse(cmd, max)
    DUT.SetandCheck(cmd, round(max-step, 10))

    DUT.SetandCheck(cmd, max)
    DUT << cmd + ' ' + str(max - step/2.0)
    DUT.QueryResponse(cmd, max)


def adjust_scale_trigger(TDS, **kargs):
    if 'ampl' in kargs:
        ampl = kargs['ampl']
        TDS.CH1.scale, TDS.CH2.scale = ampl / 2.0, ampl / 2.0
        TDS.turn_knob('VERTSCALE1', 1)
        TDS.turn_knob('VERTSCALE2', 1)
    if 'load' in kargs and kargs['load']=='FIFTY':
        TDS.turn_knob('VERTSCALE1', -1)
        TDS.turn_knob('VERTSCALE2', -1)
    if 'freq' in kargs:
        freq = kargs['freq']
        TDS.hor_scale = 1.0 / freq / 4.0
    if 'offset' in kargs:
        offset = kargs['offset']
        offset2 = offset/TDS.CH1.scale
        TDS.CH1.position, TDS.CH2.position = -offset2, -offset2
        TDS.trigger.level = offset
    if 'func' in kargs:
        if kargs['func'] in ['SINC', 'GAUSSIAN', 'LORENTZ', 'ERISE', 'EDECAY', 'HAVERSINE']:
            TDS.trigger.level = offset2 + ampl/4.0
    time.sleep(1)


def afg_verify_wavefrom(func, ampl, freq, offset=0, load='HIGHZ', **kargs):
    DUT = Interfaces['DUT']
    TDS = Interfaces['TDS']
    AFG3K = Interfaces['WVGEN']
    PrintLog('===> verify scope AFG waveform output via limit test')
    PrintLog('===> func={}, ampl={}, freq={}, offset={}, load={}'
             .format(func, ampl, freq, offset, load))

    if func != 'ARBITRARY':
        DUT.AFG.func = func
        AFG3K.func = func
    DUT.AFG.out_load = load
    AFG3K.load = load
    DUT.AFG.config(ampl=ampl, freq=freq, offset=offset, onoff=1)
    AFG3K.config(ampl=ampl, freq=freq, offset=offset, onoff=1)

    if 'ramp_symm' in kargs:
        DUT.AFG.ramp_symm = kargs['ramp_symm']
        AFG3K.ramp_symm = kargs['ramp_symm']
    if 'square_duty' in kargs:
        DUT.AFG.square_duty = kargs['square_duty']
        AFG3K.func = 'PULSE'
        AFG3K.square_duty = kargs['square_duty']
    if 'pulse_width' in kargs:
        DUT.AFG.pulse_width = kargs['pulse_width']
        AFG3K.pulse_width = kargs['pulse_width']
    if 'arb_freq' in kargs:
        DUT.AFG.freq = kargs['arb_freq']

    adjust_scale_trigger(TDS, func=func, ampl=ampl, freq=freq, offset=offset, load=load)
    TDS.config_limit_test(150, 150)
    failed, passed, total = TDS.run_limit_test(10)
    assertEqual(failed, 0, 'verify afg waveform')



