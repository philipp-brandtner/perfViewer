"""
perfViewer
Module: inputparser
Responsible: Brandtner Philipp
Description: Module to parse input data to data structures
"""

import argparse
import os
import shutil
import datetime


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--username", help='Username to login on target, default root',
                        type=str, default="root")
    parser.add_argument("--password", help='Password to login on target, otherwise standard password',
                        type=str, default="sdhr-r&s")
    parser.add_argument("--first", help='Connect to first side with standard ip 192.168.24.200',
                        action="store_true")
    parser.add_argument("--second", help='Connect to second side with standard ip 192.168.24.201',
                        action="store_true")
    parser.add_argument("-ip", help='Connect to IP',nargs="?", type=str, action='store', const='192.168.24.200')
    parser.add_argument("-o", "--offline_dir", nargs="?", action='store', const='true',
                        help="Use files from offline directory")
    parser.add_argument("-t", "--record_duration", help="Duration of perf data record",
                        type=float, nargs="?", default=1)
    parser.add_argument("-tr", "--trace",
                        help="Use perf probes defined in perf.list to trace userspace function calls",
                        nargs='*', action='store')
    parser.add_argument("-p", "--pid", help="Record events on existing process ID (comma separated list)", type=str)
    parser.add_argument("--overwrite", help="Overwrite data of ./SampleData directory", action="store_true")
    parser.add_argument("-e", "--executable", help="Specify path to executable. Default loaded from target", nargs='*',
                        type=str, action='store')

    args = parser.parse_args()

    if not args.black and not args.red and args.offline_dir is None and args.ip is None:
        parser.error("At least one of the following arguments needs to be specified: -r, -b. -o, -ip")
    elif args.trace == [] and args.offline_dir is None:
        parser.error("Online --trace requires parameter <probe_list>. Ex.: --trace probe_lists/probes_TNW.list")
    elif args.offline_dir == 'true':
        parser.error("Offline usage requires specification of offline folder. Ex.: --offline ../SampleData_2020-03-18_10:43:25")
    elif args.executable == []:
        parser.error("-e, --executable require explicit executable names")

    if args.executable is not None and args.executable !=[]:
        for file in args.executable:
            if not os.path.exists(file):
                parser.error("Following executable doesn't exist:" + file)

    if args.trace is not None and args.trace !=[]:
        for file in args.trace:
            if not os.path.exists(file):
                parser.error("Following probe file doesn't exist:" + file)

    return args

def get_additional_args(args, conf):
    additional_args = dict()
    time = datetime.datetime.now().strftime("_%Y-%m-%d_%H:%M:%S")
    if args.offline_dir:
        load_files_from_target = False

        if "../" in args.offline_dir:
            perf_import_dir = args.offline_dir
        else:
            perf_import_dir = "../" + args.offline_dir
        if perf_import_dir.strip()[-1] != '/':
            perf_import_dir += '/'

        if not os.path.exists(perf_import_dir):
            print("Error: Couldn't find path: " + perf_import_dir)
            os.sys.exit()
    else:
        load_files_from_target = True

        if not args.overwrite:
            data_folder = '../SampleData' + time + '/'
            os.makedirs(data_folder)
            perf_import_dir = data_folder
        else:
            if os.path.exists('../SampleData'):
                shutil.rmtree('../SampleData')
            os.makedirs('../SampleData')
            perf_import_dir = "../SampleData/"

    if args.red:
        target_ip = conf.get("IP_1_DEFAULT")
    elif args.black:
        target_ip = conf.get("IP_2_DEFAULT")
    else:
        target_ip = args.ip

    if args.trace is not None:
        tracing = True
        probe_list_filename = args.trace
    else:
        tracing = False
        probe_list_filename = ''

    additional_args["PERF_IMPORT_DIR"] = perf_import_dir
    additional_args["LOAD_FILES_FROM_TARGET"] = load_files_from_target
    additional_args["TARGET_IP"] = target_ip
    additional_args["TRACING"] = tracing
    additional_args["PROBE_LIST_FILENAME"] = probe_list_filename

    return additional_args, time