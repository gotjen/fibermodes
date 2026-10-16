"""Each application window can be constructed and shown."""

import sys

import pytest
from qtpy import QtWidgets

from fibermodesgui import materialcalculator, wavelengthcalculator


@pytest.mark.parametrize("cls", [
    wavelengthcalculator.WavelengthCalculator,
    materialcalculator.MaterialCalculator,
])
def test_dialog_starts(qtbot, cls):
    win = cls()
    qtbot.addWidget(win)
    win.show()
    qtbot.waitExposed(win)
    assert win.isVisible()
    with qtbot.waitSignal(win.hidden):
        win.hide()


@pytest.mark.parametrize("module", [wavelengthcalculator, materialcalculator])
def test_main(qapp, qtbot, monkeypatch, module):
    """main() starts the event loop and exits with its return code."""
    windows = []

    class FakeApplication:
        def __init__(self, argv):
            pass

        def setApplicationName(self, name):
            self.name = name

        def exec(self):
            windows.extend(w for w in qapp.topLevelWidgets()
                           if w.isVisible())
            return 0

    monkeypatch.setattr(QtWidgets, "QApplication", FakeApplication)
    monkeypatch.setattr(sys, "argv", ["prog"])
    with pytest.raises(SystemExit) as excinfo:
        module.main()
    assert excinfo.value.code == 0
    assert windows
    for w in windows:
        qtbot.addWidget(w)
