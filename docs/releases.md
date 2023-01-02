# Releases

## 1.2.1
* [Published](https://pypi.org/project/MPh/1.2.1) on January 2, 2023.
* Increased default time-out of server shutdown to accommodate Comsol 6.1.
  ([#106](https://github.com/MPh-py/MPh/issues/106))
* Fixed tests that would otherwise fail with Comsol 6.1.
* Added ["Credits"](https://mph.readthedocs.io/en/1.2/credits.html) page
  to documentation.

## 1.2.0
* [Published](https://pypi.org/project/MPh/1.2.0) on August 31, 2022.
* Includes Comsol installation found on `PATH` in discovery.
  ([#89](https://github.com/MPh-py/MPh/issues/89))
  <br>
  So if the `comsol` command works in the console, the corresponding
  installation will now be found automatically, even if not in a default
  location.
* Adds support for material property groups, which now show up in model tree.
  ([#78](https://github.com/MPh-py/MPh/issues/78))
  <br>
  Material properties can be read and altered by calling
  [`property()`](https://mph.readthedocs.io/en/1.2/api/mph.Node.html#mph.Node.property)
  on the node referring to its property group.
* Adds method
  [`problems()`](https://mph.readthedocs.io/en/1.2/api/mph.Model.html#mph.Model.problems)
  to the `Model` class.
  <br>
  It does the same as calling
  [`Node.problems()`](https://mph.readthedocs.io/en/1.2/api/mph.Node.html#mph.Node.problems)
  on the model's root node, but provides for an easy way to check if
  there are currently errors or warnings reported anywhere in the model.
* Adds "Uncertainty Quantification" to list of recognized
  [`modules`](https://mph.readthedocs.io/en/1.2/api/mph.Client.html#mph.Client.modules).
* External links to Comsol documentation now refer to Comsol 6.0.

## 1.1.6
* [Published](https://pypi.org/project/MPh/1.1.6) on June 30, 2022.
* Adds missing support for export of meshes. ([#73](https://github.com/MPh-py/MPh/issues/73))
* No longer checks process environment in stand-alone mode. ([#13](https://github.com/MPh-py/MPh/issues/13))

## 1.1.5
* [Published](https://pypi.org/project/MPh/1.1.5) on February 28, 2022.
* Fixes: Server does not start when language set to Chinese. ([#72](https://github.com/MPh-py/MPh/issues/72))

## 1.1.4
* [Published](https://pypi.org/project/MPh/1.1.4) on February 23, 2022.
* Fixes discovery of Comsol 6.0 on Linux. ([#67](https://github.com/MPh-py/MPh/issues/67))

## 1.1.3
* [Published](https://pypi.org/project/MPh/1.1.3) on February 21, 2022.
* Adds support for export of animations. ([#43](https://github.com/MPh-py/MPh/issues/43))
* Catches spurious exceptions when reading properties in [`mph.inspect()`](https://mph.readthedocs.io/en/1.1/api/mph.inspect.html). ([#68](https://github.com/MPh-py/MPh/issues/68))

## 1.1.2
* [Published](https://pypi.org/project/MPh/1.1.2) on January 8, 2022.
* Fixes evaluation error for datasets with slash in name. ([#66](https://github.com/MPh-py/MPh/issues/66))

## 1.1.1
* [Published](https://pypi.org/project/MPh/1.1.1) on December 2, 2021.
* Supports custom Comsol install locations on Linux via symbolic links in `~/.local`. ([#62](https://github.com/MPh-py/MPh/issues/62))

## 1.1.0
* [Published](https://pypi.org/project/MPh/1.1.0) on October 21, 2021.
* Client instances may now re-[`connect()`](https://mph.readthedocs.io/en/1.1/api/mph.Client.html#mph.Client.connect) to a different server. ([#41](https://github.com/MPh-py/MPh/pull/41))
* [`Server`](https://mph.readthedocs.io/en/1.1/api/mph.Server.html) instances can be started with the `multi` option.
* Module licenses can be queried with [`Client.modules()`](https://mph.readthedocs.io/en/1.1/api/mph.Client.html#mph.Client.modules) and [`Model.modules()`](https://mph.readthedocs.io/en/1.1/api/mph.Model.html#mph.Model.modules).
* Node selections can be set and queried with [`.select()`](https://mph.readthedocs.io/en/1.1/api/mph.Node.html#mph.Node.select) and [`.selection()`](https://mph.readthedocs.io/en/1.1/api/mph.Node.html#mph.Node.selection).
* Warnings and errors are reported by [`Node.problems()`](https://mph.readthedocs.io/en/1.1/api/mph.Node.html#mph.Node.problems).
* User comments on model nodes can be accessed with [`Node.comment()`](https://mph.readthedocs.io/en/1.1/api/mph.Node.html#mph.Node.comment).
* The [`import_()`](https://mph.readthedocs.io/en/1.1/api/mph.Node.html#mph.Node.import_) method is now also available on nodes.
* No longer logs warning when [`mph.start()`](https://mph.readthedocs.io/en/1.1/api/mph.start.html) returns existing client instance.
* Fixes: Java DLL not found if another program is first on the Windows search path. ([#49](https://github.com/MPh-py/MPh/issues/49))
* Fixes: Certain preferences not defined on older Comsol installations. ([#50](https://github.com/MPh-py/MPh/issues/50))
* Added documentation note regarding issue with export of animations. ([#43](https://github.com/MPh-py/MPh/issues/43))
* Improved API documentation. Cross-referenced [Comsol API docs](https://doc.comsol.com/5.6/doc/com.comsol.help.comsol/api).
* Added new logo. (Not subject to the source code's MIT license.)

## 1.0.4
* [Published](https://pypi.org/project/MPh/1.0.4) on May 23, 2021.
* Adds missing support for installations with classkit license. ([#40](https://github.com/MPh-py/MPh/pull/40))
* Adds name validation of available configuration options. ([#40](https://github.com/MPh-py/MPh/pull/40))
* Adds support for persistent configuration storage to [`mph.config`](https://mph.readthedocs.io/en/1.0/api/mph.config.html).
* Fixes: No preference `checkforrecoveries` on certain installations. ([#39](https://github.com/MPh-py/MPh/issues/39))
* Fixes: Unclear error message when requested version is not installed. ([#42](https://github.com/MPh-py/MPh/issues/42))

## 1.0.3
* [Published](https://pypi.org/project/MPh/1.0.3) on May 5, 2021.
* Fixes: [`Client.remove()`](https://mph.readthedocs.io/en/1.0/api/mph.Client.html#mph.Client.remove) did not accept model by name.
* Fixes: Node names were not escaped when creating new features.
* Fixes: [`Model.save()`](https://mph.readthedocs.io/en/1.0/api/mph.Model.html#mph.Model.save) failed when `format` given, but not `path`.
* Fixes: [`Model.save()`](https://mph.readthedocs.io/en/1.0/api/mph.Model.html#mph.Model.save) without `path` given did not save new models.
* Fixes: [`Model.parameters(evaluate=True)`](https://mph.readthedocs.io/en/1.0/api/mph.Model.html#mph.Model.parameters) returned strings, not numbers.
* Fixes off-by-one error when passing `inner` indices to [`Model.evaluate()`](https://mph.readthedocs.io/en/1.0/api/mph.Model.html#mph.Model.evaluate).
* Comsol expects 1-based indices, as opposed to Python's 0-based indexing.
* Adds missing built-in group `'couplings'`.
* [`mph.start()`](https://mph.readthedocs.io/en/1.0/api/mph.start.html) now returns existing client instance on subsequent calls.

## 1.0.2
* [Published](https://pypi.org/project/MPh/1.0.2) on April 28, 2021.
* Assigns more typical tag names when creating new model features.
* In most cases, tags are now named like they are in the Comsol GUI.
* [`Node.retag()`](https://mph.readthedocs.io/en/1.0/api/mph.Node.html#mph.Node.retag) allows post-hoc modification of a node's tag.
* Adds missing built-in groups, e.g. evaluations and tables.
* Improves performance of node navigation in client–server mode.
* The internal type-casting converts [`Node`](https://mph.readthedocs.io/en/1.0/api/mph.Node.html) instances to their tags.
* The internal type-casting handles lists of numbers.
* Before, [`property()`](https://mph.readthedocs.io/en/1.0/api/mph.Node.html#mph.Node.property) and [`create()`](https://mph.readthedocs.io/en/1.0/api/mph.Node.html#mph.Node.create) would only accept lists of strings.
* [`Node.type()`](https://mph.readthedocs.io/en/1.0/api/mph.Node.html#mph.Node.type) now returns nothing if node has no feature type.
* Moved tutorial model to [`demos`](https://github.com/MPh-py/MPh/tree/main/demos) folder.
* Added demo script [`create_capacitor.py`](https://github.com/MPh-py/MPh/blob/main/demos/create_capacitor.py) that generates the tutorial model.

## 1.0.1
* [Published](https://pypi.org/project/MPh/1.0.1) on April 23, 2021.
* Fixes failing evaluation when name of default dataset contains slash.
* Fixes failing evaluation of complex-valued expressions.
* Fixes issue with complex numbers in parameter assignments. ([#36](https://github.com/MPh-py/MPh/issues/36))

## 1.0.0
* [Published](https://pypi.org/project/MPh/1.0.0) on April 13, 2021.
* We now offer you the best API Comsol has ever seen! 🎉
* See ["Creating models: Python style"](https://mph.readthedocs.io/en/1.0/demonstrations.html#creating-models-python-style) for a feature demonstration.
* A new [`Node`](https://mph.readthedocs.io/en/1.0/api/mph.Node.html) class allows easy navigation of the model tree.
* The [`Model`](https://mph.readthedocs.io/en/1.0/api/mph.Model.html) class relies internally on `Node` for most functionality.
* Feature nodes can be created with [`Model.create()`](https://mph.readthedocs.io/en/1.0/api/mph.Model.html#mph.Model.create).
* Node properties can be read and written via [`Model.property()`](https://mph.readthedocs.io/en/1.0/api/mph.Model.html#mph.Model.property).
* Feature nodes can be removed with [`Model.remove()`](https://mph.readthedocs.io/en/1.0/api/mph.Model.html#mph.Model.remove).
* The [`Node`](https://mph.readthedocs.io/en/1.0/api/mph.Node.html) class has additional functionality for modifying the model.
* All feature nodes can now be [toggled](https://mph.readthedocs.io/en/1.0/api/mph.Node.html#mph.Node.toggle), not just physics features.
* [`Model.features()`](https://mph.readthedocs.io/en/0.9/api/mph.Model.html#mph.Model.features) and [`Model.toggle()`](https://mph.readthedocs.io/en/0.9/api/mph.Model.html#mph.Model.toggle) have been deprecated.
* Use the [`Node`](https://mph.readthedocs.io/en/1.0/api/mph.Node.html) class instead to access that functionality.
* [`Model.import_()`](https://mph.readthedocs.io/en/1.0/api/mph.Model.html#mph.Model.import_) was introduced to supersede [`Model.load()`](https://mph.readthedocs.io/en/0.9/api/mph.Model.html#mph.Model.load).
* Arguments `unit` and `description` to [`Model.parameter()`](https://mph.readthedocs.io/en/1.0/api/mph.Model.html#mph.Model.parameter) are deprecated.
* Parameter descriptions should now be accessed via [`Model.description()`](https://mph.readthedocs.io/en/1.0/api/mph.Model.html#mph.Model.description).
* [`Model.parameters()`](https://mph.readthedocs.io/en/1.0/api/mph.Model.html#mph.Model.parameters) now returns a dictionary [instead of named tuples](https://mph.readthedocs.io/en/0.9/api/mph.Model.html#mph.Model.parameters).
* This is a breaking change, but in line with other parts of the API.
* [`mph.start()`](https://mph.readthedocs.io/en/1.0/api/mph.start.html) now picks a random free server port in client-server mode.
* This avoids collisions when starting multiple processes on Linux and macOS.
* Models may be [saved as](https://mph.readthedocs.io/en/1.0/api/mph.Model.html#mph.Model.save) Java, Matlab, or VBA source files.
* [`mph.tree()`](https://mph.readthedocs.io/en/1.0/api/mph.tree.html) helps developers inspect the model tree in the console.
* Known issue: Navigating the model tree is slow in client–server mode.
* It is much faster in stand-alone mode, the default on Windows.
* Made folder search case-insensitive on Linux/macOS, as requested in [#31](https://github.com/MPh-py/MPh/issues/31).
* Documentation builds now use the [MyST parser](https://github.com/executablebooks/MyST-Parser) and the [Furo theme](https://github.com/pradyunsg/furo).

## 0.9.1
* [Published](https://pypi.org/project/MPh/0.9.1) on March 24, 2021.
* Added documentation chapter ["Demonstrations"](https://mph.readthedocs.io/en/0.9/demonstrations.html).
* Added [demo script](https://github.com/MPh-py/MPh/blob/72624ea6d92f009af07b3c7468084ab2a62dccfb/demos/worker_pool.py) that runs parallel Comsol sessions.
* Amended [`mph.start()`](https://mph.readthedocs.io/en/0.9/api/mph.start.html#mph.start) to allow hand-selecting the server port.
* This makes the demo script work reliably on Linux and macOS.
* Improved error handling at [server](https://mph.readthedocs.io/en/0.9/api/mph.Server.html#mph.Server) start-up.
* Relaxed log levels during [discovery](https://mph.readthedocs.io/en/0.9/api/mph.discovery.html) of Comsol installations.
* This suppresses possibly confusing log messages as described in [#28](https://github.com/MPh-py/MPh/issues/28).

## 0.9.0
* [Published](https://pypi.org/project/MPh/0.9.0) on March 10, 2021.
* [`mph.start()`](https://mph.readthedocs.io/en/0.9/api/mph.start.html) is now the preferred way to start a local Comsol session.
* On Windows, it starts a lightweight, stand-alone client.
* On Linux and macOS, it starts a thin client and local server.
* This is due to limitations on these platforms described in [issue #8](https://github.com/MPh-py/MPh/issues/8).
* Configuration options are exposed by [`mph.option()`](https://mph.readthedocs.io/en/0.9/api/mph.config.html#mph.config.option).
* An in-memory [cache](https://mph.readthedocs.io/en/0.9/api/mph.Client.html#mph.Client.caching) for previously loaded model files may be activated.
* Selection names are returned by [`model.selections()`](https://mph.readthedocs.io/en/0.9/api/mph.Model.html#mph.Model.selections).
* Feature names in physics interfaces are returned by [`model.features()`](https://mph.readthedocs.io/en/0.9/api/mph.Model.html#mph.Model.features).
* Feature nodes in physics interfaces can be [toggled](https://mph.readthedocs.io/en/0.9/api/mph.Model.html#mph.Model.toggle) on or off.
* [Parameter](https://mph.readthedocs.io/en/0.9/api/mph.Model.html#mph.Model.parameter) descriptions can be modified.
* [Parameter](https://mph.readthedocs.io/en/0.9/api/mph.Model.html#mph.Model.parameter) values may be returned as evaluated numbers instead of string expressions.
* Custom classes derived from [`Model`](https://mph.readthedocs.io/en/0.9/api/mph.Model.html#mph.Model) can now be more easily type-cast to.
* Users are warned if log-in details for the Comsol [server](https://mph.readthedocs.io/en/0.9/api/mph.Server.html#mph.Server) have not been set up.
* Fixes [issue #23](https://github.com/MPh-py/MPh/issues/23) regarding discovery with older Python versions on Windows.
* Fixes [issue #24](https://github.com/MPh-py/MPh/issues/24) regarding localized server output messages.

## 0.8.2
* [Published](https://pypi.org/project/MPh/0.8.2) on February 13, 2021.
* Fixes: Exit code was always 0, even when terminating with `sys.exit(2)`. ([#15](https://github.com/MPh-py/MPh/issues/15))
* Fixes: Exit code was 0, not 1, when exiting due to unhandled exception. ([#15](https://github.com/MPh-py/MPh/issues/15))

## 0.8.1
* [Published](https://pypi.org/project/MPh/0.8.1) on February 9, 2021.
* Applies fixes for macOS from [pull request #11](https://github.com/MPh-py/MPh/pull/11).
* macOS support has now actually been tested according to [issue #13](https://github.com/MPh-py/MPh/issues/13).

## 0.8.0
* [Published](https://pypi.org/project/MPh/0.8.0) on February 7, 2020.
* Adds support for Linux and macOS.
* Caveats apply. See documentation chapter ["Limitations"](https://mph.readthedocs.io/en/0.8/limitations.html) as well as issues [#8](https://github.com/MPh-py/MPh/issues/8) and [#9](https://github.com/MPh-py/MPh/issues/9).
* Refactored [discovery](https://mph.readthedocs.io/en/0.8/api/mph.discovery.html) mechanism for Comsol installations.

## 0.7.6
* [Published](https://pypi.org/project/MPh/0.7.6) on November 29, 2020.
* Unpins [JPype](https://pypi.org/project/JPype1) and Python version.
* Works around [issue #1](https://github.com/MPh-py/MPh/issues/1) by brute-forcing shutdown of Java VM.
* [`Client`](https://mph.readthedocs.io/en/0.7/api/mph.Client.html) instances now report the Comsol version actually used.
* Updates the documentation regarding [limitations](https://mph.readthedocs.io/en/0.7/limitations.html).
* Resolves [issue #4](https://github.com/MPh-py/MPh/issues/4) regarding compatibility with 32-bit Python.
* Possibly resolves [issue #5](https://github.com/MPh-py/MPh/issues/5) regarding spaces in path names.

## 0.7.5
* [Published](https://pypi.org/project/MPh/0.7.5) on July 30, 2020.
* First release used extensively "in production".
* Last release based on [JPype 0.7.5](https://github.com/jpype-project/jpype/releases/tag/v0.7.5).
* Performs a regular shutdown of the Java VM, as opposed to releases to follow.
* Respects user-set Comsol preferences when starting [`Client`](https://mph.readthedocs.io/en/0.7/api/mph.Client.html).
* Adds screen-shot of Comsol demonstration model to [Tutorial](https://mph.readthedocs.io/en/0.7/tutorial.html).

## 0.7.4
* [Published](https://pypi.org/project/MPh/0.7.4) on July 17, 2020.
* Pins JPype dependency to [version 0.7.5](https://github.com/jpype-project/jpype/releases/tag/v0.7.5).
* Works around shutdown delays of the Java VM, see [issue #1](https://github.com/MPh-py/MPh/issues/1).
* Requires Python version to be 3.8.3 or below.
* Minor improvements to wording of documentation.

## 0.7.3
* [Published](https://pypi.org/project/MPh/0.7.3) on June 15, 2020.
* Suppresses console pop-up during [client initialization](https://mph.readthedocs.io/en/0.7/api/mph.Client.html).
* Ignores empty units in [parameter assignments](https://mph.readthedocs.io/en/0.7/api/mph.Model.html#mph.Model.parameter).

## 0.7.2
* [Published](https://pypi.org/project/MPh/0.7.2) on May 18, 2020.
* Makes `dataset` argument to [`Model.outer()`](https://mph.readthedocs.io/en/0.7/api/mph.Model.html#mph.Model.outer) optional.
* Minor tweaks to project's meta information.

## 0.7.1
* [Published](https://pypi.org/project/MPh/0.7.1) on May 17, 2020… later that day.
* Fixes meta information on PyPI.

## 0.7.0
* [Published](https://pypi.org/project/MPh/0.7.0) on May 17, 2020.
* First open-source release published on PyPI.
