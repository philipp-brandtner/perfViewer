"""
perfViewer
Module: probe
Responsible: Brandtner Philipp

Definition of Class for perf probes

"""

import subprocess
import statistics
import prettytable
import re
import pandas as pd

def calculate_probe_deltas(scheduler_irq_tracing_files, probes_delta):
    """
    Calculate time differences between perf probes.
    :param scheduler_irq_tracing_files: Dictonary of all input files
    :param probes_delta: List of probes to calculate differences from. Ex: [5,6] --> Calculate differnce between probe
                         5 and 6
    :return: Tracing_Delta_Table
    """
    probe_list = scheduler_irq_tracing_files["PROBE_LIST"]
    tracing_delta_table = prettytable.PrettyTable(
        ['Probe 1', 'Timestamps Probe 1', 'Probe 2', 'Timestamps Probe 2', 'Delta between Probe entries[ms]'])

    if probes_delta != ['']:
        for x in probes_delta:
            delta = ""
            probe_entry_index, probe_exit_index = x.split(",")

            probe_entry = probe_list[int(probe_entry_index)]
            probe_exit = probe_list[int(probe_exit_index)]

            if probe_entry_index == probe_exit_index:
                for runtime_entry_1, runtime_entry_2 in zip(probe_entry.function_runtimes,
                                                            probe_entry.function_runtimes[1:]):
                    delta += str(round((runtime_entry_2[0] - runtime_entry_1[0])*1e3,3)) + "\n"
            else:
                for runtime_entry, runtime_exit in zip(probe_entry.function_runtimes, probe_exit.function_runtimes):
                    delta += str(round((runtime_entry[0] - runtime_exit[0])*1e3, 3)) + "\n"
            delta = delta.rstrip()
            tracing_delta_table.add_row([probe_entry.function,
                                         ('\n').join([str(runtime[0]) for runtime in probe_entry.function_runtimes]),
                                         probe_exit.function,
                                         ('\n').join([str(runtime[0]) for runtime in probe_exit.function_runtimes]),
                                         delta])
    else:
        tracing_delta_table = None
    if probes_delta == []:
        tracing_delta_table = None
    return tracing_delta_table


