"""
perfViewer
Module: dataimporterexporter
Responsible: Brandtner Philipp
Description:
Imports data from following perf dump files:
    - sched:sched_stat_runtime.dump
    - sched:sched_switch.dump
    - sched:sched_wakeup.dump
    - sched:sched_migrate.dump
    - irq:irq_handler_entry.dump
    - probes_*.list
    - perf.data.probe_*_entry.dump and perf.data.probe_*_exit__return.dump
Exports data to following files:
    - Tracing_Data*.csv
    - input_args.txt
    - tid_pid.txt
    - Console_Output*.csv

"""

import re
import os
from probe import Probe
import glob
import pandas as pd
import csv

def import_data_from_sched_runtime(perf_import_dir, filename):
    """
    Open sched:sched_stat_runtime.dump file and import data
    :param perf_import_dir: Path to file
    :param filename: name of file
    :return: Pandas dataframe of events on success, otherwise -1
    """
    try:
        colnames = ['task', 'tid', 'cpu', 'timestamp', 'event', 'comm', 'pid', 'runtime', 'ns', 'vruntime', 'ns2']
        sched_runtime_df = pd.read_csv(perf_import_dir + filename, index_col=False, names=colnames, header=None,
                                       delim_whitespace=True)
        del sched_runtime_df['ns'], sched_runtime_df['ns2']

        sched_runtime_df['tid'] = pd.to_numeric(sched_runtime_df['tid'])
        sched_runtime_df['cpu'] = sched_runtime_df['cpu'].map(lambda cpu: re.sub("[^0-9]", "", cpu))
        sched_runtime_df['cpu'] = pd.to_numeric(sched_runtime_df['cpu'])
        sched_runtime_df['timestamp'] = sched_runtime_df['timestamp'].map(lambda timestamp: timestamp.replace(":", ""))
        sched_runtime_df['timestamp'] = pd.to_numeric(sched_runtime_df['timestamp'])
        sched_runtime_df['comm'] = sched_runtime_df['comm'].map(lambda comm: comm.replace("comm=", ""))
        sched_runtime_df['pid'] = sched_runtime_df['pid'].map(lambda pid: pid.replace("pid=", ""))
        sched_runtime_df['runtime'] = sched_runtime_df['runtime'].map(lambda runtime: runtime.replace("runtime=", ""))
        sched_runtime_df['runtime'] = pd.to_numeric(sched_runtime_df['runtime'])
        sched_runtime_df['vruntime'] = sched_runtime_df['vruntime'].map(lambda vruntime:
                                                                        vruntime.replace("vruntime=", ""))
        sched_runtime_df['vruntime'] = pd.to_numeric(sched_runtime_df['vruntime'])
        sched_runtime_df['event'] = sched_runtime_df['event'].map(
            lambda event: event.rstrip(':'))

    except:
        print("Error: Dataimport of sched_runtime failed.")
        os.sys.exit()

    return sched_runtime_df

def import_data_from_cpu_idle(perf_import_dir, filename):
    """
    Open power:cpu_idle.dump file and import data
    :param perf_import_dir: Path to file
    :param filename: name of file
    :return: Pandas dataframe of events on success, otherwise -1
    """

    try:
        colnames = ['task', 'tid', 'cpu', 'timestamp', 'event', 'state', 'cpu_id']
        cpu_idle_df = pd.read_csv(perf_import_dir + filename, index_col=False, names=colnames, header=None,
                                  delim_whitespace=True)

        cpu_idle_df['tid'] = pd.to_numeric(cpu_idle_df['tid'])
        cpu_idle_df['cpu'] = cpu_idle_df['cpu'].map(lambda cpu: re.sub("[^0-9]", "", cpu))
        cpu_idle_df['cpu'] = pd.to_numeric(cpu_idle_df['cpu'])
        cpu_idle_df['timestamp'] = cpu_idle_df['timestamp'].map(lambda timestamp: timestamp.replace(":", ""))
        cpu_idle_df['timestamp'] = pd.to_numeric(cpu_idle_df['timestamp'])
        cpu_idle_df['state'] = cpu_idle_df['state'].map(lambda state: state.replace("state=", ""))
        cpu_idle_df['state'] = pd.to_numeric(cpu_idle_df['state'])
        cpu_idle_df['cpu_id'] = cpu_idle_df['cpu_id'].map(lambda state: state.replace("cpu_id=", "").rstrip())
        cpu_idle_df['cpu_id'] = pd.to_numeric(cpu_idle_df['cpu_id'])
        cpu_idle_df['event'] = cpu_idle_df['event'].map(
            lambda event: event.rstrip(':'))

    except:
        print("Error: Dataimport of cpu_idle_list failed.")
        os.sys.exit()
    return cpu_idle_df

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

