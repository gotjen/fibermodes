"""Shared configuration for the GUI smoke tests (pytest-qt)."""

import os

# Use the offscreen platform when no display is available. pytest-qt makes
# the QApplication lazily, so this setting is in place before Qt starts.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


import shutil  # noqa: E402

import pytest  # noqa: E402

FIBER_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), os.pardir, "fiber"))
SMF28 = os.path.join(FIBER_DIR, "smf28.fiber")


@pytest.fixture
def smf28_file(tmp_path):
    """A copy of smf28.fiber, so that tests can write a .solver beside it."""
    path = tmp_path / "smf28.fiber"
    shutil.copy(SMF28, path)
    return str(path)


@pytest.fixture
def modesolver(qtbot):
    """An empty ModeSolver window. Its document thread is stopped at
    teardown, and the window is closed without a save prompt."""
    from fibermodesgui.modesolver.mainwindow import ModeSolver

    win = ModeSolver()

    def before_close(w):
        w.setDirty(False)
        w.doc.stop_thread()

    qtbot.addWidget(win, before_close_func=before_close)
    return win


def load_fiber(win, filename):
    """Load a fiber file in a ModeSolver, as FiberSelector.chooseFiber
    does after the file dialog."""
    win.doc.filename = filename
    win.fiberSelector.fileLoaded.emit()


def compute(qtbot, win, params=("neff",), wavelengths=None,
            timeout=120000):
    """Select params and wavelengths, run the simulation, and wait for
    computeFinished."""
    if wavelengths is not None:
        win.wavelengthInput.setValue(wavelengths)
    for p, box in win.simParamBoxes.items():
        box.setChecked(p in params)
    with qtbot.waitSignal(win.doc.computeFinished, timeout=timeout):
        win.run_simulation()
    win.doc.wait()
