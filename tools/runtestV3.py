# -*- coding:utf-8 -*-

import os
import sys
import re
import visa
import time
import subprocess
import requests
import logging
import shutil
import psutil
import telnetlib
import configparser
import threading

fthinit_str = r'''
    @ECHO OFF
    PATH %windir%\system32;%windir%;%windir%\System32\Wbem

    SET FTHROOT={0}
    SET PATH=%PATH%;%FTHROOT%
    SET PATH=%PATH%;%FTHROOT%\Tcl\bin
    SET PATH=%PATH%;%FTHROOT%\Tcl\lib\Expect5.43
    SET PATH=%PATH%;%FTHROOT%\DOS_UTIL
    SET PATH=%PATH%;%FTHROOT%\fth_lib
    SET PATH=%PATH%;%FTHROOT%\perl\bin
    SET PATH=%PATH%;%FTHROOT%\Python
    SET TCL_LIBRARY=%FTHROOT%\Tcl\lib\tcl8.5
'''

fthinit_str_55 = r'''
    @ECHO OFF
    PATH %windir%\system32;%windir%;%windir%\System32\Wbem
    SET FTHROOT={0}
    SET PATH=%PATH%;%FTHROOT%\perl\bin
    SET PATH=%PATH%;%FTHROOT%\EXPECT-5.21\BIN
    SET PATH=%PATH%;%FTHROOT%\EXPECT-5.21\LIB
    SET PATH=%PATH%;%FTHROOT%
    SET PATH=%PATH%;%FTHROOT%\DOS_UTIL
    SET PATH=%PATH%;%FTHROOT%\FTH_LIB
    SET PATH=%PATH%;%FTHROOT%\Tcl83\bin
    SET PATH=%PATH%;%FTHROOT%\Tcl85\bin
    SET PATH=%PATH%;%FTHROOT%\..\tp4
    SET PATH=%PATH%;%FTHROOT%\..\Stress
    SET TCL_LIBRARY=%FTHROOT%\Expect-5.21\lib\tcl8.0
'''

functest_str = r'''
    Call runtest.bat -type automatic {0}
    CALL extract_summary.bat runtest.transcript > summary.txt
    CALL format_summary.bat
    CALL copy summary.txt summary_analysis.txt
    CALL copy runtest.transcript runtest.transcript.save
    Call extract_errors.bat runtest.transcript -errors > failError.txt
    Call extract_errors.bat runtest.transcript -fails >> failError.txt
'''
functest_str_2 = r'''
    Call runtest.bat -list -type automatic {0} | grep 'is in $REGRESSION_TEST_ROOT' -c
'''

functest_str_rerun = r'''
    Call mkdir re-run
    Call extract_errors.bat runtest.transcript -errors > .\\re-run\\failError.txt
    Call extract_errors.bat runtest.transcript -fails >> .\\re-run\\failError.txt
    Call copy .fthrc        .\\re-run\\.fthrc
    Call cd re-run
    Call mkdir logs
    Call runtest.bat -test failError.txt -repeat {0} -passSkipOnCycle ENABLE
    Call summary.bat
    CALL format_summary.bat
'''

rm = visa.ResourceManager()

def logger_init(tag, debug=False):
    logtag = tag
    logdir = 'C:\\runtest_logs\\'
    logfile = logtag + '___' + time.strftime("%Y_%m_%d____%H_%M_%S", time.localtime())
    logpath = logdir + logfile

    if not os.path.exists(logdir):
        os.mkdir(logdir)

    logger = logging.getLogger(logtag)
    # delete all handlers
    while len(logger.handlers):
        for x in logger.handlers:
            logger.removeHandler(x)
    logger.setLevel(logging.DEBUG)
    # create file handler which logs even debug messages
    fh = logging.FileHandler(logpath)
    fh.setLevel(logging.DEBUG)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    if debug:
        ch.setLevel(logging.DEBUG)
    else:
        ch.setLevel(logging.INFO)
    # create formatter and add it to the handlers
    formatter1 = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    formatter2 = logging.Formatter('- runtest - %(levelname)s - %(message)s')
    # formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter1)
    ch.setFormatter(formatter2)
    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)


