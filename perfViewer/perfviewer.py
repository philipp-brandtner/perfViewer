"""
perfViewer
Module: perfviewer
Responsible: Brandtner Philipp
"""

import sshscpcommander
import dataimporterexporter
import inputparser
import drawplots
import listtableprocessing
import probe

def import_target_files(perf_import_dir):
    """ Import scheduler, irq and cpu-idle data for later processing """
    imported_files = dict()

    sched_migrate_df = dataimporterexporter.import_data_from_sched_migrate(perf_import_dir,
                                                                             conf.get("SCHED_MIGRATE_FILENAME"))
    sched_runtime_df = dataimporterexporter.import_data_from_sched_runtime(perf_import_dir,
                                                                             conf.get("SCHED_RUNTIME_FILENAME"))
    sched_switch_df = dataimporterexporter.import_data_from_sched_switch(perf_import_dir,
                                                                           conf.get("SCHED_SWITCH_FILENAME"))
    sched_waking_df = dataimporterexporter.import_data_from_sched_waking(perf_import_dir,
                                                                           conf.get("SCHED_WAKING_FILENAME"))
    sched_wakeup_df = dataimporterexporter.import_data_from_sched_wakeup(perf_import_dir,
                                                                         conf.get("SCHED_WAKEUP_FILENAME"))
    irq_handler_entry_df = dataimporterexporter.import_data_from_irq(perf_import_dir,
                                                                       conf.get("IRQ_HANDLER_ENTRY_FILENAME"))
    irq_handler_exit_df = dataimporterexporter.import_data_from_irq(perf_import_dir,
                                                                     conf.get("IRQ_HANDLER_EXIT_FILENAME"))
    cpu_idle_df = dataimporterexporter.import_data_from_cpu_idle(perf_import_dir,
                                                                       conf.get("CPU_IDLE_FILENAME"))

    imported_files['SCHED_MIGRATE_DF'] = sched_migrate_df
    imported_files['SCHED_RUNTIME_DF'] = sched_runtime_df
    imported_files['SCHED_SWITCH_DF'] = sched_switch_df
    imported_files['SCHED_WAKING_DF'] = sched_waking_df
    imported_files['SCHED_WAKEUP_DF'] = sched_wakeup_df
    imported_files['IRQ_HANDLER_ENTRY_DF'] = irq_handler_entry_df
    imported_files['IRQ_HANDLER_EXIT_DF'] = irq_handler_exit_df
    imported_files['CPU_IDLE_DF'] = cpu_idle_df

    return imported_files

def load_files_from_target_with_tracing(ip, username, password, pid, record_duration, perf_import_dir,
                                        probe_list_filename, local_executables):
    """ Load files from target and activate tracing utilities"""
    ssh_scp_commander = sshscpcommander.SSHSCPCommander()
    ssh_scp_commander.connect_to_target(ip, username, password)
    probe_list = dataimporterexporter.import_probe_list(conf, probe_list_filename)
    ssh_scp_commander.load_files_with_probes(pid, record_duration, probe_list, perf_import_dir, local_executables,
                                             conf.get("PERF_PROBE_MAX_FUNCTION_LEN"))

    dataimporterexporter.import_probe_tracing_data(perf_import_dir, probe_list)

    imported_files = import_target_files(perf_import_dir)
    imported_files["PROBE_LIST"] = probe_list

    return imported_files, ssh_scp_commander

def load_files_from_target_without_tracing(ip, username, password, pid, record_duration, perf_import_dir):
    """ Load files from target and without tracing utilities"""
    ssh_scp_commander = sshscpcommander.SSHSCPCommander()
    ssh_scp_commander.connect_to_target(ip, username, password)
    ssh_scp_commander.load_files_without_probes(pid, record_duration, perf_import_dir)

    imported_files = import_target_files(perf_import_dir)

    return imported_files, ssh_scp_commander

def offline_usage_with_tracing(perf_import_dir):
    """ Use files from perf_import_dir and activate tracing utilities """
    probe_list = dataimporterexporter.import_offline_probe_tracing_data(perf_import_dir, conf)
    scheduler_irq_tracing_files = import_target_files(perf_import_dir)

    dataimporterexporter.import_probe_tracing_data(perf_import_dir, probe_list)

    scheduler_irq_tracing_files["PROBE_LIST"] = probe_list

    return scheduler_irq_tracing_files

def offline_usage_without_tracing(perf_import_dir):
    """ Use files from perf_import_dir and deactivate tracing utilities """
    scheduler_irq_tracing_files = import_target_files(perf_import_dir)

    return scheduler_irq_tracing_files

def print_welcome_string(ip,username,password,load_files_from_target, tracing, perf_import_dir, probe_list_filename,
                         local_executables):
    print("perfViewer Version: " + conf.get("VERSION"))
    if load_files_from_target and tracing:
        print("starting with following arguments and activated function tracing:")
        print("- Loading files from target with IP: " + ip)
        print("- Username: " + username)
        print("- Password: " + password)
        print("- Importing files to path: " + perf_import_dir)
        print("- Using probes from file: " + ', '.join(probe_list_filename))
        if local_executables is not None:
            print("- Using local executables for demangling: " + ' '.join(local_executables) + "\n")
    elif load_files_from_target and not tracing:
        print("starting perfViewer with following arguments and deactivated function tracing:")
        print("- Loading files from target with IP: " + ip)
        print("- Username: " + username)
        print("- Password: " + password + "\n")
        print("- Importing files to path: " + perf_import_dir + "\n")
    elif not load_files_from_target and tracing:
        print("offline usage - Loading files from path: " + perf_import_dir)
        print("Function Tracing is enabled")
    elif not load_files_from_target and not tracing:
        print("offline usage - Loading files from path: " + perf_import_dir)
        print("Function Tracing is disabled")

