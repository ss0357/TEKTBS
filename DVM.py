
import time

class DigVoltMeas(object):
    """
    """

    def __init__(self, scope):
        self.scope = scope
        self.mode_list = ['OFF', 'ACRMS', 'ACDCRMS', 'DC']
        self.autorange_list = ['0', '1']
        self.display_list = ['FULL', 'MINIMUM']
        self.source_list = self.scope.InstInfo['channel_list']

    def config(self, **kargs):
        for att in ['mode', 'source', 'autorange', 'display']:
            if att in kargs:
                cmd = 'self.{} = kargs[att]'.format(att)
                exec(cmd)
                time.sleep(0.5)

    def reset(self):
        self.scope << ':DVM RESET'
        time.sleep(0.1)

    @property
    def mode(self):
        return self.scope.Query(':DVM:MODE')

    @mode.setter
    def mode(self, value):
        self.scope.SetandCheck(':DVM:MODE', value)

    @property
    def source(self):
        return self.scope.Query(':DVM:SOURCE')

    @source.setter
    def source(self, value):
        self.scope.SetandCheck(':DVM:SOURCE', value)

    @property
    def autorange(self):
        return int(self.scope.Query(':DVM:autorange'))

    @autorange.setter
    def autorange(self, value):
        self.scope  << ':DVM:autorange '+str(value)

    @property
    def display(self):
        return self.scope.Query(':DVM:DISPLAYSTYle')

    @display.setter
    def display(self, value):
        self.scope.SetandCheck(':DVM:DISPLAYSTYle', value)

    @property
    def value(self):
        return float(self.scope.Query('DVM:MEASUrement:VALue'))

    @property
    def freq(self):
        return float(self.scope.Query('DVM:MEASUrement:FREQuency'))

    @property
    def his_min(self):
        return float(self.scope.Query('DVM:MEASUrement:HIStory:MINImum'))

    @property
    def his_max(self):
        return float(self.scope.Query('DVM:MEASUrement:HIStory:MAXimum'))

    @property
    def his_average(self):
        return float(self.scope.Query('DVM:MEASUrement:HIStory:AVErage'))

    @property
    def inf_min(self):
        return float(self.scope.Query('DVM:MEASUrement:INFMINimum'))

    @property
    def inf_max(self):
        return float(self.scope.Query('DVM:MEASUrement:INFMAXimum'))
