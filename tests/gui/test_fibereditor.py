"""Tests for the fiber editor application (fibermodesgui.fibereditor)."""

import json
import os.path
import sys

import pytest
from qtpy import QtCore, QtWidgets

from fibermodes import FiberFactory
from fibermodes.fiber import material
from fibermodesgui import fibereditorapp
from fibermodesgui.fibereditor.fiberplot import FiberPlot
from fibermodesgui.fibereditor.fiberproperties import FiberPropertiesWindow
from fibermodesgui.fibereditor.infotable import FiberInfoTable
from fibermodesgui.fibereditor.mainwindow import FiberEditor

_FIBERS = os.path.join(os.path.dirname(__file__), os.pardir, "fiber")
SMF28 = os.path.normpath(os.path.join(_FIBERS, "smf28.fiber"))
RCFS = os.path.normpath(os.path.join(_FIBERS, "rcfs.fiber"))

ACCEPTED = QtWidgets.QDialog.DialogCode.Accepted
REJECTED = QtWidgets.QDialog.DialogCode.Rejected


@pytest.fixture
def editor(qtbot):
    w = FiberEditor()
    # qtbot closes the window at teardown; a dirty window would ask to save.
    qtbot.addWidget(w, before_close_func=lambda w: w.setDirty(False))
    return w


@pytest.fixture
def smf28():
    factory = FiberFactory()
    with open(SMF28) as f:
        factory.load(f)
    return factory[0]


def _layer_names(editor):
    lst = editor.layerList
    return [lst.item(i).text() for i in range(lst.count())]


def _form_labels(layout):
    labels = []
    for row in range(layout.rowCount()):
        item = layout.itemAt(row, QtWidgets.QFormLayout.ItemRole.LabelRole)
        if item is not None and item.widget() is not None:
            labels.append(item.widget().text())
    return labels


def test_start(editor):
    assert editor.windowTitle() == "Fiber Editor"
    assert _layer_names(editor) == ["core", "cladding"]
    assert not editor.dirty()
    assert not editor.actions['save'].isEnabled()
    assert editor.actions['new'].shortcuts()
    assert editor.infoTable.columnCount() == 2


def test_main(qapp, qtbot, monkeypatch):
    shown = []

    class FakeApplication:
        def __init__(self, argv):
            pass

        def setApplicationName(self, name):
            pass

        def exec(self):
            shown.extend(w for w in qapp.topLevelWidgets()
                         if isinstance(w, FiberEditor) and w.isVisible())
            return 0

    monkeypatch.setattr(QtWidgets, "QApplication", FakeApplication)
    monkeypatch.setattr(sys, "argv", ["fibereditor", SMF28])
    with pytest.raises(SystemExit) as excinfo:
        fibereditorapp.main()
    assert excinfo.value.code == 0
    assert len(shown) == 1
    qtbot.addWidget(shown[0])
    assert shown[0].documentName() == SMF28


def test_open_file(editor):
    editor.actionOpen(SMF28)
    assert editor.documentName() == SMF28
    assert _layer_names(editor) == ["core", "cladding"]
    assert not editor.dirty()


def test_open_dialog(editor, monkeypatch):
    def fake_exec(self):
        self.selectFile(SMF28)
        return ACCEPTED.value

    monkeypatch.setattr(QtWidgets.QFileDialog, "exec", fake_exec)
    monkeypatch.setattr(QtWidgets.QFileDialog, "selectedFiles",
                        lambda self: [SMF28])
    editor.actionOpen()
    assert editor.documentName() == SMF28


def test_open_dialog_cancel(editor, monkeypatch):
    monkeypatch.setattr(QtWidgets.QFileDialog, "exec",
                        lambda self: REJECTED.value)
    editor.actionOpen()
    assert editor.documentName() == ""


def test_save_as_round_trip(editor, tmp_path, monkeypatch):
    target = str(tmp_path / "new.fiber")
    monkeypatch.setattr(QtWidgets.QFileDialog, "exec",
                        lambda self: ACCEPTED.value)
    monkeypatch.setattr(QtWidgets.QFileDialog, "selectedFiles",
                        lambda self: [target])
    editor.layerList.setCurrentRow(0)
    editor.addLayer()
    assert editor.dirty()
    editor.save()  # no document name: goes through actionSaveAs
    assert editor.documentName() == target
    assert not editor.dirty()

    with open(target) as f:
        data = json.load(f)
    assert len(data["layers"]) == 3

    editor.actionNew()
    assert not editor.dirty()
    editor.actionOpen(target)
    assert _layer_names(editor) == ["core", "layer 2", "cladding"]


