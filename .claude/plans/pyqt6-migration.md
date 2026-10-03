# Plan: Port fibermodes GUI from PyQt4 to PyQt6 (through qtpy) and modernize the project

## Context

`fibermodesgui` imports `PyQt4` in 24 modules (about 4,900 lines). PyQt4 has no
wheels for current Python. Thus the four GUI applications (`modesolver`,
`fibereditor`, `materialcalculator`, `wavelengthcalculator`) cannot start.

The project tooling is also out of date:

- `setup.py` calls `ez_setup` and lists Python 3.4/3.5.
- The tests use `nose`, which does not run on Python 3.13.
- No test module can be collected. Many test files assign a module variable
  named `__dir__`, which breaks `dir(module)` in pytest and unittest.
- `.travis.yml` is the only CI configuration.

Decisions from the user:

- Scope: full modernization (GUI port, packaging, tests, CI, core warnings).
- Binding: import through `qtpy`, with PyQt6 as the installed binding.

Outcome: all four applications start on PyQt6 and Python 3.10+. `pytest` runs
the core tests and new GUI smoke tests. `pip install .[gui]` installs all
that is necessary.

## Branches and work packages

Repository: `gotjen/fibermodes` (fork of `cbrunet/fibermodes`).
Base branch: `refactor/modernization`. It contains this plan.

Rules for each agent:

- Make the sub-branch from the latest `origin/refactor/modernization`.
- Do only the work of one work package. Do not change files of other packages.
- Open the pull request in the fork, not in upstream:
  `gh pr create --repo gotjen/fibermodes --base refactor/modernization`.