def import_data_from_sched_migrate(perf_export_dir, filename):
    """
    Open sched:sched_migrate.dump file and import data
    :param perf_export_dir: Path to file
    :param filename: name of file
    :return: pandas dataframe of events on success, otherwise -1
    """

    try:
        colnames = ['task', 'tid', 'cpu', 'timestamp', 'command', 'pid', 'prio', 'orig_cpu', 'dest_cpu']
        sched_migrate_df = pd.read_csv(perf_export_dir + filename, index_col=False, names=colnames, header=None,
                                       delim_whitespace=True)

        sched_migrate_df['tid'] = pd.to_numeric(sched_migrate_df['tid'])
        sched_migrate_df['cpu'] = sched_migrate_df['cpu'].map(lambda cpu: re.sub("[^0-9]", "", cpu))
        sched_migrate_df['cpu'] = pd.to_numeric(sched_migrate_df['cpu'])
        sched_migrate_df['timestamp'] = sched_migrate_df['timestamp'].map(lambda timestamp: timestamp.replace(":", ""))
        sched_migrate_df['timestamp'] = pd.to_numeric(sched_migrate_df['timestamp'])
    except OSError as err:
        print("OS error: {0}".format(err))
        os.sys.exit()

    return sched_migrate_df

def import_data_from_sched_waking(perf_export_dir, filename):
    """
    Open sched:sched_waking.dump file and import data
    :param perf_export_dir: Path to file
    :param filename: name of file
    :return: pandas dataframe of events on success, otherwise -1
    """
    try:
        colnames = ['task', 'tid', 'cpu', 'timestamp', 'event', 'comm', 'pid', 'prio', 'target']
        sched_waking_df = pd.read_csv(perf_export_dir + filename, index_col=False, names=colnames, header=None,
                                      delim_whitespace=True)

        sched_waking_df['tid'] = pd.to_numeric(sched_waking_df['tid'])
        sched_waking_df['cpu'] = sched_waking_df['cpu'].map(lambda cpu: re.sub("[^0-9]", "", cpu))
        sched_waking_df['cpu'] = pd.to_numeric(sched_waking_df['cpu'])
        sched_waking_df['timestamp'] = sched_waking_df['timestamp'].map(lambda timestamp: timestamp.replace(":", ""))
        sched_waking_df['timestamp'] = pd.to_numeric(sched_waking_df['timestamp'])
        sched_waking_df['comm'] = sched_waking_df['comm'].map(lambda comm: comm.replace("comm=", ""))
        sched_waking_df['pid'] = sched_waking_df['pid'].map(lambda pid: pid.replace("pid=", ""))
        sched_waking_df['pid'] = pd.to_numeric(sched_waking_df['pid'])
        sched_waking_df['prio'] = sched_waking_df['prio'].map(lambda prio: prio.replace("prio=", ""))
        sched_waking_df['prio'] = pd.to_numeric(sched_waking_df['prio'])
        sched_waking_df['target'] = sched_waking_df['target'].map(lambda target: target.replace("target_cpu=", ""))
        sched_waking_df['event'] = sched_waking_df['event'].map(
            lambda event: event.rstrip(':'))
    except OSError as err:
        print("OS error: {0}".format(err))
        os.sys.exit()
    return sched_waking_df

