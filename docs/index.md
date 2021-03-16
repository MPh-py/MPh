MPh
===
Pythonic scripting interface for Comsol Multiphysics

[Comsol][comsol] is a commercial software application that is widely
used in science and industry for research and development. It excels
at modeling almost any (multi-)physics problem by solving the governing
set of partial differential equations via the finite-element method.
It comes with a modern graphical user interface to set up simulation
models and can be scripted from Matlab or via its native Java API.

This library brings the dearly missing power of Python to the world
of Comsol. It leverages the universal Python-to-Java bridge provided
by [JPype][jpype] to access the native API, and wraps it in a layer
of pythonic ease-of-use. The Python wrapper only covers common
scripting tasks, such as loading a model from a file, modifying some
parameters, running the simulation, to then evaluate the results.
Though the full functionality is available to those willing to drop
down to the pythonized Java layer underneath.

Comsol models are marked by their `.mph` file extension, which stands
for multi-physics. Hence the name of this library. It is open-source
and in no way affiliated with Comsol Inc., the company that develops
and sells the simulation software.


[comsol]: https://www.comsol.com
[jpype]:  https://pypi.org/project/JPype1


```eval_rst
.. toctree::
    :hidden:

    installation
    tutorial
    limitations
    demonstrations
    api
```