- Use conventional commit messages (`feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `ci`).
- Run `QT_QPA_PLATFORM=offscreen pytest` before each push. Put the result in the pull request.
- Do not change solver mathematics. If a failure looks numerical, stop and report it.

| Wave | Sub-branch | Work | Plan section | Needs |
|---|---|---|---|---|
| 1 | `refactor/test-baseline` | Make the tests load in pytest, repair core warnings, find the cause of the 2 failures | Phase 0 | none |
| 1 | `refactor/pyproject` | `pyproject.toml`, remove old tooling, GitHub Actions, README | Phase 1 | none |
| 2 | `refactor/qtpy-foundation` | `fibermodesgui/__init__.py`, `util.py`, `widgets/`, `wavelengthcalculator.py`, `materialcalculator.py`, plus their tests | 3.1 to 3.4, Phase 2 | wave 1 merged |
| 3 | `refactor/qtpy-fibereditor` | `fibereditor/`, `fibereditorapp.py`, plus tests | 3.2 to 3.5, Phase 2 | wave 2 merged |
| 3 | `refactor/qtpy-fieldvisualizer` | `fieldvisualizer/`, plus tests | 3.2 to 3.5, Phase 2 | wave 2 merged |
| 4 | `refactor/qtpy-modesolver` | `modesolver/`, `modesolverapp.py`, plus tests | 3.2 to 3.5, Phase 2 | wave 3 merged |
| 5 | `refactor/cleanup-docs` | Remaining PyQt4 references, `doc/`, review, final checks | Phase 4, Verification | wave 4 merged |

Sub-branches in the same wave can be done at the same time by different agents.
The two wave 1 branches touch different files, but `refactor/pyproject`
cannot show a green CI run until `refactor/test-baseline` is merged.
Merge `refactor/test-baseline` first, then rebase `refactor/pyproject`.

Each `qtpy-*` branch writes its GUI tests first (they fail), then does the
port of its modules (they pass). Thus the base branch always has passing tests.

After wave 5, open one pull request from `refactor/modernization` to `master`
in the fork.

### Start prompt for a cloud agent

    Read .claude/plans/pyqt6-migration.md on branch refactor/modernization of
    gotjen/fibermodes. Do the work package for sub-branch <NAME> and obey the
    rules in "Branches and work packages". Open a pull request to
    refactor/modernization in gotjen/fibermodes when the tests pass.

## Findings that control the design

- The code already uses new-style signals. There is no `SIGNAL()`, `QString`
  or `QVariant` use. No `.ui` or `.qrc` files exist. The port is mechanical.
- All GUI modules use only `QtGui` and `QtCore`. In Qt6, the widget classes
  are in `QtWidgets`. `QAction`, `QActionGroup` and `QShortcut` stay in `QtGui`.
  `QSortFilterProxyModel` is in `QtCore`.
- pyqtgraph is used lightly: `PlotWidget`, `ColorButton`, `ImageItem`,
  `ArrowItem`, `ScatterPlotItem`, `mkPen`, `mkBrush`, `GradientWidget`, and
  `GradientEditorItem.Gradients`.
- The local environment has Python 3.13.2, numpy 2.2, scipy 1.15, pytest 9,
  PyQt5. PyQt6, qtpy, pyqtgraph and pytest-qt are not installed.

## Phase 0: Baseline and tooling (before GUI work)

Baseline measured on 2026-10-02 (Python 3.13.2, numpy 2.2.4, scipy 1.15.2),
with `__dir__` renamed in a temporary copy of the tests:
113 passed, 2 failed, 1 xfailed, in about 5 minutes. The failures are:

- `tests/fiber/material/test_sio2geo2.py::TestSiO2GeO2::testConcentrationZero`
  (`AssertionError`).
- `tests/fiber/solver/test_tlsif.py::TestTLSIF::testCase1LP`
  (`brentq` gets NaN at x=1.4474; `ValueError`).

1. Do the work on the sub-branch `refactor/test-baseline`.
2. Rename the module variable `__dir__` to `_HERE` in each test file that
   uses it (`tests/fiber/test_factory.py`, `tests/fiber/test_fiber.py`,
   `tests/simulator/test_simulator.py`, `tests/test_field.py`, and others
   that `grep -rl __dir__ tests` finds).
3. Rename `tests/fiber/solver/cuda.py` and `tests/simulator/psimulator.py`
   only if they must run. If not, keep them out of collection.
4. Run `pytest tests` and compare with the baseline above. Find the cause of
   the two failures. Repair them if the cause is a Python, numpy or scipy
   change. Do not change solver mathematics without approval from the user.
5. Repair the `SyntaxWarning` items: use raw docstrings in
   `fibermodes/wavelength.py:72` and `fibermodes/field.py:398`.

## Phase 1: Packaging

1. Add `pyproject.toml` (setuptools backend, PEP 621 metadata):
   - `requires-python = ">=3.10"`.
   - `dependencies`: `numpy`, `scipy`.
   - `optional-dependencies.gui`: `qtpy>=2.4`, `PyQt6>=6.5`, `pyqtgraph>=0.13.7`.
   - `optional-dependencies.test`: `pytest`, `pytest-cov`, `pytest-qt`.
   - `project.gui-scripts`: the four entry points now in `setup.py`.
   - `tool.setuptools.package-data` for `fibermodesgui/icons/**`.
   - `tool.pytest.ini_options` (`testpaths = ["tests"]`, `qt_api = "pyqt6"`).
   - `tool.coverage` content from `.coveragerc`.
2. Delete `setup.py`, `ez_setup.py`, `setup.cfg`, `.coveragerc`, `.travis.yml`.
   Keep `MANIFEST.in` only if the sdist needs it.
3. Add `.github/workflows/tests.yml`: Python 3.10 to 3.13,
   `pip install .[gui,test]`, `QT_QPA_PLATFORM=offscreen`, `pytest --cov`.
4. Update `README.md` (requirements, install commands, test command) and
   `modesolver.bat`.

## Phase 2: GUI smoke tests first (RED)

Add `tests/gui/` with pytest-qt. Each test makes a window and uses `qtbot`.

- `test_apps_start.py`: construct `ModeSolver`, `FiberEditor`,
  `MaterialCalculator`, `WavelengthCalculator`, and the field visualizer.
- `test_appwindow.py`: `initActions`, `getIcon` fallback, `_closeDocument`
  with a patched `QMessageBox.exec`.
- `test_modetable.py`: `ModeTableModel` roles, check state, sort proxy.
- `test_plotframe.py`: `updatePlot` with each line style and each marker,
  legend on and off, `save()`/`load()` round trip.
- `test_solverdocument.py`: load `tests/fiber/smf28.fiber`, set a wavelength,
  wait for `computeFinished` with `qtbot.waitSignal`.
- `test_slrc.py`, `test_colormap.py`: widget construction and value signals.

Each `qtpy-*` sub-branch adds the tests for its own modules, and adds them
before it does the port. The tests fail at import until that port is complete.

## Phase 3: The port

### 3.1 Binding setup

In `fibermodesgui/__init__.py`, before all other imports:

    os.environ.setdefault("QT_API", "pyqt6")

Import `qtpy` there, so that pyqtgraph selects the same binding.

### 3.2 Import pattern (all 24 modules)

    from PyQt4 import QtGui, QtCore
    ->
    from qtpy import QtCore, QtGui, QtWidgets

Then change the namespace of each class:

- `QtGui.Q<widget>` -> `QtWidgets.Q<widget>` (QLabel, QDialog, QFileDialog,
  QMessageBox, QApplication, QMainWindow, layouts, item views, QWhatsThis,
  QStyledItemDelegate, and so on).
- Stay in `QtGui`: `QIcon`, `QFont`, `QKeySequence`, `QDoubleValidator`,
  `QAction`, `QActionGroup`.
- `QtGui.QSortFilterProxyModel` -> `QtCore.QSortFilterProxyModel`
  (`modesolver/mainwindow.py:387`).

Do this with one scripted replacement for each class name, then examine the diff.

### 3.3 Scoped enums

Write the full Qt6 names. Do not rely on the qtpy enum promotion.

| Old | New |
|---|---|
| `Qt.DisplayRole`, `UserRole`, `ToolTipRole`, `CheckStateRole` | `Qt.ItemDataRole.*` |
| `Qt.AlignRight`, `AlignCenter` | `Qt.AlignmentFlag.*` |
| `Qt.ItemIsEnabled` and related | `Qt.ItemFlag.*` |
| `Qt.Horizontal`, `Vertical` | `Qt.Orientation.*` |
| `Qt.SolidLine`, `DotLine`, `DashLine`, ... | `Qt.PenStyle.*` |
| `Qt.Checked`, `Unchecked` | `Qt.CheckState.*` |
| `Qt.AscendingOrder` | `Qt.SortOrder.AscendingOrder` |
| `Qt.Widget`, `RichText`, `RightDockWidgetArea` | `Qt.WindowType`, `Qt.TextFormat`, `Qt.DockWidgetArea` |
| `QMessageBox.Save/Yes/...` | `QMessageBox.StandardButton.*` |
| `QDialogButtonBox.Ok/...`, `ActionRole` | `.StandardButton.*`, `.ButtonRole.*` |
| `QFileDialog.AcceptOpen/AcceptSave` | `QFileDialog.AcceptMode.*` |
| `QFileDialog.Accepted`, `QDialog.Accepted` | `QDialog.DialogCode.Accepted` |
| `QKeySequence.New/Open/...` | `QKeySequence.StandardKey.*` |
| `QFrame.Panel`, `Sunken` | `QFrame.Shape.Panel`, `QFrame.Shadow.Sunken` |
| `QToolButton.InstantPopup` | `QToolButton.ToolButtonPopupMode.*` |
| `QFont.TypeWriter` | `QFont.StyleHint.TypeWriter` |
| `QAbstractItemView.AllEditTriggers` | `QAbstractItemView.EditTrigger.*` |

### 3.4 Changes that are not mechanical

- **`exec_()`**: change to `exec()` (22 call sites). Rename the override in
  `fibereditor/fiberproperties.py:40` to `exec`.
- **`QTextCodec.setCodecForTr`**: delete the line in the four `main()`
  functions. Qt6 has no `QTextCodec`.
- **`QTime` as a stopwatch** (`modesolver/mainwindow.py:290, 607, 618, 634`):
  replace with `QtCore.QElapsedTimer`. `QTime.start()`/`elapsed()` do not exist in Qt6.
- **Pen style stored as an integer** (`modesolver/plotframe.py:137, 222, 390`):
  `hash(Qt.SolidLine)` and `Qt.PenStyle(int)` depend on PyQt4 integer enums.
  Store `PenStyle.value` in the model and in the saved JSON. Convert with
  `Qt.PenStyle(value)` at read time. Old `.solver` files then stay compatible.
- **`UserRole + 1`** (`plotframe.py:24`): use `Qt.ItemDataRole.UserRole + 1`
  and make sure `index.data(YAXISLIST)` accepts the integer.
- **Check state** (`modetable.py` `setData`, `mainwindow.py:717`):
  `Qt.CheckState` is not an integer in PyQt6. Store a `bool` in
  `doc.selection`, and compare with `Qt.CheckState(value) == Checked`.
- **`rowCount(self, parent=QtCore.QModelIndex)`** (`modetable.py`): the
  default is the class, not an instance. Change to `QtCore.QModelIndex()`.
- **`stateChanged`** on `QCheckBox` (`plotframe.py:49-60`): change to
  `toggled`. Qt 6.7 deprecates `stateChanged`.
- **`QFrame.setFrameStyle(Panel | Sunken)`**: the two enum types do not
  combine in PyQt6. Use `setFrameShape` and `setFrameShadow`.
- **`QDoubleValidator(bottom=, top=)`** (`chareq.py:88`, `simparams.py:20`):
  use positional arguments plus `decimals`.
- **`QFileDialog.getOpenFileName`** (`fibereditor/fiberplot.py:162`): already
  unpacks a tuple. Confirm only.
- **`getIcon`** (`widgets/appwindow.py:98`): the fallback loop has an
  indentation defect, so only the last path is tested. Repair it during the
  port, because Qt6 icon theme lookup changes make the fallback more important.
- **`SolverDocument(QThread)`**: no API change. Verify that `PSimulator`
  (multiprocessing `Pool`) operates from the Qt thread with the test in Phase 2.

### 3.5 pyqtgraph 0.13+

- `from pyqtgraph.graphicsItems import GradientEditorItem` gives the module.
  Change to `from pyqtgraph.graphicsItems.GradientEditorItem import Gradients`
  and add the color maps to that dictionary (`fieldvisualizer/colormapwidget.py`).
  pyqtgraph now includes viridis, inferno, plasma and magma. Add only `parula`
  and those that are absent.
- `mkPen(style=...)` accepts `Qt.PenStyle` members. Pass the enum, not an integer.
- Verify `addLegend`/legend removal, `ArrowItem`, `ImageItem.setLookupTable`
  and `scene().sigMouseClicked` with the Phase 2 tests.

### 3.6 Sequence of work

1. `fibermodesgui/__init__.py`, `util.py`, `widgets/` (appwindow, delegate, slrc).
2. `wavelengthcalculator.py`, `materialcalculator.py` (small, stand-alone).
3. `fibereditor/` and `fibereditorapp.py`.
4. `fieldvisualizer/`.
5. `modesolver/` and `modesolverapp.py` (largest: `mainwindow.py`, `plotframe.py`).

Steps 1 and 2 are `refactor/qtpy-foundation`. Steps 3, 4 and 5 each have
their own sub-branch. Run the related smoke tests after each step.

## Phase 4: Clean-up

- `grep -rn "PyQt4\|exec_(\|QTextCodec" .` must return no results.
- Run the `python-reviewer` agent on the diff.
- Update `doc/` and `README.md` where they name PyQt4.
- `scripts/` and `plots/` are not packaged. Change them only if they import PyQt4.

## Verification

1. `pip install -e ".[gui,test]"` in a clean virtual environment.
2. `QT_QPA_PLATFORM=offscreen pytest --cov=fibermodes --cov=fibermodesgui`:
   all tests pass, with no `DeprecationWarning` from Qt.
3. Start each application manually: `modesolver`, `fibereditor`,
   `materialcalculator`, `wavelengthcalculator`.
4. Manual scenario in `modesolver`:
   - Open `tests/fiber/smf28.fiber`.
   - Set a wavelength range and select `neff` and `cutoff (V)`.
   - Make sure the table fills, the progress timer counts, and the plot shows.
   - Change line style and marker, set the legend on and off.
   - Open the field visualizer (F4) and change the color map.
   - Save a `.solver` file, open it again, and compare the settings.
5. Manual scenario in `fibereditor`: make a new fiber, add a layer, save,
   and open the file again.

## Risks

- Two core tests fail in the baseline. Their cause is not yet known, and
  it can be numerical.
- qtpy hides some binding differences, but pyqtgraph selects its binding
  independently. The `QT_API` default in 3.1 keeps the two aligned.
- Python 3.14 changes the default multiprocessing start method on Linux.
  `PSimulator` can then need picklable callables. Keep 3.14 out of the CI
  matrix until this is tested.
