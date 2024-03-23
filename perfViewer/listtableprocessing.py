"""
perfViewer
Module: listtableprocessing
Responsible: Brandtner Philipp
Description: Processes task, cpu and probe list and extracts tables
"""

import prettytable
import task
import cpu

def create_tracing_list_and_table(scheduler_irq_tracing_files):
    """
    Create PrettyTable for Tracing data
    :param probe_list: List of all probes
    :param sched_switch_list: List with context switch information
    :param irq_handler_entry_list: List with irq information
    :return: PrettyTable of Tracing Data
    """
    probe_list = scheduler_irq_tracing_files["PROBE_LIST"]
    sched_switch_df = scheduler_irq_tracing_files["SCHED_SWITCH_DF"]
    irq_handler_entry_df = scheduler_irq_tracing_files["IRQ_HANDLER_ENTRY_DF"]

    probe_tracepoint_table = prettytable.PrettyTable(
        ['Num', 'Probe', '# Calls', 'Min [ms]', 'Max [ms]', 'Median [ms]',
         '# CSW', 'CSW: [count]', 'CSW @ Max:[count]', 'CSW @ Min:[count]',
         '# IRQ', 'IRQ: [count]', 'IRQ @ Max:[count]', 'IRQ @ Min:[count]'])

    for probe in probe_list:
        probe.calculate_function_runtimes()
        probe.calculate_tracepoint_statistics()
        probe.evaluate_contextswitch_irq_collisions(sched_switch_df, irq_handler_entry_df)
        probe_table_entry = probe.get_probe_table_entry()
        probe_table_entry.insert(0, str(probe_list.index(probe)))
        probe_tracepoint_table.add_row(probe_table_entry)
    return probe_list, probe_tracepoint_table

def create_task_list_and_table(scheduler_irq_tracing_files, ssh_scp_commander, tid_pid_mapping):
    """
    Create Task Runtime Table, Task Wakeup Table
    :param scheduler_irq_tracing_files: Dictonary of input files
    :param ssh_scp_commander: Instance of ssh_scp_commander to receive tid_pid_mapping
    :param tid_pid_mapping: tid_pid data for offline processing
    :return: Task Runtime List, Task Runtime Table, Task Wakeup Table
    """
    sched_wakeup_df = scheduler_irq_tracing_files["SCHED_WAKEUP_DF"]
    tasks_list = task.process_task_runtime(scheduler_irq_tracing_files)
    tasks_list = task.process_sched_wakeup_list_for_tasks(sched_wakeup_df, tasks_list)

    if tid_pid_mapping is None:
        tasks_list = task.get_pid_from_target(tasks_list, ssh_scp_commander)
    else:
        tasks_list = task.import_pid_from_file(tasks_list, tid_pid_mapping)

    tasks_list.sort(key=lambda x: x.numberofwakeups, reverse=True)

    task_table_wakeup = prettytable.PrettyTable(['Task', 'TID', 'PID', 'Total Wakeups'])
    for Task in tasks_list:
        task_table_wakeup.add_row(Task.get_task_wakeup_table_entry())

    tasks_list.sort(key=lambda x: x.total_runtime, reverse=True)

    task_table = prettytable.PrettyTable(['Task', 'TID', 'PID', 'Total Runtime [ms]',
                                          'Minimum Runtime [ms]', 'Maximum Runtime [ms]',
                                          'Average Runtime [ms]'])
    for _task in tasks_list:
        task_table_entry = _task.get_task_table_entry()
        if task_table_entry[3] != '-':
            task_table.add_row(task_table_entry)

    return tasks_list, task_table, task_table_wakeup

def create_cpu_list_and_table(record_duration, scheduler_irq_tracing_files, task_list):
    """
    Create CPU Runtime Table, CPU Wakeup Table
    :param record_duration: Record duration of perf dump
    :param scheduler_irq_tracing_files: Dictionary of input files
    :param task_list: List of Tasks
    :return: CPU List, CPU Runtime Table, CPU Idle Table (only if power:cpu_idle files are available)
    """
    sched_switch_df = scheduler_irq_tracing_files["SCHED_SWITCH_DF"]
    cpu_idle_df = scheduler_irq_tracing_files["CPU_IDLE_DF"]

    cpu_list = []
    cpu_list = cpu.process_sched_switch_list(cpu_list, task_list, sched_switch_df)

    # Sort Tasks with Total_Runtime as Attribute
    cpu_list.sort(key=lambda x: x.number, reverse=False)

    # Print CPU Table
    cpu_table = prettytable.PrettyTable(['CPU', 'Total Task Runtime [ms]', 'Usage [%]'])
    for CPU in cpu_list:
        CPU.set_sleeptime_and_percentage(record_duration)
        cpu_table.add_row(CPU.get_cpu_table_entry())

    if len(cpu_idle_df) > 0:
        cpu_idle_state = cpu.process_cpu_idle_list(cpu_idle_df, record_duration)
        # Create CPU Idle Table
        cpu_idle_table = prettytable.PrettyTable(['CPU', 'busy-idle [ms]', 'sleep state [ms]', '% in busy-idle',
                                                  '% in sleep state', '% in idle-busy and sleep-state'])
        for lines in cpu_idle_state:
            cpu_idle_table.add_row(lines)
    else:
        cpu_idle_table = None

    return cpu_list, cpu_table, cpu_idle_table

def print_table(record_duration, task_table, task_wakeup_table, cpu_table, cpu_idle_table=None, tracing_table=None):
    """ Print task, task_wakeup, cpu and tracing table """
    print("\n")
    print("Record Duration: " + str(record_duration))
    print("\n")
    print("CPU Runtime Information:")
    print(cpu_table)
    print("\n")
    if cpu_idle_table is not None:
        print("CPU Sleep Information:")
        print(cpu_idle_table)
        print("\n")
    print("Task Runtime Information:")
    print(task_table)
    print("\n")
    print("Task Wakeup Information:")
    print(task_wakeup_table)
    if tracing_table is not None:
        print("\n")
        print("Function Tracing Information:")
        print(tracing_table)

def print_delta_table(tracing_delta_table=None):
    """ Print tracing delta table """
    if tracing_delta_table is not None:
        print("\n")
        print(tracing_delta_table)