class basetest():
    debug = 0
    rerun = 0
    mail_flag = 0
    run_mode = 1
    con_type = "USB"
    time_boot = 80
    time_summary = 10
    timeout_500cmds = 900
    mod_list = []
    script_list = []
    use_GEN = False
    # used for send mail
    test_title = ""
    fth_version = '6.1'

    def __init__(self, project, **kwargs):

        print("\n{}\n".format('*'*40 + '  test start  ' + '*'*40))
        sys.stdout.flush()
        if 'debug' in kwargs:
            self.debug = kwargs['debug']
        logger_init(project, debug=self.debug)
        self.logger = logging.getLogger(project)
        self.logger.debug("===> runtest args:")
        for key, value in kwargs.items():
            if type(value) is str:
                value = value.replace('\\', '\\\\')
                value = '\"' + value + '\"'
            exec("self.%s = %s" % (key, value))
            self.logger.debug("        %s => %s" % (key, value))

        self.project = project
        self.run_dir = self.dir_prefix + project + '\\'
        self.fth_root = self.dir_prefix + project + '\\' + 'FTH\\FTH'
        self.stress_root = self.dir_prefix + project + '\\' + 'FTH\\Stress'
        self.reg_test_root = self.dir_prefix + project + '\\' + 'FTH\\funcTests'
        self.mail_tool = self.dir_prefix + project + '\\test_tools\\blat312\\full\\blat.exe'

        self.logger.debug('===> reg_test_root: ' + self.reg_test_root)
        self.logger.debug('===> mail tool: ' + self.mail_tool)
        if not os.path.exists(self.reg_test_root) or \
                not os.path.exists(self.mail_tool):
            self.logger.info("===> verify file path exists failed")
            exit(-1)
        self.get_pc_id()
        # read config file
        self.cfg_file = sys.path[0] + '\config.ini'
        self.logger.info("===> config file: %s" % self.cfg_file)
        if not os.path.exists(self.cfg_file):
            self.logger.info("===> verify config file exists failed; \n %s" % self.cfg_file)
            exit(-1)
        self.config = configparser.ConfigParser()
        self.config.read(self.cfg_file)

    def list_all_device(self):
        inst_list = rm.list_resources()
        print('-'*80)
        for inst in inst_list:
            if inst.startswith('USB') or inst.startswith('GPIB'):
                try:
                    dev = rm.open_resource(inst, open_timeout=10)
                    dev_idn = dev.query("*IDN?")
                except:
                    dev_idn = 'open resource failed'
                print('===> {}     {}'.format(inst, dev_idn))
        print('-'*80)

    def __check_resources(self):
        try:
            inst_list = rm.list_resources()
            self.logger.debug('===> device list: ' + str(inst_list))
            DUT, GEN = {}, {}
            for inst in inst_list:
                if inst.startswith('USB') or inst.startswith('GPIB'):
                    dev = rm.open_resource(inst, open_timeout=10)
                    dev_idn = dev.query("*IDN?").strip()
                    if dev_idn.startswith('TEKTRONIX,TBS'):
                        dev.write('HEADER 0')
                        DUT['inst'] = inst
                        DUT['idn'] = dev_idn
                    if dev_idn.startswith('TEKTRONIX,AFG'):
                        GEN['inst'] = inst
                        GEN['idn'] = dev_idn
                        dev.write('*RST')
                    dev.close()
        except Exception as e:
            print("Exception:", e)
            return False

        if not 'idn' in DUT:
            self.logger.info("===> get DUT idn failed.")
            return False
        if self.use_GEN and not 'idn' in GEN:
            self.logger.info("===> get GEN idn failed.")
            return False

        # get fw version ; type; serial_id
        ret = re.match('TEKTRONIX,(.*?),(.*?),(.*?) FV:(.*?)[;\n]', DUT['idn'])
        if ret:
            DUT['type'], DUT['ser_id'], DUT['fw_ver'] = ret.group(1, 2, 4)
            DUT['type'] = DUT['type'].replace(' ', '')
            DUT['type'] = DUT['type'].replace('-', '')
            self.logger.info('-'*80)
            self.logger.info('===> DUT info:')
            self.logger.info("     DUT id:           " + DUT['idn'])
            self.logger.info("     DUT res name:     " + DUT['inst'])
            self.logger.info("     DUT type:         " + DUT['type'])
            self.logger.info("     DUT serial id:    " + DUT['ser_id'])
            self.logger.info("     firmware version: " + DUT['fw_ver'])
            self.logger.info('-'*80)
            self.DUT = DUT
        else:
            self.logger.info("===> parse DUT id failed.")
            self.logger.info("===> DUT id: " + DUT['idn'])
            return False

        if self.use_GEN:
            ret = re.match('TEKTRONIX,(.*?),', GEN['idn'])
            GEN['type'] = ret.group(1)
            GEN['type'] = GEN['type'].replace(' ', '')
            GEN['type'] = GEN['type'].replace('-', '')
            self.logger.info("===> WVGEN id: " + GEN['idn'])
            self.GEN = GEN
        else:
            self.GEN = {'inst': 'none'}
        return True

    def check_resources(self):
        for x in range(4):
            if self.__check_resources():
                return True
            time.sleep(5)
        self.logger.info("===> check_resources failed after try several times")
        return False

    def get_pc_id(self):
        pcname = os.environ['COMPUTERNAME']
        ret = re.match("W-SHPD-(SQA0[1-9])", pcname)
        if ret:
            self.test_pc_name = ret.group(1)
            self.test_pc_id = int(self.test_pc_name[-2:])
            self.power_flag = 1
        else:
            self.test_pc_name = pcname
            self.test_pc_id = 1
            self.power_flag = 0

    def enter_runtest_dir(self):
        os.chdir(self.run_dir)

        subdir = self.DUT['fw_ver']
        if self.mod_list or self.script_list: subdir = 'temp'

        if not subdir in os.listdir(os.getcwd()):
            try:
                os.mkdir(subdir)
            except:
                self.logger.info("===> create dir {} encounter error".format(subdir))
                time.sleep(2)
        if not os.path.exists(subdir):
            self.logger.info("===> create dir {} failed".format(subdir))
            exit(-1)
        os.chdir(subdir)

        seq_list = [0, ]
        for x in os.listdir(os.getcwd()):
            ret = re.match("^([0-9]{1,3})_.*", x)
            seq_list.append(int(ret.group(1)) if ret else -1)

        seq = max(seq_list) + 1
        now = int(time.time())
        timeArray = time.localtime(now)
        # timestamp = time.strftime("%m%d_%H%M", timeArray)
        timestamp = time.strftime("%m%d", timeArray)

        self.run_dir_2 = str(seq) + '_' + self.DUT['type'] + \
                         '_' + self.DUT['ser_id'] + '_' + self.test_pc_name
        self.logger.debug('\n===> create dir ' + self.run_dir_2)
        os.mkdir(self.run_dir_2)
        self.logger.debug('===> enter dir ' + self.run_dir_2)
        os.chdir(self.run_dir_2)
        self.run_dir = os.getcwd()
        self.logger.info("===> run test in directory: " + os.getcwd())

    def lan_reset(self):
        dev = rm.open_resource(self.DUT['inst'], open_timeout=10)
        dev_idn = dev.query("*IDN?")
        dev.write('*RST')
        ret = dev.query("*OPC?")

        self.logger.info("===> reset ethernet")
        dev.write(':ETHERnet:DHCPbootp 0')
        time.sleep(5)
        dev.write(':ETHERnet:DHCPbootp 1')
        time.sleep(15)
        # get scope ipaddress again
        dev.write(':HEADER 0')
        ret = dev.query(':ETHERnet:ipadd?')
        reret = re.match('\"([0-9.]+)\"', ret)
        if not reret:
            self.logger.info('===> lan_reset: get scope ip add failed; %s' % ret)
            exit(-1)

        self.ipadd = reret.group(1)
        if self.ipadd.startswith('169') or self.ipadd.startswith('0'):
            self.logger.info('===> lan_reset: invalid ipadd; %s' % self.ipadd)
            exit(-1)
        self.DUT['inst2'] = 'TCPIP0::' + self.ipadd + '::inst0::INSTR'
        self.logger.info(self.DUT['inst2'])

        # ping gateway
        dev.write(':ETHERnet:PING EXECute')
        time.sleep(5)
        ret = dev.query(':ETHERnet:PING:STATUS?')
        if ret != 'OK\n':
            self.logger.info('===> lan_reset: ping gateway failed')
            exit(-1)

        dev.close()
        return True

    def init_ethernet(self):
        dev = rm.open_resource(self.DUT['inst'], open_timeout=10)
        dev_idn = dev.query("*IDN?")
        dev.write('*RST')
        ret = dev.query("*OPC?")

        self.ipadd = '0.0.0.0'
        # get scope ipaddress first
        dev.write(':HEADER 0')
        ret = dev.query(':ETHERnet:ipadd?')
        reret = re.match('\"([0-9.]+)\"', ret)
        if reret: self.ipadd = reret.group(1)

        if self.ipadd.startswith('169') or self.ipadd.startswith('0'):
            self.logger.info('===> init_ethernet: invalid ipadd, try to reset lan; %s' % self.ipadd)
            dev.write(':ETHERnet:DHCPbootp 0')
            time.sleep(5)
            dev.write(':ETHERnet:DHCPbootp 1')
            time.sleep(15)
            ret = dev.query(':ETHERnet:ipadd?')
            reret = re.match('\"([0-9.]+)\"', ret)
            if not reret:
                self.logger.info('===> after reset lan, get scope ip add failed; %s' % ret)
                exit(-1)
            self.ipadd = reret.group(1)
            if self.ipadd.startswith('169') or self.ipadd.startswith('0'):
                self.logger.info('===> after reset lan, get invalid ipadd; %s' % self.ipadd)
                exit(-1)

        # ping scope ip from pc
        ping_ret = subprocess.check_output(['ping', self.ipadd])
        self.logger.debug('===> ping result: \n {} \n'.format(ping_ret))
        re_str = 'Reply from ' + self.ipadd + ': bytes=32'
        if not re.findall(re_str, str(ping_ret)):
            self.logger.info('===> ping scope ip failed, try to reset lan')
            dev.write(':ETHERnet:DHCPbootp 0')
            time.sleep(5)
            dev.write(':ETHERnet:DHCPbootp 1')
            time.sleep(15)
            ret = dev.query(':ETHERnet:ipadd?')
            reret = re.match('\"([0-9.]+)\"', ret)
            if not reret:
                self.logger.info('===> after reset lan, get scope ip add failed; %s' % ret)
                exit(-1)
            self.ipadd = reret.group(1)
            if self.ipadd.startswith('169') or self.ipadd.startswith('0'):
                self.logger.info('===> after reset lan, get invalid ipadd; %s' % self.ipadd)
                exit(-1)

        self.DUT['inst2'] = 'TCPIP0::' + self.ipadd + '::inst0::INSTR'
        self.logger.info(self.DUT['inst2'])
        # ping scope ip from pc again
        ping_ret = subprocess.check_output(['ping', self.ipadd])
        self.logger.debug('===> ping result: \n {} \n'.format(ping_ret))
        re_str = 'Reply from ' + self.ipadd + ': bytes=32'
        if not re.findall(re_str, str(ping_ret)):
            self.logger.info('===> ping scope ip failed second times, exit')
            exit(-1)

        dev.close()
        return True

    def umount_udisk(self):
        self.init_ethernet()
        self.logger.info('===> try to umount udisk:')
        host = self.ipadd
        username = b'root'
        prompt = b'~$'

        tn = telnetlib.Telnet(host)
        tn.set_debuglevel(2)
        # login
        tn.read_until(b'login: ')
        tn.write(username + b'\n')
        print(tn.read_until(prompt))

        tn.write(b'ls\n')
        print(tn.read_until(prompt))

        tn.write(b'umount -f /usb0\n')
        ret = tn.read_until(prompt)

        tn.write(b'mount\n')
        ret = tn.read_until(prompt)
        ret = ret.decode('ascii')
        reret = re.findall('usb', ret)

        tn.close()

        if reret:
            self.logger.info('===> umount udisk failed')
            exit(-1)
        else:
            return True

    def has_udisk(self):
        dev = rm.open_resource(self.DUT['inst'], open_timeout=10)
        dev.timeout = 100000
        freespace = dev.query("filesystem:freespace?")
        return (float(freespace)>1E8)

    def generate_fthrc(self):
        if self.con_type == 'IP':
            self.init_ethernet()
            self.logger.info('===> generate_fthrc: connect type %s' % self.con_type)
            DUT_ID = self.DUT['inst2']
            EVENT_ENABLE = '1'
        else:
            DUT_ID = self.DUT['inst']
            EVENT_ENABLE = '1'
        rc = '''
        INTERFACE_SPEC WVGEN {
             TYPE VISA {
                    RESOURCE_EXPR %s
             }
        }

        INTERFACE_SPEC DUT {
            TYPE VISA {
                    RESOURCE_EXPR %s
                    ###EVENT_ENABLE_STATE %s
           }
        }

        REGRESSION_TEST_ROOT %s
        REGRESSION_TEST_LOGS .\logs
        DEBUG_MODE 1
        ''' % (self.GEN['inst'], DUT_ID, EVENT_ENABLE, self.reg_test_root)

        if not os.path.exists('logs'):
            os.mkdir('logs')
        with open(".fthrc", mode='w') as fthrc:
            fthrc.write(rc)
        self.logger.info('===> create .fthrc')
        self.logger.debug(rc)

    def generate_fthinstall(self):
        if self.fth_version == '5.5':
            fthinit_str2 = fthinit_str_55
        else:
            fthinit_str2 = fthinit_str

        fthinstall_str = fthinit_str2.format(self.fth_root)

        os.chdir(self.run_dir)
        with open('fthinstall.bat', mode='w') as bat:
            bat.write(fthinstall_str)
        self.logger.info('===> create fthinstall.bat')
        self.logger.debug(fthinstall_str)
        self.fthinstall_str = fthinstall_str

    def generate_bat(self):
        pass

    def pre_test(self):
        return
        os.system("taskkill /F /IM OpenChoiceDesktop.exe /T")
        os.system("taskkill /F /IM TEKVIS~1.EXE /T")
        os.system("taskkill /F /IM TekVisaRM.exe /T")
        os.system("taskkill /F /IM fth.exe /T")

    def exec_test(self):
        self.pre_test()
        os.chdir(self.run_dir)
        self.start_time = time.time()
        self.test_result = 'FAIL'

        if self.mail_flag:
            thread = threading.Thread(target=self.test_monitor)
            thread.start()
        if self.run_mode == 1:
            os.system('run_test.bat')
        if self.run_mode == 2:
            import win32api
            win32api.ShellExecute(0, 'open', 'run_test.bat', '', '', 1)
            thread.join()

    def fth_is_running(self):
        ps1 = psutil.Process()
        if ps1.children():
            return True
        else:
            return False

    def monitor(self, rundir):
        pass

    def send_mail(self):
        pass

    def mail_error(self, mail_text):
        if self.mail_flag<=0:
            self.logger.info ('===> mail_flag is 0, abort send mail')
            return
        self.logger.info ('===> enter mail_error')
        mail_from = self.config["mail"]['from']
        mail_to   = self.config["mail"]['group_'+str(self.mail_flag)]
        self.logger.info ('===> send error to %s' % mail_to)

        mail_sub  = self.test_title + ' encounter an error. '
        mail_cmd1 = '%s -install smtpserver.tek.com %s 3 25' % (self.mail_tool, mail_from)
        mail_cmd2 = '%s -body \"%s\" -s \"%s\" -to \"%s\" '\
            % (self.mail_tool, mail_text, mail_sub, mail_to)

        subprocess.check_call(mail_cmd1)
        subprocess.check_call(mail_cmd2)

    def test_monitor(self):
        self.monitor(self.run_dir)
        time.sleep(self.time_summary)
        self.send_mail()
        if self.rerun and type(self) is functest:
            self.monitor('re-run')
            time.sleep(self.time_summary)
            # self.send_mail()

    def add_result_to_summary(self, result):
        self.logger.info('===> add result to summary')
        try:
            with open(r'..\summary.csv', mode='a+') as body:
                body.write(result + '\n')
        except Exception as e:
            self.logger.info('===> %s' % e)

    def power_cycle(self):

        if self.power_flag == 0:
            self.logger.info("===> power_flag is 0, abort power cycle")
            return False

        ip = self.config["power"]["ip"]
        user = self.config["power"]["user"]
        passwd = self.config["power"]["passwd"]
        port = self.config["power"][self.test_pc_name]
        self.logger.debug("===> power info: %s %s %s %s %s" % (ip, user, passwd, port, self.test_pc_name))
        assert (int(port) > 0 and int(port) < 9)

        url_off = 'http://%s/outlet?%s=OFF' % (ip, port)
        url_on = 'http://%s/outlet?%s=ON' % (ip, port)

        r1 = requests.get(url_off, auth=(user, passwd), timeout=10)
        result1 = 'success' if r1.status_code == 200 else 'failed'
        self.logger.debug("===> power off port %s %s" % (port, result1))
        time.sleep(3)
        r2 = requests.get(url_on, auth=(user, passwd), timeout=10)
        result2 = 'success' if r2.status_code == 200 else 'failed'
        self.logger.debug("===> power on port %s %s" % (port, result2))

    def reboot_DUT(self):
        assert (self.power_flag != 0)
        self.power_cycle()
        self.logger.info('===> wait {} seconds for scope boot up'.format(self.time_boot))
        time.sleep(self.time_boot)

    def DUT_send_cmd(self, cmd):
        dev = rm.open_resource(self.DUT['inst'], open_timeout=10)
        time.sleep(2)
        self.logger.info('===> send cmd %s to DUT' % cmd)
        dev.write(cmd)
        time.sleep(1)
        dev.close()

    def DUT_query(self, cmd):
        dev = rm.open_resource(self.DUT['inst'], open_timeout=10)
        time.sleep(2)
        ret = dev.query(cmd)
        self.logger.info('===> Query %s: %s' % (cmd, ret))
        dev.close()

    def initialize(self):
        if not self.check_resources():
            self.logger.info('===> check_resources failed.')
            return False
        if self.has_udisk() != self.need_udisk:
            self.logger.info('===> check USB driver failed.')
            return False
        self.enter_runtest_dir()
        self.generate_fthrc()
        self.generate_fthinstall()
        self.generate_bat()
        self.logger.info('initialize done.')
        return True