def test_add_remove_layer(editor):
    editor.layerList.setCurrentRow(0)
    assert editor.actions['remove'].isEnabled()
    editor.actionAddLayer()
    assert _layer_names(editor) == ["core", "layer 2", "cladding"]
    assert editor.layerList.currentRow() == 1
    assert editor.dirty()
    assert editor.actions['save'].isEnabled()
    editor.actionRemoveLayer()
    assert _layer_names(editor) == ["core", "cladding"]


def test_last_layer_cannot_be_removed(editor):
    editor.layerList.setCurrentRow(1)
    assert not editor.actions['remove'].isEnabled()
    assert not editor.geomType.isEnabled()


def test_layer_name(editor):
    editor.layerList.setCurrentRow(0)
    editor.layerName.setText("center")
    assert _layer_names(editor)[0] == "center"
    assert editor.factory.layers[0].name == "center"
    editor.layerName.setText("")
    assert _layer_names(editor)[0] == "layer 1"


def test_geometry(editor):
    editor.layerList.setCurrentRow(0)
    assert editor.geomType.currentText() == "StepIndex"
    assert _form_labels(editor.geomLayout) == ["Geometry type:", "Radius:"]
    assert editor.radiusInput.value == pytest.approx(4e-6)

    editor.radiusInput.numberInput.setValue(5)
    assert editor.factory.layers[0].tparams[0] == pytest.approx(5e-6)
    assert editor.dirty()

    editor.geomType.setCurrentText("SuperGaussian")
    assert editor.factory.layers[0].type == "SuperGaussian"
    assert _form_labels(editor.geomLayout) == [
        "Geometry type:", "Radius:", "Center (mu):", "Width (c):",
        "m parameter:"]


@pytest.mark.parametrize("name", [
    "Fixed",  # index parameter
    "SiO2GeO2",  # concentration parameter
    "Silica",  # no parameter
] + [pytest.param(name, marks=pytest.mark.stress)
     for name in material.__all__
     if name not in ("Fixed", "SiO2GeO2", "Silica")])
def test_material(editor, qtbot, name):
    editor.layerList.setCurrentRow(0)
    editor.matType.setCurrentText(name)
    assert editor.factory.layers[0].material == name
    labels = _form_labels(editor.matLayout)
    mat = material.__dict__[name]
    if issubclass(mat, material.Fixed):
        assert labels == ["Material type:", "Index:"]
    elif issubclass(mat, material.compmaterial.CompMaterial):
        assert labels == ["Material type:", "Molar concentration:"]
    else:
        assert labels == ["Material type:"]


def test_fixed_index(editor):
    editor.layerList.setCurrentRow(0)
    editor.indexInput.numberInput.setValue(1.46)
    assert editor.factory.layers[0].mparams[0] == pytest.approx(1.46)


def test_about_material(editor, monkeypatch):
    shown = []

    def fake_exec(self):
        shown.append(self.text())
        return 0

    monkeypatch.setattr(QtWidgets.QMessageBox, "exec", fake_exec)
    editor.layerList.setCurrentRow(0)
    editor.matType.setCurrentText("Silica")
    editor.aboutFiberMaterial()
    assert len(shown) == 1
    assert material.Silica.name in shown[0]


def test_fiber_number(editor):
    editor.actionOpen(RCFS)
    n = len(editor.factory)
    assert n > 1
    assert editor.fnumInput.maximum() == n
    assert editor.fnumSlider.maximum() == n
    editor.fnumSlider.setValue(2)
    assert editor.fnumInput.value() == 2


def test_wavelength_changes_info(editor):
    editor.matType.setEnabled(True)
    editor.layerList.setCurrentRow(0)
    editor.matType.setCurrentText("Silica")
    before = editor.infoTable.item(3, 0).text()
    editor.wlInput.setValue(1000)
    assert editor.infoTable.item(3, 0).text() != before


def test_fiber_properties(editor, monkeypatch):
    shown = []

    def fake_exec(self):
        shown.append(self)
        self.nameInput.setText("renamed")
        self.accept()
        return ACCEPTED.value

    monkeypatch.setattr(QtWidgets.QDialog, "exec", fake_exec)
    editor.actionOpen(SMF28)
    editor.actionInfo()
    assert len(shown) == 1
    assert editor.factory._fibers["name"] == "renamed"
    assert editor.dirty()


