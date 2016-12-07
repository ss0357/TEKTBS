
import re
import visa
from time import sleep
rm = visa.ResourceManager()



class TBS2K(object):
    def __init__(self, res_name=''):

        device_list = rm.list_resources()
        tbs_list = [x for x in device_list if '0x0699::0x03C' in x]
        if res_name=='':
            res_name = tbs_list[0]
            print('found {} TBS2K scopes, connect to scope with resource name: {}'.format(\
                len(tbs_list), res_name))

        scope = rm.open_resource(res_name, open_timeout = 10)
        self.res_name = res_name
        self.idn = scope.query('*IDN?').strip()
        ret = re.match('(),(),(),CF:() FV:(); FPGA:();', self.idn)

        if ret:
            self.vendor, self.model, self.serial = ret.group(1, 2, 3)
            self.cf_version, self.firmware_version, self.FPGA_version = ret.group(4, 5, 6)
            print('connect scope success.')
            print('vendor: {}  model: {}  serial number: {}'.foramt(\
                self.vendor, self.model, self.serial))
        else:
            print('parse scope idn failed. idn='.format(self.idn))

    def send(self, message, **kargs):
        scope.write(message, **kargs)

    def query(self, message, **kargs):
        if not message.endswith('?'):
            message += '?'
        scope.query(message, **kargs)

    def send_and_query(self, msg_send, msg_query='', delay=0):
        if msg_query=='':
            msg_query = msg_send + '?'
        self.send(msg_send)
        sleep(delay)
        self.query(msg_query)

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
        return 'TBS2K: {}; {}'.format(self.res_name, self.idn)

    def autoset(self):
        self.scope << [':AUTOSET EXEC', '*OPC?']
        sleep(1)

    def defaultsetup(self):
        self.scope << ['*RST', '*OPC?']
        sleep(1)