def import_data_from_sched_wakeup(perf_export_dir, filename):
    """
    Open sched:sched_wakeup.dump file and import data
    :param perf_export_dir: Path to file
    :param filename: name of file
    :return: pandas dataframe of events on success, otherwise -1
    """
    try:
        colnames = ['task', 'tid', 'cpu', 'timestamp', 'event', 'comm', 'pid', 'prio', 'target']
        sched_wakeup_df = pd.read_csv(perf_export_dir + filename, index_col=False, names=colnames, header=None,
                                      delim_whitespace=True)

        sched_wakeup_df['tid'] = pd.to_numeric(sched_wakeup_df ['tid'])
        sched_wakeup_df['cpu'] = sched_wakeup_df ['cpu'].map(lambda cpu: re.sub("[^0-9]", "", cpu))
        sched_wakeup_df['cpu'] = pd.to_numeric(sched_wakeup_df ['cpu'])
        sched_wakeup_df['timestamp'] = sched_wakeup_df ['timestamp'].map(lambda timestamp: timestamp.replace(":", ""))
        sched_wakeup_df['timestamp'] = pd.to_numeric(sched_wakeup_df ['timestamp'])
        sched_wakeup_df['comm'] = sched_wakeup_df ['comm'].map(lambda comm: comm.replace("comm=", ""))
        sched_wakeup_df['pid'] = sched_wakeup_df ['pid'].map(lambda pid: pid.replace("pid=", ""))
        sched_wakeup_df['pid'] = pd.to_numeric(sched_wakeup_df['pid'])
        sched_wakeup_df['prio'] = sched_wakeup_df ['prio'].map(lambda prio: prio.replace("prio=", ""))
        sched_wakeup_df['prio'] = pd.to_numeric(sched_wakeup_df['prio'])
        sched_wakeup_df['target'] = sched_wakeup_df['target'].map(lambda target: target.replace("target_cpu=", ""))
        sched_wakeup_df['event'] = sched_wakeup_df['event'].map(
            lambda event: event.rstrip(':'))
    except OSError as err:
        print("OS error: {0}".format(err))
        os.sys.exit()
    return sched_wakeup_df

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

def import_probe_list(conf, probe_files):
    """
    Open probe.list file and function names to probe
    :param perf_export_dir: Path to file
    :param filename: name of file
    :return: pandas dataframe of events on success, otherwise -1
    """
    Probes = []
    for file in probe_files:
        try:
            f_probe_list = open(file, "r")
            if f_probe_list.mode == 'r':
                probe_list = f_probe_list.readlines()
                probe_list = [entry for entry in probe_list if entry[0] != '#' and entry[0] != '\n']

                probe_executable = probe_list[0].split("=")[1].strip()
                probe_executable_path = probe_list[1].split("=")[1].strip()

                del probe_list[0], probe_list[0]

                for probe in probe_list:
                    probe_namespace_func_args = probe.rstrip()

                    probe_namespace_function = probe_namespace_func_args.split('(')[0]
                    probe_arguments = probe_namespace_func_args.split('(')[1].split(')')[0]

                    if '::' in probe_namespace_function:
                        probe_namespace, probe_function = probe_namespace_function.split('::')
                    else:
                        probe_namespace = ''
                        probe_function = probe_namespace_function

                    new_probe = Probe(probe_executable, probe_executable_path, probe_namespace, probe_function,
                                      probe_arguments)
                    Probes.append(new_probe)
        except OSError as err:
            print("OS error: {0}".format(err))
            os.sys.exit()
    return Probes

