"""Tests for the mode solver main window (fibermodesgui.modesolver)."""

import json
import os
import sys

import pytest
from qtpy import QtCore, QtWidgets

from fibermodes import ModeFamily
from fibermodesgui import modesolverapp
from fibermodesgui.fieldvisualizer import FieldVisualizer
from fibermodesgui.materialcalculator import MaterialCalculator
from fibermodesgui.modesolver.chareq import CharEqDialog
from fibermodesgui.modesolver.mainwindow import ModeSolver, msToStr
from fibermodesgui.modesolver.showhide import ShowHideMode
from fibermodesgui.modesolver.simparams import SimParamsDialog
from fibermodesgui.wavelengthcalculator import WavelengthCalculator

from .conftest import compute, load_fiber

Qt = QtCore.Qt
ACCEPTED = QtWidgets.QDialog.DialogCode.Accepted


@pytest.fixture
def loaded(modesolver, smf28_file):
    modesolver.doc.numProcs = 1
    load_fiber(modesolver, smf28_file)
    return modesolver


@pytest.fixture
def solved(loaded, qtbot):
    compute(qtbot, loaded, params=("cutoff (V)", "neff"),
            wavelengths=[800e-9, 1550e-9])
    loaded.wavelengthSlider.wavelengthInput.setValue(1)
    return loaded


def test_ms_to_str():
    assert msToStr(3723004) == "1:02:03.004"
    assert msToStr(3723004, False) == "1:02:03"


def test_start(modesolver, qtbot):
    modesolver.show()
    qtbot.waitExposed(modesolver)
    assert modesolver.windowTitle() == "Mode Solver"
    assert modesolver.countLabel.text() == "No fiber"
    assert modesolver.timeLabel.frameShape() == \
        QtWidgets.QFrame.Shape.Panel
    assert modesolver.timeLabel.frameShadow() == \
        QtWidgets.QFrame.Shadow.Sunken
    assert not modesolver.actions['save'].isEnabled()
    assert not modesolver.dirty()
    assert modesolver.documentName() == ""


def test_main(qapp, qtbot, monkeypatch, smf28_file):
    solver = os.path.splitext(smf28_file)[0] + ".solver"
    shown = []

    class FakeApplication:
        def __init__(self, argv):
            pass

        def setApplicationName(self, name):
            pass

        def exec(self):
            shown.extend(w for w in qapp.topLevelWidgets()
                         if isinstance(w, ModeSolver) and w.isVisible())
            return 0

    monkeypatch.setattr(QtWidgets, "QApplication", FakeApplication)
    monkeypatch.setattr(sys, "argv", ["modesolver", solver])
    # The .solver file does not exist: main() still starts the window.
    with pytest.raises(SystemExit) as excinfo:
        modesolverapp.main()
    assert excinfo.value.code == 0
    assert len(shown) == 1
    shown[0].setDirty(False)
    qtbot.addWidget(shown[0])


def test_load_fiber(loaded):
    assert loaded.fiberSelector.fiberName.text() == "smf28"
    assert loaded.actions['edit'].isEnabled()
    assert loaded.actions['info'].isEnabled()
    assert loaded.countLabel.text() == "1 F x 1 W = 1"
    assert loaded.dirty()
    assert loaded.documentName().endswith("smf28.solver")
    assert loaded.wavelengthSlider.vLabel.text().startswith("| V = ")


def test_wavelength_range(loaded):
    loaded.wavelengthInput.setValue(
        {'start': 1300e-9, 'end': 1600e-9, 'num': 4})
    assert loaded.countLabel.text() == "1 F x 4 W = 4"
    assert loaded.wavelengthSlider.wavelengthInput.maximum() == 4
    loaded.wavelengthSlider.slider.setValue(4)
    assert loaded.wavelengthSlider.wlLabel.text() == "1600.00000 nm"


def test_simulation(solved):
    assert solved.modeTableModel.rowCount() > 1
    assert solved.actions['exportcur'].isEnabled()
    assert solved.actions['fields'].isEnabled()
    assert solved.progressBar.value() == solved.progressBar.maximum()
    assert solved.timeLabel.text().startswith("E: ")
    assert solved.showhidesel.modes == solved.modeTableModel.modes


def test_progress_timer(loaded):
    loaded.initProgressBar()
    assert loaded.timer.isActive()
    loaded.updateTime()
    assert loaded.timeLabel.text().startswith("E: 0:00:")
    loaded.stop_simulation()
    assert not loaded.timer.isActive()
    assert loaded.actions['start'].isEnabled()
    assert not loaded.actions['stop'].isEnabled()


