import sys
sys.path.append(sys.path[0] + '\\pylibs')
from runtestV3 import runtest
from parse_args import parser


args = parser.parse_args()
args.run_mode   = 2


for x in range(args.rerun):

    # start run stress test
    Runtest = runtest('Cornerstone', 'stresstest', **args.__dict__)
    #Runtest.seed = (Runtest.test_pc_id-1)*2000
    Runtest.seed = x*2000 + args.seed

    if args.p: Runtest.reboot_DUT()

    if Runtest.initialize():
        # Runtest.umount_udisk()
        Runtest.exec_test()