def Application():
    username = args.username
    password = args.password
    ip = additional_args.get("TARGET_IP")
    perf_import_dir = additional_args.get("PERF_IMPORT_DIR")
    load_files_from_target = additional_args.get("LOAD_FILES_FROM_TARGET")
    record_duration = args.record_duration
    pid = args.pid
    tracing = additional_args["TRACING"]
    probe_list_filename = additional_args["PROBE_LIST_FILENAME"]
    local_executables = args.executable

    ssh_scp_commander = None
    tid_pid_mapping = None

    print_welcome_string(ip,username,password,load_files_from_target, tracing, perf_import_dir, probe_list_filename,
                         local_executables)

    if load_files_from_target and tracing:
        scheduler_irq_tracing_files, ssh_scp_commander = load_files_from_target_with_tracing(
            ip, args.username, password, pid, record_duration, perf_import_dir, probe_list_filename, local_executables)
        probe_list, tracing_table = listtableprocessing.create_tracing_list_and_table(scheduler_irq_tracing_files)
        dataimporterexporter.export_input_args(perf_import_dir, record_duration)
    elif load_files_from_target and not tracing:
        scheduler_irq_tracing_files, ssh_scp_commander = load_files_from_target_without_tracing(
            ip, args.username, password, pid, record_duration, perf_import_dir)
        dataimporterexporter.export_input_args(perf_import_dir, record_duration)
    elif not load_files_from_target and tracing:
        record_duration = dataimporterexporter.import_input_args(perf_import_dir)
        tid_pid_mapping = dataimporterexporter.import_tid_pid(perf_import_dir)
        scheduler_irq_tracing_files = offline_usage_with_tracing(perf_import_dir)
        probe_list, tracing_table = listtableprocessing.create_tracing_list_and_table(scheduler_irq_tracing_files)
    elif not load_files_from_target and not tracing:
        record_duration = dataimporterexporter.import_input_args(perf_import_dir)
        tid_pid_mapping = dataimporterexporter.import_tid_pid(perf_import_dir)
        scheduler_irq_tracing_files = offline_usage_without_tracing(perf_import_dir)

    print("Starting file processing...")
    task_list, task_table, task_table_wakeup = listtableprocessing.create_task_list_and_table(
        scheduler_irq_tracing_files, ssh_scp_commander, tid_pid_mapping)
    cpu_list, cpu_table, cpu_idle_table = listtableprocessing.create_cpu_list_and_table(
        record_duration, scheduler_irq_tracing_files, task_list)

    if ssh_scp_commander is not None:
        ssh_scp_commander.close_connection()

    if load_files_from_target:
        dataimporterexporter.export_tid_pid(perf_import_dir, task_list)

    if tracing:
        listtableprocessing.print_table(record_duration, task_table, task_table_wakeup, cpu_table, cpu_idle_table,
                                        tracing_table)

        probes_delta = input("Calculate delta in execution between probe entries? Format: 1,2; 1,3\n").split(";")
        tracing_delta_table = probe.calculate_probe_deltas(scheduler_irq_tracing_files, probes_delta)
        listtableprocessing.print_delta_table(tracing_delta_table)

        if load_files_from_target:
            dataimporterexporter.export_console_output_txt(perf_import_dir, cpu_table, cpu_idle_table, task_table,
                                                       task_table_wakeup, time, tracing_table,tracing_delta_table)
            dataimporterexporter.export_console_output_csv(perf_import_dir, cpu_table, cpu_idle_table, task_table,
                                                       task_table_wakeup, time, tracing_table, tracing_delta_table)
            dataimporterexporter.export_tracing_data_txt(scheduler_irq_tracing_files, perf_import_dir, time)
            dataimporterexporter.export_tracing_data_csv(scheduler_irq_tracing_files, perf_import_dir, time)
        drawplots.draw_task_plot(task_list, probe_list)
        drawplots.draw_cpu_plot(cpu_list)
    else:
        listtableprocessing.print_table(record_duration, task_table, task_table_wakeup, cpu_table, cpu_idle_table)
        if load_files_from_target:
            dataimporterexporter.export_console_output_txt(perf_import_dir, cpu_table, cpu_idle_table, task_table,
                                                       task_table_wakeup, time)
            dataimporterexporter.export_console_output_csv(perf_import_dir, cpu_table, cpu_idle_table, task_table,
                                                       task_table_wakeup, time)
        drawplots.draw_task_plot(task_list)
        drawplots.draw_cpu_plot(cpu_list)

def conf_init():
    config = dict()
    exec(open('perfviewer.config').read(), config)
    return config

if __name__ == "__main__":
    args = inputparser.parse_args()
    conf = conf_init()
    additional_args, time = inputparser.get_additional_args(args, conf)
    Application()