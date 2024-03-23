"""
perfViewer
Module: cpu
Responsible: Brandtner Philipp

Definition of Class for CPU

"""

def process_sched_switch_list(cpu_list, task_list, sched_switch_df):
    """
    Process scheduler switch events
    :param cpu_list: List of CPUs
    :param task_list: List of already processed tasks
    :param sched_switch_df: Dataframe of sched_switch events
    :return: cpu_list
    """

    for task in task_list:
        task_runtime = task.get_task_runtime()
        cpu_indices = task.get_cpu_to_runtime()

        for runtime_entry, cpu_index in zip(task_runtime[0], cpu_indices):
            runtime_start = runtime_entry[0]
            runtime_duration = runtime_entry[1]

            new_cpu = CPU(int(cpu_index))
            if not new_cpu in cpu_list:
                cpu_list.append(new_cpu)
            index = cpu_list.index(new_cpu)

            cpu_list[index].set_cpu_runtime(task.get_task_number(),
                                            runtime_start,
                                            runtime_duration)

    for switch_event_index, switch_event in sched_switch_df.iterrows():
        new_cpu = CPU(switch_event['cpu'])
        if not new_cpu in cpu_list:
            cpu_list.append(new_cpu)
        index = cpu_list.index(new_cpu)

        cpu_list[index].set_cpu_task_switching(switch_event['timestamp'], switch_event['prev_comm'],
                                                                switch_event['prev_prio'], switch_event['next_comm'],
                                                                switch_event['next_prio'])
    return cpu_list

def process_cpu_idle_list(cpu_idle_df, record_duration):
    """
    Calculate duration in idle states from power:cpu_idle
    :param cpu_idle_df: pandas dataframe of power:cpu_idle
    :param record_duration: perf record duration
    :return: cpu_idle_state table
    """
    num_cpus = 0
    state_change_identifier=4294967295  # perf identifier for idle state change (see perf kernel reference)

    for entry_index, entry in cpu_idle_df.iterrows():
        if num_cpus < entry['cpu']:
            num_cpus+=1
    num_cpus+=1

    previous_timestamps = [0]*num_cpus
    last_idle_state = [0]*num_cpus
    cpu_idle_state = [[0]*2]*num_cpus

    for item_index, item in cpu_idle_df.iterrows():
        if item['state'] != state_change_identifier:
            previous_timestamps[item['cpu']] = item['timestamp']
            last_idle_state[item['cpu']] = item['state']
        else:
            cpu_idle_state[item['cpu']][last_idle_state[item['cpu']]] += item['timestamp'] -\
                                                                         previous_timestamps[item['cpu']]
    i = 0
    for lines in cpu_idle_state:
        lines[0] = round(lines[0]*1e3, 3)
        lines[1] = round(lines[1]*1e3, 3)
        lines.insert(0, i)
        if lines[2] + lines[1] > 0:
            lines.insert(3, round(100 * lines[1]*1e-3 / record_duration, 3))
            lines.insert(4, round(100 * lines[2]*1e-3 / record_duration, 3))
            lines.insert(5, round(100 * (lines[1]*1e-3 + lines[2]*1e-3) / record_duration, 3))
        else:
            lines.insert(3, 0)
            lines.insert(4, 0)
            lines.insert(5, 0)
        i += 1

    return cpu_idle_state

class CPU:
    """
    CPU Class
    """
    def __init__(self, cpu_number):
        self.number = cpu_number
        self.total_runtime = 0
        self.total_sleeptime = 0
        self.runtime = []
        self.task_switch = []
        self.usage_percent = 0

    def __eq__(self, other):
        return self.number == other.number

    def get_cpu_number(self):
        """ get CPU number"""
        return self.number

    def get_cpu_runtime_tuple(self):
        """ get cpu runtime data """
        runtime_data = []
        runtime_data.append([tuple(row[1]) for row in self.runtime])
        return runtime_data

    def get_task_switch_tuple(self, yvalue):
        """ get cpu task switch data """
        return [(float(row[0]), yvalue) for row in self.task_switch]

    def get_cpu_task_switching_text(self, time):
        """ get task switch information """
        return [row for row in self.task_switch if float(row[0]) == time]

    def get_cpu_table_entry(self):
        """ get entry for cpu table """
        return [self.number, round(self.total_runtime*1e3, 3), round(self.usage_percent * 100, 3)]

    def set_cpu_runtime(self, task, start_time, duration):
        """ receive entry for cpu runtime """
        self.runtime.append([task, tuple([start_time, duration])])
        self.total_runtime += duration

    def set_cpu_task_switching(self, time, old_task, old_task_prio, new_task, new_task_prio):
        """ receive task switch data """
        self.task_switch.append([time, old_task, old_task_prio, new_task, new_task_prio])

    def set_sleeptime_and_percentage(self, total_log_time):
        """ set overall sleeptime and calculate percentage to overall runtime """
        self.total_sleeptime = total_log_time - self.total_runtime
        self.usage_percent = self.total_runtime / total_log_time
