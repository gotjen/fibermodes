# fibermodes
Multilayers fiber mode solver

[![tests](https://github.com/gotjen/fibermodes/actions/workflows/tests.yml/badge.svg)](https://github.com/gotjen/fibermodes/actions/workflows/tests.yml)

API documentation available on http://fibermodes.rtfd.org/


Installation
============

Requirements:

- Python >= 3.10
- numpy
- scipy

For GUI (extra `gui`):

 - PyQt6 >= 6.5
 - qtpy >= 2.4
 - pyqtgraph >= 0.13.7

To run unit tests (extra `test`):

 - pytest
 - pytest-cov (for coverage tests)
 - pytest-qt (for GUI tests)

All dependencies are declared in `pyproject.toml` and are installed by `pip`.


This software is still under heavy development. Therefore, it is recommended to
install it in a development environment, to be able to quickly pull newest changes
from the GitHub repository, and to be able to propose pull requests. However,
we also describe a *simple* installation, in case you only want to run  the 
software, without hacking it.


Installing the required environment
-----------------------------------

### For Linux

Install Python 3.10 or higher and `pip` from your distribution
(for instance `python3`, `python3-pip` and `python3-venv` on **Ubuntu** / **Debian**,
or `python` and `python-pip` on **Arch**). The Python dependencies are then
installed with `pip` (see below). It is recommended to work in a virtual environment:

```
python3 -m venv .venv
source .venv/bin/activate
```

On a machine without a display (e.g. a CI server), PyQt6 needs a few system
libraries, such as `libegl1`, `libgl1`, `libxkbcommon0`, `libfontconfig1` and
`libdbus-1-3`. Set `QT_QPA_PLATFORM=offscreen` to run the GUI tests.


### For Windows

I recommend to use a distribution that includes scientific Python.
Choose a distribution that includes Python 3.10 or higher. I recommend
using either
[WinPython](http://winpython.github.io/) or
[Anaconda](https://www.continuum.io/downloads).
Follow the installation instructions, and everything should work out-of-the-box.


### For Mac OS

I do not have a machine to test installation on Mac OS. However, it *should* work.
Please fell free to share me your experience.


*Simple* installation
---------------------

This is not the recommended way. You should consider *development* installation
instead. However, this is the simplest installation, as it does not require `git`.

1. Download the [ZIP archive from GitHub](https://github.com/cbrunet/fibermodes).
2. Unzip it!
3. On a command line, go inside the `fibermodes` directory.
4. Run `pip install .[gui]` (or `pip install .` if you do not need the GUI).

The command on line 4 may vary.
For instance, it should be `python3 -m pip install .[gui]` on Ubuntu / Debian,
preferably inside a virtual environment.

This installs four GUI applications: `modesolver`, `fibereditor`,
`materialcalculator` and `wavelengthcalculator`.
On Windows, you can also start the mode solver from the source directory
with `modesolver.bat`.


Development installation
------------------------

The first step is to install `git`. For Linux, the package should be called `git`.
For Windows, it is a little more complicated. I recommend using
[Git for Windows](https://git-for-windows.github.io/). Follow the installation
instructions from their page.
You could also install [GitHub Desktop](https://desktop.github.com/) instead.

The second step is to create a GitHub account, if you do not already have one.
Then you should configure you machine with ssh keys, and configure your name
and email for git.

The third step is to fork and clone the
[fibermodes repository](https://github.com/cbrunet/fibermodes).
I recommend forking it first, as it will allow you to commit your changes
on GitHub, and to suggest pull requests.

Then you should install the software in *editable* mode. This is similar
to a normal installation, but it uses links instead of copying the files. Therefore, you
do not need to reinstall each time you pull changes from GitHub.
The command, from the `fibermodes` directory, is:

```
pip install -e .[gui,test]
```


Running tests
-------------

To ensure you have all the required dependencies to run tests, you can
do, from the `fibermodes` directory: `pip install -e .[gui,test]`.

Then run `pytest`. To get a coverage report, run `pytest --cov`.
On a machine without a display, run `QT_QPA_PLATFORM=offscreen pytest`.


Building documentation
----------------------

You need sphinx (and probably a few dependencies to be documented).

```
sphinx-build doc doc/_build/html
```

Documentation is generated under `doc/_build/html`.


