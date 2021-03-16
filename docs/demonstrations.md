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