def test_fiber_properties_window(qtbot, monkeypatch):
    fibers = FiberFactory()._fibers
    fibers.update(name="n", author="a", description="d",
                  crdate=0, tstamp=0)
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)
    monkeypatch.setattr(QtWidgets.QDialog, "exec",
                        lambda self: REJECTED.value)
    dlg = FiberPropertiesWindow(fibers, parent)
    assert dlg.exec() == REJECTED.value
    assert dlg.nameInput.text() == "n"
    assert dlg.authorInput.text() == "a"
    assert dlg.descriptionInput.toPlainText() == "d"
    assert dlg.crdateLabel.text()


def test_info_table(qtbot, smf28):
    table = FiberInfoTable()
    qtbot.addWidget(table)
    table.updateInfo(smf28, 1550e-9)
    assert table.columnCount() == 2
    assert table.item(0, 0).text() == "0.00000 µm"
    assert table.item(1, 0).text() == "4.50000 µm"
    assert table.item(1, 1).text() == "∞"
    assert table.item(1, 1).textAlignment() == \
        QtCore.Qt.AlignmentFlag.AlignCenter.value
    assert table.item(3, 0).text() == "1.44890"


def test_fiber_plot(qtbot, smf28):
    plot = FiberPlot()
    qtbot.addWidget(plot)
    plot.updateInfo(smf28, 1550e-9)
    x, y = plot.curve.getData()
    assert len(x) > 0
    assert max(y) == pytest.approx(1.4489)
    plot.lineWidthSpinBox.setValue(3)
    assert plot.curve.opts['pen'].widthF() == 3
    plot.backgroundColorButton.setColor((10, 20, 30))
    plot.updateBgColor()


def test_fiber_plot_import_and_delete(qtbot, monkeypatch, tmp_path, smf28):
    csvfile = tmp_path / "data.csv"
    csvfile.write_text("-1,1.444\n0,1.449\n1,1.444\n")
    plot = FiberPlot()
    qtbot.addWidget(plot)
    plot.updateInfo(smf28, 1550e-9)

    monkeypatch.setattr(
        QtWidgets.QFileDialog, "getOpenFileName",
        lambda *args, **kwargs: (str(csvfile),
                                 "Comma Separated Values (*.csv)"))
    plot.importData()
    assert plot.dataFile == str(csvfile)
    assert plot.fiberData.shape == (2, 3)
    assert plot.deleteDataAction.isEnabled()
    assert plot.dataFgColorButton.isEnabled()

    monkeypatch.setattr(
        QtWidgets.QMessageBox, "warning",
        lambda *args, **kwargs: QtWidgets.QMessageBox.StandardButton.No)
    plot.deleteData()
    assert plot.fiberData is not None

    monkeypatch.setattr(
        QtWidgets.QMessageBox, "warning",
        lambda *args, **kwargs: QtWidgets.QMessageBox.StandardButton.Yes)
    plot.deleteData()
    assert plot.fiberData is None
    assert not plot.deleteDataAction.isEnabled()


def test_fiber_plot_import_cancel(qtbot, monkeypatch, smf28):
    plot = FiberPlot()
    qtbot.addWidget(plot)
    monkeypatch.setattr(QtWidgets.QFileDialog, "getOpenFileName",
                        lambda *args, **kwargs: ("", ""))
    plot.importData()
    assert plot.fiberData is None


def test_fiber_plot_double_click(qtbot, smf28):
    plot = FiberPlot()
    qtbot.addWidget(plot)
    plot.updateInfo(smf28, 1550e-9)
    viewBox = plot.plot.getPlotItem().getViewBox()
    viewBox.setXRange(0, 1, 0)

    class Event:
        def double(self):
            return True

    plot.mouseClickEvent(Event())
    xmin, xmax = viewBox.viewRange()[0]
    assert xmin == pytest.approx(-4.5 * 1.5)
    assert xmax == pytest.approx(4.5 * 1.5)


def test_new_after_open_keeps_layers(editor):
    """actionNew on a loaded fiber does not rename the last layer, and the
    new fiber is not dirty."""
    editor.actionOpen(SMF28)
    editor.layerList.setCurrentRow(0)
    editor.actionNew()
    assert [layer.name for layer in editor.factory.layers] == \
        ["core", "cladding"]
    assert _layer_names(editor) == ["core", "cladding"]
    assert not editor.dirty()