class stresstest(basetest):
    seed = 0
    num_cmds = 10000
    timeout = 60
    use_GEN = False
    need_udisk = False

    def __init__(self, project, **kwargs):
        basetest.__init__(self, project, **kwargs)
        self.test_title = self.project + '  stresstest'
        self.run_dir += 'StressTest'
        self.logger.info("===> run_dir: " + self.run_dir)

    def generate_stress_file(self, stress_file='', mod_list=[]):
        if stress_file != '':
            self.stress_file = self.stress_root + '\\' + stress_file
        elif len(mod_list) > 0:
            cmds = ''
            for mod in mod_list:
                with open(self.stress_root + '\\' + mod + '.str') as modcmds:
                    cmds += '\n\n' + modcmds.read()
            self.stress_file = '_'.join(mod_list) + '.str'
            with open(self.stress_file, 'w') as cmdsfile:
                cmdsfile.write(cmds)
        else:
            self.stress_file = self.stress_root + '\\' + self.project + \
                               ('_EDU.str' if 'EDU' in self.DUT['type'] else '.str')

        self.logger.info('===> stress_file: ' + self.stress_file)
        if not os.path.isfile(self.stress_file):
            self.logger.info('\n===> stress file not exist, exit.')
            exit(-1)
        shutil.copy(self.stress_file, 'cmds.str')

    def generate_bat(self):
        # copy cmds file to run_dir
        self.generate_stress_file()
        os.chdir(self.run_dir)
        runtest_str = self.fthinstall_str
        runtest_str += 'fth stress.exp -f %s -R -N %d -t %d -seed %d -C 500000' \
                       % (self.stress_file, self.num_cmds, self.timeout, self.seed)
        with open('run_test.bat', mode='w') as runStress:
            runStress.write(runtest_str)
        self.logger.info('===> create run_test.bat')
        self.logger.debug(runtest_str)

    def monitor(self, rundir):
        interval = 60
        os.chdir(rundir)
        log_file = os.getcwd() + r'\logs\status.str'
        log_file_2 = os.getcwd() + r'\logs\status_2.txt'

        cmd_old = 0
        self.logger.info("===> start monitor stress test process:")
        time.sleep(30)

        while 1:
            if not self.fth_is_running():
                self.logger.debug("===> fth is not running, exist monitor")
                return

            if os.path.exists(log_file):
                try:
                    shutil.copy(log_file, log_file_2)
                    with open(log_file_2, mode='r') as ff:
                        runlog = ff.read()
                except:
                    self.logger.debug("===> copy status.str failed")
            else:
                self.logger.debug("===> no log file found: " + log_file)
                time.sleep(interval)
                continue

            ret = re.findall("Cmds Sent: ([0-9]+)  Run Time", runlog)
            if ret:
                cmd_new = int(ret[0])
                time_used = int(time.time() - self.start_time) / 60
                self.logger.info("===> have run cmds %s/%s. use %d min" % (cmd_new, self.num_cmds, time_used))
            else:
                self.logger.debug("===> get cmd number from runlog failed.")
                self.logger.debug("===> runlog: %s" % runlog)
                time.sleep(interval)
                continue

            if cmd_new == self.num_cmds:
                self.logger.info("===> stress test finished.")
                return
            if cmd_new > cmd_old:
                starttime = int(time.time())
                cmd_old = cmd_new
            if cmd_new == cmd_old:
                runtime = int(time.time()) - starttime
                if runtime >= self.timeout_500cmds:
                    self.logger.info("===> status.str have %d seconds not updated, consider \
                                            as stress test failed." % runtime)
                    # os.system("taskkill /f /im fth.exe")
                    # return
            time.sleep(interval)

    def send_mail(self):
        if self.mail_flag <= 0:
            self.logger.info('===> mail_flag is 0, abort send mail')
            return
        self.logger.info('===> enter stresstest class send_mail')
        mail_from = self.config["mail"]['from']
        mail_to = self.config["mail"]['group_' + str(self.mail_flag)]
        self.logger.info('===> send report to %s' % mail_to)
        mail_sub = self.test_title + ' finished. ' + self.run_dir_2 + '; FW: ' + self.DUT['fw_ver']

        mail_body = 'firmware version:  ' + self.DUT['fw_ver'] + '\n\n'
        mail_body += 'test log:  ' + os.getcwd() + '\n\n'
        mail_body += 'cmds send:  ' + str(self.num_cmds) + '\n\n'

        if os.path.exists(r'logs\status.str'):
            with open(r'logs\status.str', mode='r') as body:
                runlog = body.read()
        else:
            runlog = 'empty log'

        passrate = 0
        try:
            ret = re.findall("Cmds Sent: ([0-9]+)  Run Time", runlog)
            cmds_send = int(ret[0])
            passrate = int(float(ret[0]) / float(self.num_cmds) * 100)
            self.test_result = 'PASS' if passrate == 100 else 'FAIL'
        except:
            cmds_send, self.test_result = 500, 'FAIL'
            pass
        module_list = os.path.basename(self.stress_file).split('.')[0]
        time_used = int(time.time() - self.start_time)
        time_used = "%d:%d" % (time_used / 3600, time_used % 3600 / 60)
        summary_result = "%s,%d,%d,%d%%,%s,%s" % (
        module_list, self.num_cmds, cmds_send, passrate, self.test_result, time_used)
        self.logger.info(summary_result)
        self.add_result_to_summary(summary_result)
        mail_body += 'passrate:  ' + str(passrate) + '%\n\n'
        mail_body += runlog

        mail_cmd1 = '%s -install smtpserver.tek.com %s 3 25' % (self.mail_tool, mail_from)
        if os.path.exists(r'logs\stress.cmds'):
            mail_cmd2 = '%s -s \"%s\" -to \"%s\" -body \"%s\" -attacht \"%s\" -attacht \"%s\"' \
                        % (self.mail_tool, mail_sub, mail_to, mail_body, r'logs\stress.log', r'logs\stress.cmds')
        else:
            self.logger.info('open  logs\stress.cmds  failed!!!')
            mail_cmd2 = '%s -s \"%s\" -to \"%s\" -body \"%s\" -attacht \"%s\" ' \
                        % (self.mail_tool, mail_sub, mail_to, mail_body, r'logs\stress.log')

        self.logger.debug(mail_cmd1)
        self.logger.debug(mail_cmd2)
        subprocess.check_call(mail_cmd1)
        subprocess.check_call(mail_cmd2)