def test_run_stop_actions(loaded, qtbot):
    loaded.simParamBoxes['neff'].setChecked(True)
    with qtbot.waitSignal(loaded.doc.computeFinished, timeout=120000):
        loaded.actions['start'].trigger()
    assert not loaded.actions['start'].isEnabled()
    assert loaded.actions['stop'].isEnabled()
    loaded.actions['stop'].trigger()
    assert loaded.actions['start'].isEnabled()
    assert not loaded.doc.ready


def test_save_and_load(solved, qtbot):
    solved.actions['tablewin'].setChecked(False)
    solved.togglePanes()
    solved.plotFrame.plotModel.setData(
        solved.plotFrame.plotModel.index(0, 1),
        Qt.PenStyle.DotLine.value, Qt.ItemDataRole.UserRole)
    solved.nuMaxInput.setValue(3)
    solved.modeSelector.setCurrentIndex(2)

    with qtbot.waitSignal(solved.saved):
        solved.actions['save'].trigger()
    assert not solved.dirty()
    with open(solved.documentName()) as f:
        data = json.load(f)
    assert data['params'] == ["cutoff (V)", "neff"]
    assert data['wl'] == [800e-9, 1550e-9]
    assert data['numax'] == 3
    assert data['modes'] == 2
    assert data['panes'] == {'params': 1, 'modes': 0, 'graph': 1}
    assert data['graph']['yaxis'][0][1] == Qt.PenStyle.DotLine.value

    other = ModeSolver()
    other.doc.numProcs = 1
    qtbot.addWidget(other, before_close_func=lambda w: w.setDirty(False))
    other.actionOpen(solved.documentName())
    assert not other.dirty()
    assert other.doc.params == ["cutoff (V)", "neff"]
    assert other.simParamBoxes['neff'].isChecked()
    assert not other.simParamBoxes['ng'].isChecked()
    assert other.nuMaxInput.value() == 3
    assert other.modeSelector.currentIndex() == 2
    assert not other.actions['tablewin'].isChecked()
    assert other.plotFrame.save() == data['graph']


def test_open_dialog(modesolver, monkeypatch, tmp_path):
    missing = str(tmp_path / "missing.solver")
    calls = []

    def fake_exec(self):
        calls.append(self.acceptMode())
        return ACCEPTED.value

    monkeypatch.setattr(QtWidgets.QFileDialog, "exec", fake_exec)
    monkeypatch.setattr(QtWidgets.QFileDialog, "selectedFiles",
                        lambda self: [missing])
    modesolver.actionOpen()
    assert calls == [QtWidgets.QFileDialog.AcceptMode.AcceptOpen]
    assert modesolver.doc.factory is None  # no .fiber beside the file


def test_export(solved, monkeypatch, tmp_path):
    target = str(tmp_path / "table.csv")
    monkeypatch.setattr(QtWidgets.QFileDialog, "exec",
                        lambda self: ACCEPTED.value)
    monkeypatch.setattr(QtWidgets.QFileDialog, "selectedFiles",
                        lambda self: [target])
    solved.actions['exportcur'].trigger()
    with open(target) as f:
        assert f.readline().strip() == "Mode,cutoff (V),neff"


def test_toggle_panes(modesolver):
    modesolver.actions['paramwin'].setChecked(False)
    modesolver.actions['tablewin'].setChecked(False)
    modesolver.togglePanes()
    assert not modesolver.actions['graphwin'].isEnabled()
    modesolver.actions['tablewin'].setChecked(True)
    modesolver.togglePanes()
    assert modesolver.actions['graphwin'].isEnabled()


@pytest.mark.parametrize("action, attr, cls", [
    ('mcalc', 'mcalc', MaterialCalculator),
    ('wlcalc', 'wlcalc', WavelengthCalculator),
])
def test_calculators(modesolver, qtbot, action, attr, cls):
    modesolver.show()
    qtbot.waitExposed(modesolver)
    modesolver.actions[action].trigger()
    win = getattr(modesolver, attr)
    assert isinstance(win, cls)
    assert win.isVisible()
    modesolver.actions[action].trigger()
    assert not win.isVisible()
    assert not modesolver.actions[action].isChecked()
    modesolver.actions[action].trigger()
    win.close()  # closing the dialog unchecks the action
    assert not modesolver.actions[action].isChecked()


def test_sim_params(loaded, monkeypatch):
    def fake_exec(self):
        self.numProcs.setValue(1)
        self.delta.setText("1.000000e-04")
        return 0

    monkeypatch.setattr(SimParamsDialog, "exec", fake_exec)
    loaded.actions['simparams'].trigger()
    assert loaded.doc.numProcs == 1
    assert loaded.doc.simulator.delta == 1e-4


