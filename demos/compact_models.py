"""
Compacts Comsol models in the working directory.

Loads each Comsol model (`.mph` file) in the current folder, removes
solution and mesh data, resets the modeling history, then saves the
model file under its original name, effectively compacting its size.
"""
__license__ = 'MIT'


########################################
# Dependencies                         #
########################################
import mph
from pathlib import Path
from time import perf_counter as now


########################################
# Timer                                #
########################################
class Timer():
    """Convenience class for measuring and displaying elapsed time."""

    def __init__(self, margin=4, padding=12):
        self.t0 = None
        self.margin = margin
        self.padding = padding

    def start(self, step):
        """Starts timing a step, displaying its name."""
        print(' '*self.margin + f'{step:{self.padding}}', end='', flush=True)
        self.t0 = now()

    def cancel(self, reason=''):
        """Cancels timing the step, displaying the reason."""
        print(reason, flush=True)

    def stop(self):
        """Stops timing the step, displaying the elapsed time."""
        elapsed = now() - self.t0
        print(f'{elapsed:.1f} seconds', flush=True)


########################################
# Main                                 #
########################################

# Display welcome message.
print('Compacting Comsol models in the current folder.')

# Start Comsol client.
print('Running Comsol client on single processor core.')
client = mph.start(cores=1)

# Loop over model files.
timer = Timer()
for file in Path.cwd().glob('*.mph'):

    name = file.relative_to(Path.cwd())
    print(f'{name}:')

    timer.start('Loading')
    try:
        model = client.load(file)
        timer.stop()
    except Exception:
        timer.cancel('Failed.')
        continue

    timer.start('Clearing')
    model.clear()
    timer.stop()

    timer.start('Resetting')
    try:
        model.reset()
        timer.stop()
    except Exception:
        timer.cancel('Failed.')

    timer.start('Saving')
    model.save()
    timer.stop()
