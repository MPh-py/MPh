"""Discovers all top-level groups defined in a model."""

import mph
import inspect


client = mph.start()
model = client.load('../tests/capacitor.mph')

groups = []
members = inspect.getmembers(model.java, predicate=inspect.isfunction)
exclude = ('notify', 'notifyAll', 'resetHist', 'save', 'wait')
for (name, object) in members:
    if object.__name__ in exclude:
        continue
    try:
        children = inspect.getmembers(object(), predicate=inspect.isfunction)
    except Exception:
        continue
    names = [child[0] for child in children]
    if 'tags' in names:
        groups.append( (name, object) )

groups = sorted(groups, key=lambda items: items[0])
for (name, object) in groups:
    print(f'{name!r:20} model.java.{object.__name__}')
