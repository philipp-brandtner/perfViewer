"""
perfViewer
Module: drawplots
Responsible: Brandtner Philipp

Definition of data plot functions

"""

import matplotlib.legend_handler
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.container import ErrorbarContainer


class re_order_errorbarHandler(matplotlib.legend_handler.HandlerErrorbar):
    """
    Sub-class the standard error-bar handler
    """
    def create_artists(self, *args, **kwargs):
        #  call the parent class function
        a_list = matplotlib.legend_handler.HandlerErrorbar.create_artists(self, *args, **kwargs)
        # re-order the artist list, only the first artist is added to the
        # legend artist list, this is the one that corresponds to the markers
        a_list = a_list[-1:] + a_list[:-1]
        return a_list

def draw_cpu_plot(cpu_list):
    # Draw Process Data
    plt.figure(2)
    fig = plt.gcf()
    fig.canvas.set_window_title('perfViewer')
    ax = plt.gca()

    sc_list = []
    cpu_yticks = []
    cpu_ylabels = []
    # Plot Scatter for CPU data
    cmap = plt.cm.RdYlGn
    i = 0

    for cpu in cpu_list:
        ax.broken_barh(cpu.get_cpu_runtime_tuple()[0], (10+i*10, 9), facecolors='tab:blue')

        if cpu.get_cpu_number() == 0:
            sc_list.append(plt.scatter(*zip(*cpu.get_task_switch_tuple(15)),
                                       c='red', s=5, cmap=cmap, label='sched:switch'))
        else:
            sc_list.append(plt.scatter(*zip(*cpu.get_task_switch_tuple(25)),
                                       c='red', s=5, cmap=cmap))
        cpu_ylabels.append('CPU ' + str(cpu.get_cpu_number()))
        cpu_yticks.append(15 + 10 * i)
        i += 1

    ax.set_title('per CPU System Usage')
    ax.set_ylim(5, 15 + i*10)
    ax.set_xlabel('Time [s]')
    ax.set_yticks(cpu_yticks)
    ax.set_yticklabels(cpu_ylabels)
    ax.grid(True)

    my_handler_map = {ErrorbarContainer: re_order_errorbarHandler(numpoints=2)}


    annot = ax.annotate("", xy=(0, 0), xytext=(20, 20), textcoords="offset points",
                        bbox=dict(boxstyle="round", fc="w"),
                        arrowprops=dict(arrowstyle="->"))
    annot.set_visible(False)

    legend = ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05),
                       fancybox=True, shadow=True, ncol=5, handler_map=my_handler_map)


    lined = dict()
    for legline, origline in zip(legend.legendHandles, sc_list):
        legline.set_picker(5)  # 5 pts tolerance
        lined[legline] = origline

    def onpick(event):
        # on the pick event, find the orig line corresponding to the
        # legend proxy line, and toggle the visibility
        for line in sc_list:
            line.set_visible(not line.get_visible())
        fig.canvas.draw()

    def hover(event):
        """
        Adds scheduling events while hovering over plot data
        """
        vis = annot.get_visible()
        if event.inaxes == ax:
            for scatter in sc_list:
                cont, ind = scatter.contains(event)
                if cont:
                    update_annot(ind, scatter)
                    annot.set_visible(True)
                    fig.canvas.draw_idle()
                else:
                    if vis:
                        annot.set_visible(False)
                        fig.canvas.draw_idle()

    def update_annot(ind, sc):
        """
        Updates annotation on plot
        """
        pos = sc.get_offsets()[ind["ind"][0]]
        annot.xy = pos

        sc_index = sc_list.index(sc)
        task_switch_element = cpu_list[sc_index].get_cpu_task_switching_text(pos[0])
        text = "Prev Task: {0}, {1}\nSched Task: {2}, {3}"\
            .format(task_switch_element[0][1], task_switch_element[0][2],
                    task_switch_element[0][3], task_switch_element[0][4])
        annot.set_text(text)
        annot.get_bbox_patch().set_facecolor('tab:gray')
        annot.get_bbox_patch().set_alpha(0.4)

    fig.canvas.mpl_connect('pick_event', onpick)
    fig.canvas.mpl_connect("motion_notify_event", hover)
    plt.show()


