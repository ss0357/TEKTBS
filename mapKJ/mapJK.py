import os,sys
import time
from sys import exit
from Crypto.Cipher import AES

if len(sys.argv)<=1:
    print('args is wrong.')
    exit(-1)

key, passwd = sys.argv[-2:]

if len(passwd)==0:
    print('password length should > 0')
    exit(-1)
if len(key)!=16:
    print('key length should == 16')
    exit(-1)

obj = AES.new('tek', AES.MODE_CBC, key)
if sys.argv[1]=='encode':
    if len(passwd)==0 or len(passwd)>16:
        print('password length should in range <1, 16>')
        exit(-1)
    passwd = '{:16s}'.format(passwd)
    cpwd = obj.encrypt(passwd)
    int_cpwd = int.from_bytes(cpwd, byteorder='little')
    print(int_cpwd)
    exit()

rpwd = (int(passwd)).to_bytes(16, byteorder='little')
realpwd = obj.decrypt(rpwd)
realpwd = realpwd.decode(encoding='utf-8')
realpwd = realpwd.strip(' ')

ppd = realpwd

pcname = os.environ['COMPUTERNAME']
if not (pcname.startswith('W-SHPD-SQA') or pcname == 'W-SHPD-SOLI'):
    print('test env limited')
    exit(-1)

if not os.path.exists("K:\\Group\\VDC\SQA\\"):
    os.system('net use K: /del')
    time.sleep(1)
    print('try to map \\\\W-SHPD-SQA08\\sqa08_share to K:')
    ret = os.system('net use K: \\\\w-shpd-sqa08\\sqa08_share {} /user:GLOBAL\soli'.format(ppd))
    if ret == 0:
        print('map K: success')
    else:
        exit(ret)
else:
    print('Driver K mounted, dont need map')


if not os.path.exists("J:\\Group\\VDC\SQA\\"):
    os.system('net use J: /del')
    time.sleep(1)
    print('try to map \\\\tekshfs6\\wce to J:')
    ret = os.system('net use J: \\\\tekshfs6\\wce {} /user:GLOBAL\soli'.format(ppd))
    if ret == 0:
        print('map J: success')
    else:
        exit(ret)
else:
    print('Driver J mounted, dont need map')