def import_probe_tracing_data(perf_export_dir, probe_list):
    """
    Open a file with tracing data of a perf probe and import data
    :param perf_export_dir: Path to file
    :param filename: name of file
    :return: pandas dataframe of events on success, otherwise -1
    """
    colnames_entry = ['task', 'tid', 'cpu', 'timestamp', 'event', 'address']
    colnames_exit = ['task', 'tid', 'cpu', 'timestamp', 'event', 'address1', '-', 'address']
    try:
        for probe in probe_list:
            filename_entry = "perf.data.probe_" + probe.executable + ":" + probe.probe_name + "_entry.dump"
            filename_exit = "perf.data.probe_" + probe.executable + ":" + probe.probe_name + "_exit__return.dump"

            probe_entry_df = pd.read_csv(perf_export_dir + filename_entry, index_col=False, names=colnames_entry,
                                         header=None, delim_whitespace=True)
            probe_exit_df = pd.read_csv(perf_export_dir + filename_exit, index_col=False, names=colnames_exit,
                                        header=None, delim_whitespace=True)

            del probe_exit_df['-'], probe_exit_df['address1']

            probe_entry_df['tid'] = pd.to_numeric(probe_entry_df['tid'])
            probe_entry_df['cpu'] = probe_entry_df['cpu'].map(lambda cpu: re.sub("[^0-9]", "", cpu))
            probe_entry_df['cpu'] = pd.to_numeric(probe_entry_df['cpu'])
            probe_entry_df['timestamp'] = probe_entry_df['timestamp'].map(
                lambda timestamp: timestamp.replace(":", ""))
            probe_entry_df['timestamp'] = pd.to_numeric(probe_entry_df['timestamp'])
            probe_entry_df['event'] = probe_entry_df['event'].map(
                lambda event: event.rstrip(':'))

            probe.trace_data = probe.trace_data.append(probe_entry_df)

            probe_exit_df['tid'] = pd.to_numeric(probe_exit_df['tid'])
            probe_exit_df['cpu'] = probe_exit_df['cpu'].map(lambda cpu: re.sub("[^0-9]", "", cpu))
            probe_exit_df['cpu'] = pd.to_numeric(probe_exit_df['cpu'])
            probe_exit_df['timestamp'] = probe_exit_df['timestamp'].map(
                lambda timestamp: timestamp.replace(":", ""))
            probe_exit_df['timestamp'] = pd.to_numeric(probe_exit_df['timestamp'])
            probe_exit_df['event'] = probe_exit_df['event'].map(
                lambda event: event.rstrip(':'))

            probe.trace_data = probe.trace_data.append(probe_exit_df)

            probe.trace_data = probe.trace_data.sort_values('timestamp')
            probe.trace_data = probe.trace_data.reset_index(drop=True)
    except OSError as err:
        print("OS error: {0}".format(err))
        os.sys.exit()

def import_offline_probe_tracing_data(perf_import_dir, conf):
    """
    Search for all perf.data.probe_* files in SampleData directory. Create new probe instances from each file and
    and return these as Probes list
    :param perf_import_dir: Path to file
    :param conf: configuration file from perfviewer
    :return: list of probes or empty list
    """
    probe_files = glob.glob(perf_import_dir + 'perf.data.probe_*.dump')
    Probes = []

    if not len(probe_files) == 0:
        try:
            for probe in probe_files:
                executable_function_name = re.sub(perf_import_dir+"perf.data.probe_", '', probe)
                executable_function_name = re.sub("\.dump$", '', executable_function_name)
                executable = executable_function_name.split(':')[0]
                function_name = re.sub(executable + ':','',executable_function_name)
                function_name = re.sub('_entry', '', function_name)
                function_name = re.sub('_exit__return', '', function_name)

                new_probe = Probe(executable,'', '', function_name,'')

                check_Probes = [True for entry in Probes if entry == new_probe]
                if not any(check_Probes):
                    Probes.append(new_probe)
        except:
            print("Error: Dataimport of probe_list failed.")
            os.sys.exit()
    return Probes