class functest(basetest):
    use_GEN = True
    need_udisk = True

    def __init__(self, project, **kwargs):
        basetest.__init__(self, project, **kwargs)
        self.run_dir += 'funcTests'
        self.logger.info("===> run_dir: " + self.run_dir)
        self.time_summary = 40
        self.num_cases_pass = 0

    def generate_bat(self):
        runtest_str, runtest_str_2 = self.fthinstall_str, self.fthinstall_str

        if self.mod_list:
            runtest_str += functest_str.format('-su ' + ' '.join(self.mod_list))
            runtest_str_2 += functest_str_2.format('-su ' + ' '.join(self.mod_list))
        else:
            runtest_str += functest_str.format(' ')
            runtest_str_2 += functest_str_2.format(' ')

        if self.script_list:
            runtest_str = self.fthinstall_str
            for script in self.script_list:
                runtest_str += 'fth -l %s \n' % script

        if self.rerun:
            runtest_str += functest_str_rerun.format(self.rerun)

        with open('run_test.bat', mode='w') as bat:
            bat.write(runtest_str)
        self.logger.info('===> create run_test.bat, contents:')
        self.logger.debug(runtest_str)

        if not self.script_list:
            with open('run_test2.bat', mode='w') as bat:
                bat.write(runtest_str_2)
            ret = subprocess.check_output('run_test2.bat')
            self.num_cases_all = int(ret)
            self.logger.info('===> num_cases_all: {}'.format(self.num_cases_all))

    def parse_summary(self):
        # get passrate from summary.txt
        self.passrate = ''
        if os.path.exists(r'summary.txt'):
            with open(r'summary.txt', mode='r') as txtbody:
                sumlog = txtbody.read()
            ret = re.findall("TESTS PASSED: ([0-9]+) of", sumlog)
            try:
                self.num_cases_pass += int(ret[0])
            except:
                pass
            self.passrate = "{:.0f}".format(100.0 * self.num_cases_pass / self.num_cases_all) + '%'
            self.logger.info(
                'num_cases_all: {} num_cases_pass: {} passrate: {}'.format(self.num_cases_all, self.num_cases_pass,
                                                                           self.passrate))

    def monitor(self, rundir):
        timeout = 7200
        interval = 30
        os.chdir(rundir)
        self.logger.info("===> monitor func test under dir: \n\t" + rundir)
        time.sleep(30)
        nolog_times = 0

        testcase = ''
        while 1:
            log = ''
            check_fth_times = 30
            while not self.fth_is_running():
                check_fth_times -= check_fth_times
                if os.path.exists('summary.txt'):
                    break
                if check_fth_times <= 0:
                    self.logger.info("===> long time not found fth process, exit monitor")
                    return
                time.sleep(10)

            if os.path.exists('summary.txt'):
                self.logger.info("===> found summary.txt, runtest finished. monitor exit")
                self.parse_summary()
                return

            logfile = [x for x in os.listdir(os.getcwd() + '\\logs') if re.match('^[a-zA-Z_0-9]+\.log$', x)]
            if len(logfile) != 1:
                self.logger.debug("===> no log file found %d" % nolog_times)
                time.sleep(interval)
                nolog_times += 1
                if nolog_times > 10:
                    self.logger.info("===> wait log file timeout, kill process fth.")
                    os.system("taskkill /f /im fth.exe /T")
                continue
            nolog_times = 0
            logfile = logfile[0]
            testcase_n = logfile.split('.')[0]
            try:
                starttime = os.path.getctime('logs\\' + logfile)
            except:
                self.logger.debug("===> get create time for log file failed, may be this script finished.")
                time.sleep(10)
                continue
            if testcase_n == testcase:
                # check time
                runtime = time.time() - starttime
                runtime = int(runtime)
                if runtime > timeout:
                    self.logger.info("===> timeout, kill process fth.")
                    os.system("taskkill /f /im fth.exe /T")
                else:
                    self.logger.debug(runtime)
            else:
                testcase = testcase_n
                self.logger.debug("===> start run case: " + testcase)

            time.sleep(interval)

    def send_mail(self):
        if self.mail_flag <= 0 or self.script_list:
            self.logger.info('===> mail_flag is {}, abort send mail'.format(self.mail_flag))
            return
        self.logger.info('===> enter functest_send_mail')
        mail_from = self.config["mail"]['from']
        mail_to = self.config["mail"]['group_' + str(self.mail_flag)]
        self.logger.info('===> send report to %s' % mail_to)

        if not os.path.exists(r'summary.html'):
            with open(r'summary.html', mode='w') as body:
                body.write('not found summary.html')

        mail_sub = self.test_title + ' finished. ' + self.run_dir_2 + '; ' \
                   + self.con_type + '; FW: ' + self.DUT['fw_ver'] + '; ' + self.passrate
        mail_cmd1 = '%s -install smtpserver.tek.com %s 3 25' % (self.mail_tool, mail_from)
        mail_cmd2 = '%s summary.html -html -s \"%s\" -to \"%s\" -attacht \"%s\"' \
                    % (self.mail_tool, mail_sub, mail_to, 'summary.html')

        subprocess.check_call(mail_cmd1)
        subprocess.check_call(mail_cmd2)


