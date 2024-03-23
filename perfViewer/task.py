"""
perfViewer
Module: Task
Responsible: Brandtner Philipp
"""

import pandas as pd

def import_pid_from_file(tasks_list, tid_pid_mapping):
    """
    Set PID of task objects with tid_pid_mapping. Only in offline mode necessary
    :param tasks_list: List of tasks
    :param tid_pid_mapping: Imported mapping of tid pid
    """
    del tid_pid_mapping[0]

    for entry in tid_pid_mapping:
        task_index = [tasks_list.index(task) for task in tasks_list if int(entry[0]) == task.get_task_number()]
        tasks_list[task_index[0]].set_pid(entry[1].rstrip())

    return tasks_list

def get_pid_from_target(tasks_list, ssh_scp_commander):
    """
    Connect to target and check /proc for pid
    :param tasks_list: List of all tasks
    :param ssh_scp_commander: Instance of ssh_scp_commander
    """
    if ssh_scp_commander is not None:
        task_tids = []
        for task in tasks_list:
            task_tids.append(task.get_task_number())
        pid_tid = ssh_scp_commander.get_pid(task_tids)

        for pid, tid in pid_tid:
            for task in tasks_list:
                if task.get_task_number() == int(tid):
                    task.set_pid(int(pid))

    return tasks_list


def process_task_runtime(scheduler_irq_tracing_files):
    """
    Routine to calculate runtime of tasks from perf dump files.
    :param scheduler_irq_tracing_files: Dictonary of files
    :param ssh_scp_commander: Instance of ssh_scp_commander to download files
    :return: List of tasks
    """
    tasks_list = []
    sched_migrate_df = scheduler_irq_tracing_files["SCHED_MIGRATE_DF"]
    sched_runtime_df = scheduler_irq_tracing_files["SCHED_RUNTIME_DF"]
    sched_switch_df = scheduler_irq_tracing_files["SCHED_SWITCH_DF"]
    sched_wakeup_df = scheduler_irq_tracing_files["SCHED_WAKEUP_DF"]
    sched_waking_df = scheduler_irq_tracing_files["SCHED_WAKING_DF"]
    irq_handler_entry_df = scheduler_irq_tracing_files['IRQ_HANDLER_ENTRY_DF']
    irq_handler_exit_df = scheduler_irq_tracing_files['IRQ_HANDLER_EXIT_DF']
    cpu_idle_df = scheduler_irq_tracing_files['CPU_IDLE_DF']

    perf_data_df = pd.concat([sched_migrate_df, sched_runtime_df, sched_switch_df, sched_wakeup_df, sched_waking_df,
                              irq_handler_entry_df, irq_handler_exit_df, cpu_idle_df], ignore_index=True)
    perf_data_df = perf_data_df.sort_values('timestamp')

    perf_data_df = perf_data_df.reset_index(drop=True)
    # process all perf events
    i = 0

    while i < len(perf_data_df):
        entry_i = perf_data_df.iloc[i]
        entry_i_event = entry_i['event']

        if entry_i_event == 'sched:sched_switch':
            runtime_correction = 0
            k = i + 1
            while k < len(perf_data_df):
                entry_k = perf_data_df.iloc[k]
                entry_k_event = entry_k['event']

                if entry_k_event == 'sched:sched_stat_runtime':
                    newtask = Task(entry_k['task'], entry_k['tid'])
                    if newtask not in tasks_list:
                        tasks_list.append(newtask)
                    index = tasks_list.index(newtask)

                    tasks_list[index].set_task_runtime(entry_k['timestamp'], entry_k['timestamp'] + entry_k['runtime'] * 1e-9,
                                                       entry_k['cpu'])
                    while perf_data_df.iloc[k]['event'] != 'sched:sched_switch':
                        k += 1
                    i = k-1
                    break

                elif entry_k_event == 'sched:sched_waking':
                    x = k + 1
                    while True:
                        entry_x = perf_data_df.iloc[x]
                        entry_x_event = entry_x['event']

                        if entry_x_event == 'sched:sched_wakeup':
                            runtime_correction += entry_x['timestamp'] - entry_k['timestamp']
                            k = x + 1
                            break
                        x += 1

                elif entry_k_event == 'irq:softirq_raise':
                    x = k + 1
                    while True:
                        entry_x = perf_data_df.iloc[x]
                        entry_x_event = entry_x['event']

                        if entry_x_event == 'irq:softirq_exit':
                            runtime_correction += entry_x['timestamp'] - entry_k['timestamp']
                            k = x + 1
                            break
                        x += 1

                elif entry_k_event == 'irq:irq_handler_entry':
                    x = k + 1
                    while True:
                        entry_x = perf_data_df.iloc[x]
                        entry_x_event = entry_x['event']

                        if entry_x_event == 'irq:irq_handler_exit':
                            runtime_correction += entry_x['timestamp'] - entry_k['timestamp']
                            k = x + 1
                            break
                        x += 1

                elif entry_k_event == 'power:cpu_idle':
                    x = k + 1
                    while True:
                        entry_x = perf_data_df.iloc[x]
                        entry_x_event = entry_x['event']

                        if entry_x_event == 'power:cpu_idle':
                            runtime_correction += entry_x['timestamp'] - entry_k['timestamp']
                            k = x + 1
                            break
                        x += 1

                elif entry_k_event == 'sched:sched_switch':
                    newtask = Task(entry_k['task'], entry_k['tid'])
                    if newtask not in tasks_list:
                        tasks_list.append(newtask)
                    index = tasks_list.index(newtask)

                    tasks_list[index].set_task_runtime(entry_i['timestamp'],
                                                       entry_k['timestamp'] - runtime_correction,
                                                       entry_i['cpu'])
                    i = k-1
                    break

        elif entry_i_event == 'sched:sched_stat_runtime':
            newtask = Task(entry_i['task'], entry_i['tid'])
            if newtask not in tasks_list:
                tasks_list.append(newtask)
            index = tasks_list.index(newtask)

            tasks_list[index].set_task_runtime(entry_i['timestamp'], entry_i['timestamp'] + entry_i['runtime'] * 1e-9,
                                              entry_i['cpu'])
        i+=1
    return tasks_list