def test_sim_params_dialog(qtbot, loaded):
    dlg = SimParamsDialog(loaded.doc)
    qtbot.addWidget(dlg)
    validator = dlg.delta.validator()
    assert validator.bottom() == 1e-31
    assert validator.top() == 1
    state, _, _ = validator.validate("1e-6", 0)
    assert state == validator.State.Acceptable
    state, _, _ = validator.validate("2", 0)
    assert state != validator.State.Acceptable


def test_chareq(solved, qtbot):
    solved.modeTableView.selectRow(0)
    solved.actions['plotchareq'].trigger()
    dialogs = [w for w in solved.findChildren(CharEqDialog)]
    assert len(dialogs) == 1
    dlg = dialogs[0]
    qtbot.addWidget(dlg)
    assert dlg.windowTitle().startswith("Characteristic function")
    dlg.zeros.setChecked(True)
    dlg.points.setChecked(True)
    dlg.modeInput.setCurrentText("LP")
    dlg.fType.setCurrentIndex(1)
    assert dlg.windowTitle().startswith("Cutoff function")
    dlg.zeros.setChecked(False)
    dlg.delta.setText("1e-5")


def test_fields(solved, qtbot):
    solved.modeTableView.selectRow(0)
    solved.actions['fields'].trigger()
    viewers = solved.findChildren(FieldVisualizer)
    assert len(viewers) == 1
    viewers[0].options.np.setValue(50)
    qtbot.addWidget(viewers[0])
    assert viewers[0].isVisible()
    assert len(viewers[0].modes) == 1


@pytest.mark.parametrize("what, option", [(0, 0), (1, 0), (2, 1), (3, 0)])
def test_show_hide_modes(solved, what, option):
    model = solved.modeTableModel
    solved.on_hide_modes(what, option)
    hidden = {m for m, sel in solved.doc.selection.items() if not sel}
    if what == 0:
        assert hidden == set(model.modes)
    elif what == 1:
        assert hidden == {m for m in model.modes
                          if m.family is ModeFamily(option + 1)}
    elif what == 2:
        assert hidden == {m for m in model.modes if m.nu == option}
    else:
        assert hidden == {m for m in model.modes if m.m == option + 1}
    assert hidden
    solved.on_show_modes(0, 0)
    assert all(solved.doc.selection.values())


def test_show_hide_widget(qtbot, solved):
    w = solved.showhidesel
    assert not w.options.isEnabled()
    w.what.setCurrentIndex(1)
    assert w.options.isEnabled()
    items = [w.options.itemText(i) for i in range(w.options.count())]
    assert items == [f.name for f in ModeFamily]
    present = {m.family.name for m in w.modes}
    for i, name in enumerate(items):
        flags = w.options.model().item(i).flags()
        assert bool(flags & Qt.ItemFlag.ItemIsEnabled) == (name in present)

    with qtbot.waitSignal(w.hideModes) as blocker:
        w.bhide.click()
    assert blocker.args == [1, 0]
    with qtbot.waitSignal(w.showModes):
        w.bshow.click()


def test_show_hide_empty(qtbot):
    w = ShowHideMode()
    qtbot.addWidget(w)
    for i in range(4):
        w.what.setCurrentIndex(i)


def test_fiber_properties(loaded, monkeypatch):
    shown = []
    monkeypatch.setattr(QtWidgets.QMessageBox, "exec",
                        lambda self: shown.append(self.text()) or 0)
    loaded.actions['info'].trigger()
    assert len(shown) == 1
    assert "smf28" in shown[0]


def test_choose_fiber(modesolver, monkeypatch, smf28_file):
    monkeypatch.setattr(QtWidgets.QFileDialog, "exec",
                        lambda self: ACCEPTED.value)
    monkeypatch.setattr(QtWidgets.QFileDialog, "selectedFiles",
                        lambda self: [smf28_file])
    modesolver.actions['load'].trigger()
    assert modesolver.doc.filename == smf28_file
    assert modesolver.fiberSelector.fiberName.text() == "smf28"


def test_edit_fiber(loaded, qtbot):
    loaded.actions['edit'].trigger()
    editor = loaded.fiberSelector._editWin
    assert editor is not None
    qtbot.addWidget(editor, before_close_func=lambda w: w.setDirty(False))
    assert editor.isVisible()
    assert editor.documentName() == loaded.doc.filename
    with qtbot.waitSignal(loaded.fiberSelector.fiberEdited):
        editor.save()
    editor.close()
    assert loaded.fiberSelector._editWin is None


def test_fiber_slider(loaded):
    slider = loaded.fiberSlider
    assert slider.totLabel.text() == "/ 1"
    assert slider.fiberInput.minimum() == 1
    slider.setNum(0)
    assert slider.fiberInput.minimum() == 0