def export_console_output_txt(perf_import_dir, cpu_table, cpu_sleep_table, task_table, task_wakeup_table, time,
                          trace_table = None, tracing_delta_table=None):
    """
    Export output of console to text file
    :param perf_import_dir: Path to SampleData directory
    :param cpu_table: CPU Runtime table
    :param cpu_sleep_table: table of cpu sleep states
    :param task_table: Task runtime table
    :param task_wakeup_table: Task wakeup table
    :param time: perfViewer start time
    :param trace_table: Table of probe traces
    :param tracing_delta_table: table of delta times
    """

    cpu_table_txt = cpu_table.get_string()
    task_table_txt = task_table.get_string()
    task_wakeup_table_txt = task_wakeup_table.get_string()

    table = cpu_table_txt

    if cpu_sleep_table is not None:
        cpu_sleep_txt = cpu_sleep_table.get_string()
        table += "\n\n\n" + cpu_sleep_txt

    table += "\n\n\n" + task_table_txt + "\n\n\n" + task_wakeup_table_txt

    if trace_table is not None:
        trace_table_txt = trace_table.get_string()
        table += "\n\n\n" + trace_table_txt

    if tracing_delta_table is not None:
        tracing_delta_table_txt = tracing_delta_table.get_string()
        table += "\n\n\n" + tracing_delta_table_txt

    try:
        with open(perf_import_dir + "/Console_Output"+ time + ".txt", "w") as file:
            file.write(table)
    except OSError as err:
        print("OS error: {0}".format(err))
        os.sys.exit()


def export_console_output_csv(perf_import_dir, cpu_table, cpu_sleep_table, task_table, task_wakeup_table, time,
                          trace_table = None, tracing_delta_table=None):
    """
    Export output of console to csv file
    :param perf_import_dir: Path to SampleData directory
    :param cpu_table: CPU Runtime table
    :param cpu_sleep_table: table of cpu sleep states
    :param task_table: Task runtime table
    :param task_wakeup_table: Task wakeup table
    :param time: perfViewer start time
    :param trace_table: Table of probe traces
    :param tracing_delta_table: table of delta times
    """

    def table_to_csv(table_txt):
        result = []

        for line in table_txt.splitlines():
            splitdata = line.split("|")
            if len(splitdata) == 1:
                continue
            del splitdata[0], splitdata[-1]
            linedata = []
            for field in splitdata:
                field = field.strip()
                if field:
                    linedata.append(field)
                else:
                    linedata.append('')
            result.append(linedata)
        return result

    cpu_table_txt = cpu_table.get_string()
    task_table_txt = task_table.get_string()
    task_wakeup_table_txt = task_wakeup_table.get_string()

    cpu_table_csv = table_to_csv(cpu_table_txt)
    task_table_csv = table_to_csv(task_table_txt)
    task_wakeup_table_csv = table_to_csv(task_wakeup_table_txt)

    try:
        with open(perf_import_dir + "/Console_Output" + time + ".csv", "w") as csvfile:
            writer = csv.writer(csvfile, delimiter=';')
            writer.writerows(cpu_table_csv)

            writer.writerows([''])

            if cpu_sleep_table is not None:
                cpu_sleep_txt = cpu_sleep_table.get_string()
                cpu_sleep_csv = table_to_csv(cpu_sleep_txt)
                writer.writerows(cpu_sleep_csv)
                writer.writerows([''])

            writer.writerows(task_table_csv)
            writer.writerows([''])
            writer.writerows(task_wakeup_table_csv)
            writer.writerows([''])

            if trace_table is not None:
                trace_table_txt = trace_table.get_string()
                trace_table_csv = table_to_csv(trace_table_txt)
                writer.writerows(trace_table_csv)
                writer.writerows([''])

            if tracing_delta_table is not None:
                tracing_delta_table_txt = tracing_delta_table.get_string()
                tracing_delta_table_csv = table_to_csv(tracing_delta_table_txt)
                writer.writerows(tracing_delta_table_csv)
                writer.writerows([''])
    except OSError as err:
        print("OS error: {0}".format(err))
        os.sys.exit()

