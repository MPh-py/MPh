"""
Distributes a parameter sweep over multiple worker processes.

This demonstration works around the limitation that only a single
Comsol client can run inside one Python process. It leverages the
`multiprocessing` module from Python's standard library to create
several independent subprocesses ("workers") that communicate with
the parent process ("boss") via inter-process queues to pass job
instructions and results back and forth.
"""
__license__ = 'MIT'


########################################
# Dependencies                         #
########################################
import mph                             # Comsol interface
from multiprocessing import Process    # external subprocess
from multiprocessing import Queue      # inter-process queue
from multiprocessing import cpu_count  # number of (logical) cores
from queue import Empty                # queue-is-empty exception
from numpy import insert               # element insertion into array
from matplotlib import pyplot          # data plots


########################################
# Live Plot                            #
########################################

figure = graph = None


def plot_create():
    """Create the plot figure to be updated as simulations are under way."""
    global figure, graph
    figure = pyplot.figure(figsize=(4,3), tight_layout=True)
    figure.canvas.manager.set_window_title('Simulation results')
    axes = figure.add_subplot()
    graph = axes.plot([], [], '.-', color='navy', markersize=20)[0]
    axes.set_xlabel('electrode distance (mm)')
    axes.set_xlim(0, 5)
    axes.set_ylabel('capacitance (pF)')
    axes.set_ylim(0, 3)
    axes.grid()
    pyplot.show(block=False)
    pyplot.ion()


def plot_update(d, C):
    """Updates the live plot with the latest results."""
    x = graph.get_xdata()
    y = graph.get_ydata()
    i = x.searchsorted(d)
    x = insert(x, i, d)
    y = insert(y, i, C)
    graph.set_xdata(x)
    graph.set_ydata(y)
    figure.canvas.draw()
    figure.canvas.flush_events()


def plot_final():
    """Displays the final plot when all simulations are done."""
    pyplot.ioff()
    pyplot.show()


########################################
# Workers                              #
########################################

def worker(jobs, results):
    """Performs jobs and delivers the results."""
    client = mph.start(cores=1)
    model = client.load('../tests/capacitor.mph')
    while True:
        try:
            d = jobs.get(block=False)
        except Empty:
            break
        model.parameter('d', f'{d} [mm]')
        model.solve('static')
        C = model.evaluate('2*es.intWe/U^2', 'pF')
        results.put((d, C))


########################################
# Boss                                 #
########################################

def boss():
    """Hires workers, assigns jobs, and collects the results."""
    jobs = Queue()
    values = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]
    for d in values:
        jobs.put(d)
    results = Queue()

    processes = []
    workers = cpu_count()
    for n in range(workers):
        process = Process(target=worker, args=(jobs, results))
        processes.append(process)
        process.start()

    plot_create()
    for _ in values:
        (d, C) = results.get()
        plot_update(d, C)
    plot_final()


# Fence against module import. Needed so that subprocesses don't run boss().
if __name__ == '__main__':
    boss()
