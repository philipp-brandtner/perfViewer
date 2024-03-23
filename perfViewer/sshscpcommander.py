"""
perfViewer
Module: SSH_SCP_Commander
Responsible: Brandtner Philipp
Description: Loads files from target via SSH and SCP
"""

import time
import paramiko
from paramiko import SSHClient
from scp import SCPClient
from os import sys
import subprocess

class SSHSCPCommander:
    def __init__(self):
        self.ssh_client = 0
        self.scp_client = 0

    def progress(self, filename, size, sent):
        """
        Call in a loop to create terminal progress bar
        @params:
            iteration   - Required  : current iteration (Int)
            total       - Required  : total iterations (Int)
            prefix      - Optional  : prefix string (Str)
            suffix      - Optional  : suffix string (Str)
            decimals    - Optional  : positive number of decimals in percent complete (Int)
            length      - Optional  : character length of bar (Int)
            fill        - Optional  : bar fill character (Str)
            printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
        """
        iteration = sent
        total = size
        prefix = 'Progress:'
        suffix = 'Complete'
        length = 100
        decimals = 1
        fill = '█'
        printEnd = '\r'

        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        filledLength = int(length * iteration // total)
        bar = fill * filledLength + '-' * (length - filledLength)
        print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end=printEnd)
        # Print New Line on Complete
        if iteration == total:
            print()

    def connect_to_target(self, ip, username, password):
        self.ssh_client = SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            print('Try to connect to target')
            self.ssh_client.connect(hostname=ip, username=username, password=password, timeout=100)
            self.scp_client = SCPClient(self.ssh_client.get_transport(), progress=self.progress)
            print('- Connection established\n')
        except:
            print("- Couldn't connect to target! Check ip, username and password")
            sys.exit()


    def get_pid(self, task_tids):
        tid_pid = []
        try:
            command_directory = 'cd /proc\n'
            command = 'find . -type d \('
            # find . -type d \( -name "9" -o -name "2231" -o -name "0"
            for tid in task_tids:
                command += " -o -name " + "\"" + str(tid) + "\""
            command += " \)\n"

            command = command.replace('-o', '', 1)

            remote_connection = self.ssh_client.invoke_shell()
            self.get_command_results(remote_connection)

            remote_connection.send(command_directory)
            self.get_command_results(remote_connection)
            remote_connection.send(command)
            lines = self.get_command_results(remote_connection)

            lines_splitted = lines.split("\r\n")

            for line in lines_splitted:
                if "task" in line:
                    tid_pid.append((line.split("/")[1], line.split("/")[3]))
        except:
            print("Error: Failed to get pid of task")
            sys.exit()
        return tid_pid

    def turn_probes_off(self, executable):
        """ Turn off probes from each executable """
        try:
            command = "perf probe -d probe_" + executable + ":* \n"

            remote_connection = self.ssh_client.invoke_shell()

            self.get_command_results(remote_connection)

            remote_connection.send(command)
            self.get_command_results(remote_connection)
        except:
            print("Error: Failed to turn off probes of executable: " + executable)
            sys.exit()


    def load_files_with_probes(self, pid, perf_record_seconds, probes_list, perf_export_dir, local_executables, max_probe_function_len):
        command_directory = 'cd ../../tmp \n'
        if pid is None:
            command_sched_record = "perf record -e sched:* -e irq:* -e power:cpu_idle"
        else:
            command_sched_record = "perf record --pid " + ','.join(pid) + " -e sched:* -e irq:* -e power:cpu_idle"

        remote_connection = self.ssh_client.invoke_shell()

        # Change directory to /tmp
        self.get_command_results(remote_connection)
        remote_connection.send(command_directory)
        self.get_command_results(remote_connection)


        if local_executables is not None:
            downloaded_exectuables = local_executables
        else:
            downloaded_exectuables = []
        for probe in probes_list:
            if local_executables is not None:
                if not any(probe.executable in exe for exe in downloaded_exectuables):
                    print("Starting Download of executable: " + probe.executable)
                    try:
                        self.scp_client.get(probe.executable_path + probe.executable, perf_export_dir)
                        downloaded_exectuables.append(probe.executable)
                    except:
                        print("Failed to download executable: " + probe.executable)
                    self.turn_probes_off(probe.executable)
                    command_sched_record += " -e probe_" + probe.executable + ":*"
                elif not probe.executable in command_sched_record:
                    self.turn_probes_off(probe.executable)
                    command_sched_record += " -e probe_" + probe.executable + ":*"
                    probe.set_local_executable_path([exe for exe in downloaded_exectuables if probe.executable in exe][0])
                elif any(probe.executable in exe for exe in local_executables):
                    probe.set_local_executable_path([exe for exe in local_executables if probe.executable in exe][0])
            else:
                if probe.executable not in downloaded_exectuables:
                    print("Starting Download of executable: " + probe.executable)
                    try:
                        self.scp_client.get(probe.executable_path + probe.executable, perf_export_dir)
                        downloaded_exectuables.append(probe.executable)
                    except:
                        print("Failed to download executable: " + probe.executable)
                    self.turn_probes_off(probe.executable)
                    command_sched_record += " -e probe_" + probe.executable + ":*"
        command_sched_record += " --exclude-perf " + "\n"

        for probe in probes_list:
            probe.mangle_function_name(perf_export_dir)
            probe.create_probe_command('address', max_probe_function_len)

            # Send command for function entry
            remote_connection.send(probe.probe_commands[0])
            std_out = self.get_command_results(remote_connection)
            if std_out.find("Failed") != -1:
                print("Warning: Failed to find probe: " + probe.namespace + "::" + probe.function)

            # Send command for function exit
            remote_connection.send(probe.probe_commands[1])
            std_out = self.get_command_results(remote_connection)
            if std_out.find("Failed") != -1:
                print("Warning: Failed to find probe: " + probe.namespace + "::" + probe.function)

        input("Press enter to start recording...")
        remote_connection.send(command_sched_record)
        time.sleep(perf_record_seconds)
        remote_connection.send(chr(3))
        print("Recording finished...")
        self.get_command_results(remote_connection)

        try:
            print("Starting download of perf files")
            self.scp_client.get('../../tmp/perf.data', perf_export_dir)
            command = 'cd ' + perf_export_dir + '; ../perfViewer/perf script --per-event-dump <<< :q'
            subprocess.run(command, shell=True, executable='/bin/bash')

        except:
            print('Download of perf data failed...')
            sys.exit()

    def load_files_without_probes(self, pid, perf_record_seconds, perf_export_dir):
        print('Starting file download without probes')
        command_directory = 'cd ../../tmp \n'
        if pid is None:
            command_sched_record = "perf record -e sched:* -e irq:* -e power:cpu_idle\n"
        else:
            command_sched_record = "perf record --pid " + ','.join(pid) + " -e sched:* -e irq:* -e power:cpu_idle\n"
		
        remote_connection = self.ssh_client.invoke_shell()

        self.get_command_results(remote_connection)
        remote_connection.send(command_directory)
        self.get_command_results(remote_connection)

        input("Press enter to start recording...")
        remote_connection.send(command_sched_record)
        time.sleep(perf_record_seconds)
        remote_connection.send(chr(3))
        print("Recording finished...")
        self.get_command_results(remote_connection)

        try:
            self.scp_client.get('../../tmp/perf.data', perf_export_dir)
            command = 'cd ' + perf_export_dir + '; ../perfViewer/perf script --per-event-dump <<< :q'
            subprocess.run(command, shell=True, executable='/bin/bash')
        except:
            print('Error: Download of perf data failed')
            sys.exit()

    def close_connection(self):
        self.ssh_client.close()
        self.scp_client.close()

    def get_command_results(self, remote_connection):
        output = ''
        while True:
            output += remote_connection.recv(1024).decode('utf-8')
            if 'imx8mm' in output or 'zynqmp' in output:
                break
        return output