def export_tracing_data_txt(scheduler_irq_tracing_files, perf_import_dir, time):
    """
    Export raw tracing data to Tracing_Data_*.csv
    :param scheduler_irq_tracing_files:
    :param perf_import_dir: SampleDirectory path
    :param time: time at perfviewer statup
    """
    probe_list = scheduler_irq_tracing_files["PROBE_LIST"]
    runtime_string = "Tracing Data of each probe: [Timestamp_Entry, Timestamp_Exit, Delta] \n"

    for probe in probe_list:
        runtime_string += "\n" + probe.function + '\n'
        for runtime in probe.function_runtimes:
            runtime_string += str(runtime[0]) + "," + str(runtime[1]) + "," + str(runtime[2]) + "\n"
    try:
        with open(perf_import_dir + "/Tracing_Data" + time + ".txt", "w") as file:
            file.write(runtime_string)
    except OSError as err:
        print("OS error: {0}".format(err))
        os.sys.exit()


def export_tracing_data_csv(scheduler_irq_tracing_files, perf_import_dir, time):
    """
    Export raw tracing data to Tracing_Data_*.csv
    :param scheduler_irq_tracing_files:
    :param perf_import_dir: SampleDirectory path
    :param time: time at perfviewer statup
    """
    probe_list = scheduler_irq_tracing_files["PROBE_LIST"]
    runtime_csv = []
    runtime_csv.append(["Tracing Data of each probe: [Timestamp_Entry, Timestamp_Exit, Delta]"])

    for probe in probe_list:
        runtime_csv.append([probe.function])
        for runtime in probe.function_runtimes:
            runtime_csv.append([str(runtime[0]), str(runtime[1]), str(runtime[2])])

    try:
        with open(perf_import_dir + "/Tracing_Data" + time + ".csv", "w") as csvfile:
            writer = csv.writer(csvfile, delimiter=';')
            writer.writerows(runtime_csv)
    except OSError as err:
        print("OS error: {0}".format(err))
        os.sys.exit()

def export_input_args(perf_import_dir, record_duration):
    """
    Export input args to input_args.txt Currently only recordduration is exported for offline usage.
    :param perf_import_dir: Path to SampleData directory
    :param record_duration: Duration of perf record
    """
    input_args_string = "Input Args: \n"
    input_args_string += "Record Duration: " + str(record_duration)
    try:
        with open(perf_import_dir + "/input_args.txt", "w") as file:
            file.write(input_args_string)
    except OSError as err:
        print("OS error: {0}".format(err))
        os.sys.exit()

def import_input_args(perf_import_dir):
    """
    Open input_args.txt file and import data like record duration
    :param perf_import_dir: Path to SampleData directory
    :return: recordduration
    """
    try:
        file_input_args = open(perf_import_dir + "input_args.txt", "r")
        if file_input_args.mode == 'r':
            file_input_args_lines = file_input_args.readlines()
            for line in file_input_args_lines:
                if "Record Duration: " in line:
                    record_duration = float(line.split(' ')[2].rstrip())
    except OSError as err:
        print("OS error: {0}".format(err))
        os.sys.exit()
    return record_duration

def export_tid_pid(perf_import_dir, task_list):
    """
    Export mapping of tid and pid for offline usage
    :param perf_import_dir: Import data from SampleData directory
    :param task_list: list of tasts
    """
    tid_pid_string = "TID, PID mapping File: \n"

    for task in task_list:
        tid_pid_string += str(task.get_task_number()) + " " + str(task.get_task_pid()) + '\n'
    try:
        with open(perf_import_dir + "/tid_pid.txt", "w") as file:
            file.write(tid_pid_string)
    except OSError as err:
        print("OS error: {0}".format(err))
        os.sys.exit()

def import_tid_pid(perf_import_dir):
    """
    Open tid_pid.txt file and import mapping of tid and pid
    :param perf_import_dir: Path to file
    :param filename: name of file
    :return: List of pid and tid
    """
    tid_pid_mapping = []
    try:
        file_input_args = open(perf_import_dir + "tid_pid.txt", "r")
        if file_input_args.mode == 'r':
            file_input_args_lines = file_input_args.readlines()
            for line in file_input_args_lines:
                tid_pid_mapping.append(line.split(' '))
    except OSError as err:
        print("OS error: {0}".format(err))
        os.sys.exit()
    return tid_pid_mapping