def process_sched_wakeup_list_for_tasks(sched_wakeup_df, tasks_list):
    """ Extracts task data from sched:wakeup event """
    for item_index, item in sched_wakeup_df.iterrows():
        newtask = Task(item['comm'], item['pid'])

        if newtask not in tasks_list:
            tasks_list.append(newtask)
        index = tasks_list.index(newtask)
        tasks_list[index].inc_number_of_wakeup()

    return tasks_list

class Task:
    """ Tasks Class """
    def __init__(self, task_name, task_number):
        self.name = task_name
        self.number = task_number
        self.pid = 0
        self.total_runtime = 0
        self.runtime = []
        self.cpu_to_runtime = []
        self.numberofwakeups = 0

    def __eq__(self, other_task):
        return (self.name == other_task.name) and (self.number == other_task.number)

    def set_pid(self, pid):
        self.pid = pid

    def get_task_name(self):
        """ Returns name of Task """
        return self.name

    def get_task_number(self):
        """ Returns Task number"""
        return self.number

    def get_task_pid(self):
        """ Return PID of Task"""
        return self.pid

    def get_cpu_to_runtime(self):
        """ Return CPUs of runtime data"""
        return self.cpu_to_runtime

    def get_task_runtime(self):
        """ Return runtime array of task"""
        runtime_data = []
        runtime_data.append([tuple(row) for row in self.runtime])
        return runtime_data

    def get_task_table_entry(self):
        """ Return entry for task table """
        if len(self.runtime)>0:
            min_runtime = min(x[1] for x in self.runtime)
            max_runtime = max(x[1] for x in self.runtime)
            average_runtime = sum(x[1] for x in self.runtime)/len(self.runtime)
            return [self.name, self.number, self.pid, round(self.total_runtime*1e3, 3),
                round(min_runtime*1e3, 3), round(max_runtime*1e3, 3), round(average_runtime*1e3, 3)]
        else:
            return [self.name, self.number, self.pid, '-', '-', '-', '-']

    def get_task_wakeup_table_entry(self):
        """ Returns entry for task wakeup table """
        return [self.name, self.number, self.pid, self.numberofwakeups]

    def set_task_runtime(self, start_time, stop_time, cpu):
        """  Add a runtime element to task """
        self.runtime.append([start_time, stop_time-start_time])
        self.cpu_to_runtime.append(cpu)
        self.total_runtime += stop_time-start_time

    def inc_number_of_wakeup(self):
        """  Increment number of wakeups """
        self.numberofwakeups += 1