class upgrade(basetest):
    def __init__(self, project, **kwargs):
        basetest.__init__(self, project, **kwargs)
        self.run_dir += 'funcTests'
        self.logger.info("===> run_dir: " + self.run_dir)
        self.time_summary = 40
        self.time_update = 300
        if self.project=='Cornerstone':
            self.fw_name = 'TBS2KB.TEK'
        elif self.project=='Touchstone':
            self.fw_name = 'TBD'
        self.fw_path = os.path.join(self.fw_path, \
            self.project, self.version, self.fw_name)

    def copy_firmware(self):
        self.init_ethernet()
        self.logger.info('===> start to copy fireware:')
        host = self.ipadd
        username = b'root'
        prompt = b'~$'

        tn = telnetlib.Telnet(host)
        tn.set_debuglevel(2)
        # login
        tn.read_until(b'login: ')
        tn.write(username + b'\n')
        print(tn.read_until(prompt))

        tn.write(b'ls\n')
        print(tn.read_until(prompt))

        tn.write(b'fw_setenv memsize 240M\n')
        print(tn.read_until(prompt))
        tn.write(b'rm /mnt/user-data/*.core.*\n')
        print(tn.read_until(prompt))

        tn.write(b'mkdir /tmp/mnt\n')
        ret = tn.read_until(prompt)

        tn.write(b'umount /tmp/mnt/\n')
        ret = tn.read_until(prompt)

        mount_cmd = 'mount  -o nolock,proto=tcp 134.64.222.93:/nfs_firmware/nightly/ /tmp/mnt\n'
        if self.test_pc_name == 'SQA07':
            mount_cmd = 'mount  -o nolock,proto=tcp 134.64.222.93:/nfs_firmware/nightly/release/ /tmp/mnt\n'
        self.logger.info('===> firmware path: %s' % mount_cmd)
        mount_cmd = mount_cmd.encode()
        # tn.write(b'mount  -o nolock,proto=tcp 134.64.222.93:/nfs_firmware/nightly/ /tmp/mnt\n')
        tn.write(mount_cmd)
        ret = tn.read_until(prompt)
        time.sleep(2)

        tn.write(b'mount\n')
        ret = tn.read_until(prompt)
        ret = ret.decode('ascii')
        reret = re.findall('134.64.222.93:/nfs_firmware/nightly', ret)

        tn.write(b'rm /mnt/user-data/TBS2KB.TEK\n')
        ret = tn.read_until(prompt, timeout=60)
        # tn.write(b'md5sum /tmp/mnt/TBS2KB.TEK\n')
        # ret = tn.read_until(prompt, timeout=60)
        # ret = ret.decode('ascii')
        # reret = re.findall('\n(.*)  /tmp/mnt', ret)
        # md5_1 = reret[0]
        tn.write(b'ls -al /tmp/mnt/TBS2KB.TEK\n')
        ret = tn.read_until(prompt, timeout=60)
        ret = ret.decode('ascii')
        md5_1 = ret.split()[7]

        tn.write(b'cp /tmp/mnt/TBS2KB.TEK /mnt/user-data/TBS2KB.TEK\n')
        ret = tn.read_until(prompt, timeout=180)
        time.sleep(1)
        tn.write(b'sync\n')
        ret = tn.read_until(prompt, timeout=60)
        time.sleep(5)

        # tn.write(b'md5sum /mnt/user-data/TBS2KB.TEK\n')
        # ret = tn.read_until(prompt, timeout=60)
        # ret = ret.decode('ascii')
        # reret = re.findall('\n(.*)  /mnt/user-data', ret)
        # md5_2 = reret[0]
        tn.write(b'ls -al /mnt/user-data/TBS2KB.TEK\n')
        ret = tn.read_until(prompt, timeout=60)
        ret = ret.decode('ascii')
        md5_2 = ret.split()[7]

        tn.write(b'umount /tmp/mnt/\n')
        ret = tn.read_until(prompt)
        tn.close()

        self.logger.info("===> file size: %s, %s" % (md5_1, md5_2))
        assert (int(md5_2) > 10e6)

        if md5_1 != md5_2:
            self.logger.info('===> copy firmware: check md5 failed')
            return False
        else:
            return True

    def copy_firmware2(self):
        os.chdir(sys.path[0])

        if not os.path.exists(self.fw_path):
            self.logger.info('===> copy firmware2: not found firmware: {}'.format(self.fw_path))
            return False

        # get new version from file
        with open(self.fw_path, mode='rb') as fw:
            self.fw_header = fw.read(50)
        self.exp_fw_ver = ''
        for i in self.fw_header:
            if i > 45:
                self.exp_fw_ver += chr(i)
            if len(self.exp_fw_ver) > 3 and i == 0:
                break

        self.logger.info('===> new firmware: {} {}'.format(self.fw_path, self.exp_fw_ver))
        if self.exp_fw_ver == self.DUT['fw_ver']:
            self.logger.info('===> new version {} equal current version, abort copy'.format(self.exp_fw_ver))
            return True

        cmd = 'uploadfw.exe  ' + self.fw_path
        self.logger.info('===> run cmd: %s' % cmd)
        return bool(os.system(cmd) == 0)

    def upgrade(self, mode='NFS'):

        if self.power_flag:
            self.logger.info('===> reboot scope before upgrade:')
            self.reboot_DUT()

        if not self.check_resources():
            self.logger.info('===> check_resources failed after the first reboot')
            return False

        if self.upmode == 'NFS':
            # copy firmware
            if not self.copy_firmware():
                self.logger.info('===> copy_firmware: copy firmware failed')
                return False
            # reboot again, sometimes scope visa dead
            if self.power_flag: self.reboot_DUT()
        elif self.upmode == 'USB':
            # check firmware exist on usb driver
            pass
        elif self.upmode == 'VISA':
            if not self.copy_firmware2():
                self.logger.info('===> copy_firmware2: copy firmware failed')
                return False

        if self.exp_fw_ver == self.DUT['fw_ver']:
            self.logger.info('===> new version {} equal current version, abort upgrade'.format(self.exp_fw_ver))
            return True

        dev = rm.open_resource(self.DUT['inst'], open_timeout=10)
        time.sleep(2)
        dev_idn = dev.query("*IDN?")
        if mode == 'NFS' or mode == 'VISA':
            dev.write(':fwupdate:remoteupdate')
        elif mode == 'USB':
            dev.write(':fwupdate:update')
        dev.close()
        time.sleep(15)

        try:
            dev = rm.open_resource(self.DUT['inst'], open_timeout=10)
            self.logger.info('===> scope not reboot as expected.')
            return False
        except:
            self.logger.info('===> upgrade started as expected:')
            if self.power_flag:
                self.logger.info('===> wait for {} seconds for upgrade'.format(self.time_update))
                time.sleep(self.time_update)
                if self.power_flag:
                    self.reboot_DUT()
                if not self.check_resources():
                    self.logger.info('===> check_resources failed after the upgrade and reboot')
                    return False
                if self.exp_fw_ver == self.DUT['fw_ver']:
                    return True
                else:
                    self.logger.info('===> verify firmware version failed after upgrade.')
                    self.logger.info('{}; {}'.format(self.exp_fw_ver, self.DUT['fw_ver']))
                    return False

            return True


def runtest(project, test_type, **kwargs):
    if test_type == 'functest':
        return functest(project, **kwargs)
    elif test_type == 'stresstest':
        return stresstest(project, **kwargs)
    elif test_type == 'upgrade':
        return upgrade(project, **kwargs)
    else:
        print('wrong test type.')
        exit(-1)


def cleanup():
    print("\n{}\n".format('*'*40 + '  test end  ' + '*'*40))

import atexit
atexit.register(cleanup)
