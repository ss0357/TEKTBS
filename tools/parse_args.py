import argparse
import sys, os

parser = argparse.ArgumentParser()
parser.add_argument("-debug", action='store_true')
dir_prefix = os.path.abspath(sys.path[0] + '\\..\\..\\') + '\\'
parser.add_argument("-dir_prefix", type=str, default=dir_prefix)
# used for upgrade
parser.add_argument("-upmode", type=str, default='VISA')
parser.add_argument("-version", type=str, default='nightly')
parser.add_argument("-fw_path", type=str, default='K:\\firmware\\')

# used for run nightly test
parser.add_argument("-p", action='store_true')
parser.add_argument("-fthrc", action='store_true')
parser.add_argument("-listall", action='store_true')
parser.add_argument("-mail", type=int, default=0, dest='mail_flag')
parser.add_argument("-rerun", type=int, default=0)
parser.add_argument("-con_type", type=str, default='USB')
parser.add_argument("-su", nargs='*', dest='mod_list')
parser.add_argument("-script", nargs='*', dest='script_list')

# used for stress test
parser.add_argument("-num_cmds", type=int, default= 1000000)
parser.add_argument("-seed", type=int, default= 0)