def draw_task_plot(tasks_list, probe_list=None):
    plt.figure(1)
    fig = plt.gcf()
    fig.canvas.set_window_title('perfViewer')
    ax = plt.gca()

    i = 0
    task_ylabels = []
    task_yticks = []
    color_array = []

    red_patch = mpatches.Patch(color='red', label='CPU 0')
    orange_patch = mpatches.Patch(color='orange', label='CPU 1')
    green_patch = mpatches.Patch(color='green', label='CPU 2')
    blue_patch = mpatches.Patch(color='blue', label='CPU 3')

    # Plot Scatter for CPU data
    sc_list = []
    cmap = plt.cm.RdYlGn

    for task in tasks_list:
        for x in task.get_cpu_to_runtime():
            if x==0:
                color_array.append('tab:red')
                patches = [red_patch]
            elif x==1:
                color_array.append('tab:orange')
                patches = [red_patch, orange_patch]
            elif x==2:
                color_array.append('tab:green')
                patches = [red_patch, orange_patch, green_patch]
            elif x==3:
                color_array.append('tab:blue')
                patches = [red_patch, orange_patch, green_patch, blue_patch]
        ax.broken_barh(task.get_task_runtime()[0], (10 * i + 10, 9), facecolors=color_array)
        task_ylabels.append(task.get_task_name())
        task_yticks.append(15 + 10 * i)
        i += 1

    plt.legend(handles=patches)

    ax.set_ylim(5, 15 + i * 10)
    ax.set_yticks(task_yticks)
    ax.set_yticklabels(task_ylabels)
    ax.set_title('per Task System Usage')
    ax.set_xlabel('Time [s]')
    ax.grid(True)

    annot = ax.annotate("", xy=(0, 0), xytext=(20, 20), textcoords="offset points",
                        bbox=dict(boxstyle="round", fc="w"),
                        arrowprops=dict(arrowstyle="->"))
    annot.set_visible(False)

    if probe_list is not None:
        probe_scatter_list = []
        for probe in probe_list:
            if not probe.trace_data.empty:
                # Get Task in which probe was running
                probe_tasks = probe.trace_data['task']
                probe_tasks_tid = probe.trace_data['tid']

                probe_tasks_index = [tasks_list.index(task) for task_name, task_tid in zip(probe_tasks, probe_tasks_tid)
                                     for task in tasks_list if task_name == task.name and task_tid == task.get_task_number()]

                data = [(trace_data['timestamp'], trace_data['event'], 15 + task_index*10) for (trace_data_index, trace_data), task_index
                        in zip(probe.trace_data.iterrows(), probe_tasks_index)]

                if data != []:
                    data_red = [(point[0], point[2])for point in data if 'entry' in point[1]]
                    data_blue = [(point[0], point[2])for point in data if 'exit' in point[1]]

                    if len(sc_list) > 0:
                        sc_list.append(plt.scatter(*zip(*data_red), c='green', s=5, cmap=cmap))
                        sc_list.append(plt.scatter(*zip(*data_blue), c='blue', s=5, cmap=cmap))
                    else:
                        sc_list.append(plt.scatter(*zip(*data_red), c='green', s=5, cmap=cmap, label='probe_tracepoint_entry'))
                        sc_list.append(plt.scatter(*zip(*data_blue), c='blue', s=5, cmap=cmap, label='probe_tracepoint_exit'))
                    probe_scatter_list.append(probe_list.index(probe))
                    probe_scatter_list.append(probe_list.index(probe))

        my_handler_map = {ErrorbarContainer: re_order_errorbarHandler(numpoints=2)}
        legend = ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05),
                           fancybox=True, shadow=True, ncol=5, handler_map=my_handler_map)

        lined = dict()
        for legline, origline in zip(legend.legendHandles, sc_list):
            legline.set_picker(5)  # 5 pts tolerance
            lined[legline] = origline

        def onpick(event):
            # on the pick event, find the orig line corresponding to the
            # legend proxy line, and toggle the visibility
            for line in sc_list:
                line.set_visible(not line.get_visible())
            fig.canvas.draw()

        def hover(event):
            """
            Adds scheduling events while hovering over plot data
            """
            vis = annot.get_visible()
            if event.inaxes == ax:
                for scatter in sc_list:
                    cont, ind = scatter.contains(event)
                    if cont:
                        update_annot(ind, scatter)
                        annot.set_visible(True)
                        fig.canvas.draw_idle()
                    else:
                        if vis:
                            annot.set_visible(False)
                            fig.canvas.draw_idle()

        def update_annot(ind, sc):
            """
            Updates annotation on plot
            """
            pos = sc.get_offsets()[ind["ind"][0]]
            annot.xy = pos

            sc_index = sc_list.index(sc)
            probe = probe_list[probe_scatter_list[sc_index]]

            selected_trace = [trace for (trace_index, trace) in probe.trace_data.iterrows()
                              if trace['timestamp'] == pos[0]]
            text = "Time: {0}, Event: {1}"\
                .format(selected_trace[0]['timestamp'], selected_trace[0]['event'])
            annot.set_text(text)
            annot.get_bbox_patch().set_facecolor('tab:gray')
            annot.get_bbox_patch().set_alpha(0.4)

        fig.canvas.mpl_connect('pick_event', onpick)
        fig.canvas.mpl_connect("motion_notify_event", hover)
