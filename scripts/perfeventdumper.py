"""
Module: perfviewer
Responsible: Brandtner Philipp
"""

import argparse
import os
import pandas as pd
import re
import prettytable

# Filenames for perf exports
SCHED_SWITCH_FILENAME = 'perf.data.sched:sched_switch.dump'
IRQ_HANDLER_ENTRY_FILENAME = 'perf.data.irq:irq_handler_entry.dump'
IRQ_HANDLER_EXIT_FILENAME = 'perf.data.irq:irq_handler_exit.dump'

def import_data_from_sched_switch(perf_export_dir, filename):
    """
    Open sched:sched_switch.dump file and import data
    :param perf_export_dir: Path to file
    :param filename: name of file
    :return: pandas dataframe of events on success, otherwise -1
    """
    try:
        colnames = ['task', 'tid', 'cpu', 'timestamp', 'event', 'prev_comm', 'prev_pid', 'prev_prio', 'prev_state', '-',
                    'next_comm', 'next_pid', 'next_prio']
        sched_switch_df = pd.read_csv(perf_export_dir + filename, index_col=False, names=colnames, header=None,
                                       delim_whitespace=True)
        del sched_switch_df['-']

        sched_switch_df['tid'] = pd.to_numeric(sched_switch_df['tid'])
        sched_switch_df['cpu'] = sched_switch_df['cpu'].map(lambda cpu: re.sub("[^0-9]", "", cpu))
        sched_switch_df['cpu'] = pd.to_numeric(sched_switch_df['cpu'])
        sched_switch_df['timestamp'] = sched_switch_df['timestamp'].map(lambda timestamp: timestamp.replace(":", ""))
        sched_switch_df['timestamp'] = pd.to_numeric(sched_switch_df['timestamp'])
        sched_switch_df['prev_comm'] = sched_switch_df['prev_comm'].map(
            lambda prev_comm: prev_comm.replace("prev_comm=", ""))
        sched_switch_df['prev_pid'] = sched_switch_df['prev_pid'].map(
            lambda prev_pid: prev_pid.replace("prev_pid=", ""))
        sched_switch_df['prev_prio'] = sched_switch_df['prev_prio'].map(
            lambda prev_prio: prev_prio.replace("prev_prio=", ""))
        sched_switch_df['next_comm'] = sched_switch_df['next_comm'].map(
            lambda next_comm: next_comm.replace("next_comm=", ""))
        sched_switch_df['next_pid'] = sched_switch_df['next_pid'].map(
            lambda next_pid: next_pid.replace("next_pid=", ""))
        sched_switch_df['next_prio'] = sched_switch_df['next_prio'].map(
            lambda next_prio: next_prio.replace("next_prio=", "").rstrip())
        sched_switch_df['event'] = sched_switch_df['event'].map(
            lambda event: event.rstrip(':'))

    except:
        print("Error: Dataimport of sched_switch_list failed.")
        os.sys.exit()
    return sched_switch_df

def import_data_from_irq(perf_export_dir, filename):
    """
    Open irq:irq_handler_entry.dump file and import data
    :param perf_export_dir: Path to file
    :param filename: name of file
    :return: pandas dataframe of events on success, otherwise -1
    """
    try:
        colnames = ['task', 'tid', 'cpu', 'timestamp', 'event', 'irq', 'irq_source']
        irq_handler_entry_list = pd.read_csv(perf_export_dir + filename, index_col=False, names=colnames, header=None,
                                             delim_whitespace=True)

        irq_handler_entry_list['tid'] = pd.to_numeric(irq_handler_entry_list['tid'])
        irq_handler_entry_list['cpu'] = irq_handler_entry_list['cpu'].map(lambda cpu: re.sub("[^0-9]", "", cpu))
        irq_handler_entry_list['cpu'] = pd.to_numeric(irq_handler_entry_list['cpu'])
        irq_handler_entry_list['timestamp'] = irq_handler_entry_list['timestamp'].map(
            lambda timestamp: timestamp.replace(":", ""))
        irq_handler_entry_list['timestamp'] = pd.to_numeric(irq_handler_entry_list['timestamp'])
        irq_handler_entry_list['irq'] = irq_handler_entry_list['irq'].map(lambda irq: irq.replace("irq=", ""))
        irq_handler_entry_list['irq_source'] = irq_handler_entry_list['irq_source'].map(
            lambda irq_source: irq_source.replace("name=", ""))
        irq_handler_entry_list['event'] = irq_handler_entry_list['event'].map(
            lambda event: event.rstrip(':'))
    except OSError as err:
        print("OS error: {0}".format(err))
        os.sys.exit()
    return irq_handler_entry_list

def Application():
    perf_import_dir = args.perf_dir
    entry_timestamp = args.timestamp[0]
    exit_timestamp = args.timestamp[1]

    print("perfEventDumper")
    print("Importing Files from: " + perf_import_dir)

    sched_switch_df = import_data_from_sched_switch(perf_import_dir, SCHED_SWITCH_FILENAME)
    irq_handler_entry_df = import_data_from_irq(perf_import_dir, IRQ_HANDLER_ENTRY_FILENAME)
    irq_handler_exit_df = import_data_from_irq(perf_import_dir, IRQ_HANDLER_EXIT_FILENAME)

    perf_data_df = pd.concat([sched_switch_df, irq_handler_entry_df, irq_handler_exit_df], ignore_index=True)
    perf_data_df = perf_data_df.sort_values('timestamp')

    extracted_dump = perf_data_df.loc[(perf_data_df['timestamp'] > entry_timestamp) & (perf_data_df['timestamp'] < exit_timestamp)]

    output_table = prettytable.PrettyTable(
        ['Timestamp Absolute', 'Time relativ to start [ms]', 'Time relativ to last probe [ms]', 'Interrupted by'])

    time_prev=entry_timestamp
    for index, event in extracted_dump.iterrows():
        if event['event'] == 'sched:sched_switch':
            output_table.add_row([event['timestamp'], round((event['timestamp'] - entry_timestamp)*1e3,3),
                                  round((event['timestamp'] - time_prev)*1e3,3),
                                  event['event'] + ": task: " + event['next_comm'] + " prio: " + event['next_prio']])
        elif event['event'] == 'irq:irq_handler_entry' or event['event'] == 'irq:irq_handler_exit':
            output_table.add_row([event['timestamp'], round((event['timestamp'] - entry_timestamp)*1e3,3),
                                  round((event['timestamp'] - time_prev) * 1e3, 3),
                                  event['event'] + ": " + event['irq_source']])
        time_prev = event['timestamp']
    print(output_table)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--perf_dir", nargs="?", action='store', const='true',
                        help="Folder to load files from")
    parser.add_argument("-t", "--timestamp", nargs='*', action='store', type=float,
                        help="Specify entry and exit timestamp. Format: time_entry time_exit")
    args = parser.parse_args()

    if args.perf_dir is None:
        parser.error("Directory to load files from needs to be specified")
    return args

if __name__ == "__main__":
    args = parse_args()
    Application()