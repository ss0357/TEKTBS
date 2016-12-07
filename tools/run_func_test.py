import sys, os
import time
sys.path.append(sys.path[0] + '\\pylibs')
from runtestV3 import runtest
from parse_args import parser

args = parser.parse_args()


Runtest = runtest('Cornerstone', 'functest', **args.__dict__)
Runtest.test_title = 'Cornerstone nightly test'

if args.fthrc:
    if Runtest.check_resources():
        Runtest.generate_fthrc()
    exit(0)

if args.listall:
    Runtest.list_all_device()
    exit(0)

if args.p:
    Runtest.reboot_DUT()

if Runtest.initialize():
    Runtest.exec_test()
else:
    exit(-1)