class Probe:
    """ Probe Class """

    def __init__(self, executable, executable_path, namespace,function, arguments):
        self.executable = executable
        self.executable_path = executable_path
        self.executable_path_local = ''
        self.namespace = namespace
        self.function = function
        self.arguments = arguments
        self.mangled_function = 0
        self.function_address = 0
        self.probe_name = ''
        self.probe_commands = []
        self.trace_data = pd.DataFrame(columns=['task', 'tid', 'cpu', 'timestamp', 'event', 'address'])
        self.function_runtimes = []

        self.runtime_min = 0
        self.runtime_max = 0
        self.runtime_avg = 0
        self.runtime_median = 0

        self.csw_collision_events = pd.DataFrame(columns=['task', 'tid', 'cpu', 'timestamp', 'event',
                                                                     'prev_comm', 'prev_pid', 'prev_prio', 'prev_state',
                                                                     '-', 'next_comm', 'next_pid', 'next_prio'])
        self.csw_collision_events_max_runtime = pd.DataFrame(columns=['task', 'tid', 'cpu', 'timestamp', 'event',
                                                                     'prev_comm', 'prev_pid', 'prev_prio', 'prev_state',
                                                                     '-', 'next_comm', 'next_pid', 'next_prio'])
        self.csw_collision_events_min_runtime = pd.DataFrame(columns=['task', 'tid', 'cpu', 'timestamp', 'event',
                                                                      'prev_comm', 'prev_pid', 'prev_prio',
                                                                      'prev_state',
                                                                      '-', 'next_comm', 'next_pid', 'next_prio'])
        self.irq_collision_events = pd.DataFrame(columns=['task', 'tid', 'cpu', 'timestamp', 'event', 'irq',
                                                          'irq_source'])
        self.irq_collision_events_max_runtime = pd.DataFrame(columns=['task', 'tid', 'cpu', 'timestamp', 'event', 'irq',
                                                          'irq_source'])
        self.irq_collision_events_min_runtime = pd.DataFrame(columns=['task', 'tid', 'cpu', 'timestamp', 'event', 'irq',
                                                                      'irq_source'])


    def __eq__(self, other):
        return self.executable_path == other.executable_path and \
               self.executable == other.executable and \
               self.namespace == other.namespace and \
               self.function == other.function and \
               self.arguments == other.arguments

    def get_executable_path(self):
        """ Return executable path """
        return self.executable_path

    def get_executable(self):
        """ Return name of executable """
        return self.executable

    def set_local_executable_path(self, local_executable_path):
        self.executable_path_local = local_executable_path

    def mangle_function_name(self, perf_export_dir):
        """ Return the g++ mangled function name """
        if self.executable_path_local.endswith(self.executable):
            self.executable_path_local = self.executable_path_local[:-len(self.executable)]
        if self.executable_path_local != '':
            command = 'cd ' + self.executable_path_local + '; readelf -sW ' + self.executable + ' | c++filt |grep ' + self.function
        else:
            command = 'cd ' + perf_export_dir + '; readelf -sW ' + self.executable + ' | c++filt |grep ' + self.function
        proc = subprocess.Popen(command, shell=True, executable='/bin/bash', stdout=subprocess.PIPE)
        std_out = str(proc.communicate()[0]).split('\\n')

        index = []
        for line in std_out:
            if self.namespace == '':
                if self.function in line and not '::' + self.function in line and 'FUNC' in line:
                    index.append(std_out.index(line))
            else:
                if self.namespace + '::' + self.function in line and not 'non-virtual thunk to ' in line:
                    index.append(std_out.index(line))

        if len(index) > 1:
            index_filtered = []
            for i in index:
                if [] != re.findall('\\b'+ self.function + '\\b', std_out[i]):
                    index_filtered.append(i)
            if len(index_filtered) == 1:
                index = int(index_filtered[0])
            else:
                print("Warning: Can not mangel names of overloaded functions.")
                print("Please choose correct function prototype:")
                for i in index:
                    print(str(i)+": "+ std_out[i])
                index = int(input("Number of correct function:"))
        elif len(index) == 1:
            index = index[0]
        elif len(index) == 0:
            print('Failure: Could not find any match for function: ' + self.namespace + "::" + self.function)
            print('Usually this failure occurs due to namespace not equal to namespace in executable')

        if self.executable_path_local != '':
            command = 'cd ' + self.executable_path_local + '; readelf -sW ' + self.executable + ' |grep ' + self.function
        else:
            command = 'cd ' + perf_export_dir + '; readelf -sW ' + self.executable + ' |grep ' + self.function

        proc = subprocess.Popen(command, shell=True, executable='/bin/bash', stdout=subprocess.PIPE)
        std_out = str(proc.communicate()[0]).split('\\n')
        std_out[0] = std_out[0][3:]

        self.mangled_function = std_out[index].split(" ")[-1]
        self.function_address = [x for x in std_out[index].split(" ") if x][1]

    def create_probe_command(self, x, max_probe_function_len):
        if self.namespace == '':
            self.probe_name = self.function
        else:
            self.probe_name = self.namespace + "__" + self.function

        if len(self.probe_name) > max_probe_function_len:
            self.probe_name = self.probe_name[-max_probe_function_len:]

        if x == 'address':
            self.probe_commands.append(
                "perf probe -x ../.." + self.executable_path + self.executable + " " + self.probe_name + "_entry=" + "\'0x" + self.function_address + "\'\n")
            self.probe_commands.append(
                "perf probe -x ../.." + self.executable_path + self.executable + " " + self.probe_name + "_exit=" + "\'0x" + self.function_address + "\'%return" + "\n")

        elif x == 'name':
            self.probe_commands.append(
                "perf probe -x ../.." + self.executable_path + self.executable + " " + self.probe_name + "_entry=" + self.mangled_function + "\n")
            self.probe_commands.append(
                "perf probe -x ../.." + self.executable_path + self.executable + " " + self.probe_name + "_exit=" + self.mangled_function + "%return" + "\n")

    def calculate_function_runtimes(self):
        if not self.trace_data.empty:
            i = 0
            while i < len(self.trace_data) and i != (len(self.trace_data)-1):
                entry_i = self.trace_data.iloc[i]
                entry_next = self.trace_data.iloc[i+1]

                if '_entry' in entry_i['event'] and '_exit__return' in entry_next['event']:
                    self.function_runtimes.append([entry_i['timestamp'], entry_next['timestamp'],
                                                   entry_next['timestamp'] - entry_i['timestamp']])
                    i += 1
                i += 1

    def calculate_tracepoint_statistics(self):

        if len(self.function_runtimes) != 0:
            self.runtime_min = min(self.function_runtimes, key=lambda x: x[2])
            self.runtime_max = max(self.function_runtimes, key=lambda x: x[2])

            self.runtime_avg = statistics.mean([runtime[2] for runtime in self.function_runtimes])
            self.runtime_median = statistics.median([runtime[2] for runtime in self.function_runtimes])
        else:
            self.runtime_min = 'no Data'
            self.runtime_max = 'no Data'
            self.runtime_avg = 'no Data'
            self.runtime_median = 'no Data'


    def get_probe_table_entry(self):
        def get_event_output_string(events):
            if not events.empty:
                if 'next_comm' in events.columns:
                    event_sources = events['next_comm']
                elif 'irq_source' in events.columns:
                    event_sources = events['irq_source']
                event_comm_sources_filtered = event_sources.value_counts().to_dict()
                event_output=''
                for key in event_comm_sources_filtered:
                    event_output+= key + ":" + str(event_comm_sources_filtered[key]) + '\n'
                event_output = event_output.rstrip()
            else:
                event_output = 'no Data'
            return event_output

        csw_output = get_event_output_string(self.csw_collision_events)
        irq_output = get_event_output_string(self.irq_collision_events)
        csw_max_runtime_output = get_event_output_string(self.csw_collision_events_max_runtime)
        csw_min_runtime_output = get_event_output_string(self.csw_collision_events_min_runtime)
        irq_max_runtime_output = get_event_output_string(self.irq_collision_events_max_runtime)
        irq_min_runtime_output = get_event_output_string(self.irq_collision_events_min_runtime)

        if self.runtime_min == 'no Data' and self.runtime_max == 'no Data' and self.runtime_median == 'no Data':
            return [self.function, len(self.function_runtimes), self.runtime_min,self.runtime_max, self.runtime_median,
                    str(len(self.csw_collision_events)), csw_output, csw_max_runtime_output, csw_min_runtime_output,
                    str(len(self.irq_collision_events)), irq_output, irq_max_runtime_output, irq_min_runtime_output]
        else:
            return [self.function, len(self.function_runtimes), round(self.runtime_min[2] * 1e3, 3),
                    round(self.runtime_max[2] * 1e3, 3), round(self.runtime_median * 1e3, 3),
                    str(len(self.csw_collision_events)), csw_output, csw_max_runtime_output, csw_min_runtime_output,
                    str(len(self.irq_collision_events)), irq_output, irq_max_runtime_output, irq_min_runtime_output]

    def evaluate_contextswitch_irq_collisions(self, sched_switch_df, irq_handler_entry_df):
        if len(self.trace_data) != 0:
            for runtime in self.function_runtimes:
                self.csw_collision_events = self.csw_collision_events.append(sched_switch_df.loc[
                    (sched_switch_df['timestamp'] < runtime[1]) &
                    (sched_switch_df['timestamp'] > runtime[0])])

                self.irq_collision_events=self.irq_collision_events.append(irq_handler_entry_df.loc[
                        (irq_handler_entry_df['timestamp'] < runtime[1]) &
                        (irq_handler_entry_df['timestamp'] > runtime[0])])

            # Search for interrupts and context_switches at max runtime element
            self.csw_collision_events_max_runtime = self.csw_collision_events_max_runtime.append(
                sched_switch_df.loc[(sched_switch_df['timestamp'] < self.runtime_max[1]) &
                                    (sched_switch_df['timestamp'] > self.runtime_max[0])])

            self.irq_collision_events_max_runtime = self.irq_collision_events_max_runtime.append(
                irq_handler_entry_df.loc[(irq_handler_entry_df['timestamp'] < self.runtime_max[1]) &
                                         (irq_handler_entry_df['timestamp'] > self.runtime_max[0])])

            # Search for interrupts and context_switches at min runtime element
            self.csw_collision_events_min_runtime = self.csw_collision_events_min_runtime.append(
                sched_switch_df.loc[(sched_switch_df['timestamp'] < self.runtime_min[1]) &
                                    (sched_switch_df['timestamp'] > self.runtime_min[0])])

            self.irq_collision_events_min_runtime = self.irq_collision_events_min_runtime.append(
                irq_handler_entry_df.loc[(irq_handler_entry_df['timestamp'] < self.runtime_min[1]) &
                                         (irq_handler_entry_df['timestamp'] > self.runtime_min[0])])
