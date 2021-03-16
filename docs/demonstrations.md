Demonstrations
--------------

### Busbar

["Electrical Heating in a Busbar"][busbar] is an example model used in the tutorial in [Introduction to Comsol Multiphysics][intro] and explained there in great detail. The section "Getting the Maximum and Minimum Temperature" demonstrates how two obtain the two temperature extremes within the Comsol GUI.

The following Python code does the same thing programmatically:
```python
import mph

client = mph.start()
model = client.load('busbar.mph')
model.solve()

(x, y, z, T) = model.evaluate(['x', 'y', 'z', 'T'])
(Tmax, Tmin) = (T.max(), T.min())
(imax, imin) = (T.argmax(), T.argmin())
print(f'Tmax = {T.max():.2f} K at ({x[imax]:5f}, {y[imax]:5f}, {z[imax]:5f})')
print(f'Tmin = {T.min():.2f} K at ({x[imin]:5f}, {y[imin]:5f}, {z[imin]:5f})')
```

This outputs the exact same numbers that appear in the table of the GUI:
```none
Tmax = 330.42 K at (0.105000, -0.024899, 0.053425)
Tmin = 322.41 K at (0.063272, 0.000000, 0.000000)
```

You could now sweep the model's parameters, for example the length (`L`) or width (`wbb`) of the busbar.


[busbar]: https://www.comsol.com/model/electrical-heating-in-a-busbar-10206
[intro]: https://www.comsol.com/documentation/IntroductionToCOMSOLMultiphysics.pdf


### Compacting models

We usually save models to disk after we have solved them, which includes the solution and mesh data in the file. This is convenient so that we can come back to the model later, but don't have to run the simulation again, which may take a long time. However, the files then require a lot of disk space. After a while, we may want to archive the models, but trim the fat before we do that.

To compact all model files in the current folder, we can do this:
```python
import mph
from pathlib import Path

client = mph.start()
for file in Path.cwd().glob('*.mph'):
    print(f'{file}:')
    model = client.load(file)
    model.clear()
    model.save()
```

The script `compact_models.py` in the [`demos` folder][demos] of the source-code repository is a more refined version of the above code. It displays more status information and also resets the modeling history.

Note that we could easily go through all sub-directories recursively by replacing `glob` with `rglob`. However, this should be used with care so as to not accidentally modify models in folders that were not meant to be included.


[demos]: https://github.com/John-Hennig/MPh/tree/master/demos
