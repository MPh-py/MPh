"""
Compacts Comsol models in the current folder.

Removes solution and mesh data and resets the modeling history.
Then saves the model file under its original name, effectively
compacting its size.

Processes all models it finds in the current folder. Optionally,
includes subfolders as well, if the user enters "all" after the
script starts.
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
print('Compact Comsol models in the current folder.')

# Have user type "all" to indicate subfolders should be included.
print('Press Enter to start. Type "all" to include subfolders.')
if input() == 'all':
    files = Path.cwd().rglob('*.mph')
else:
    files = Path.cwd().glob('*.mph')

# Start Comsol client.
print('Running Comsol client on single processor core.')
client = mph.Client(cores=1)

# Loop over model files.
timer = Timer()
for file in files:

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

# Have user press Enter before the console window might close itself.
input('Press Enter to quit.')
