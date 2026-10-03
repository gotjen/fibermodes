"""Tests for fibermodesgui.modesolver.plotframe."""

import json

import pytest
from qtpy import QtCore, QtWidgets

from fibermodesgui.modesolver.plotframe import (
    LINES, LINESV, MARK, MARKV, VNUMBER, WAVELENGTHS, FIBERS, YAXISLIST)

from .conftest import compute, load_fiber

Qt = QtCore.Qt


@pytest.fixture
def frame(modesolver, qtbot, smf28_file):
    modesolver.doc.numProcs = 1
    load_fiber(modesolver, smf28_file)
    compute(qtbot, modesolver, params=("cutoff (V)", "neff", "b"),
            wavelengths={'start': 1000e-9, 'end': 1600e-9, 'num': 4})
    return modesolver.plotFrame


def _curves(frame):
    return frame.plot.getPlotItem().curves


def test_line_styles_are_ints():
    """Pen styles are stored as int values (JSON and model friendly)."""
    assert all(isinstance(v, int) for v in LINESV)
    assert Qt.PenStyle(LINESV[0]) == Qt.PenStyle.SolidLine
    assert len(LINES) == len(LINESV)


def test_default_plot(frame):
    assert frame.xAxisSelector.currentIndex() == VNUMBER
    assert frame.plotModel.plots == [[0, Qt.PenStyle.SolidLine.value, None]]
    assert _curves(frame)


def test_line_style(frame):
    model = frame.plotModel
    style = Qt.PenStyle.DashLine.value
    model.setData(model.index(0, 1), style, Qt.ItemDataRole.UserRole)
    assert model.data(model.index(0, 1), Qt.ItemDataRole.DisplayRole) == \
        LINES[LINESV.index(style)]
    curves = _curves(frame)
    assert curves
    assert all(c.opts['pen'].style() == Qt.PenStyle.DashLine
               for c in curves)


def test_marks(frame):
    """No mark, one mark per mode family, and a fixed mark."""
    model = frame.plotModel
    for mark in (None, 'Mode', 's'):
        model.setData(model.index(0, 2), mark, Qt.ItemDataRole.UserRole)
        assert model.data(model.index(0, 2),
                          Qt.ItemDataRole.DisplayRole) == \
            MARK[MARKV.index(mark)]
        symbols = {c.opts['symbol'] for c in _curves(frame)}
        if mark is None:
            assert symbols == {None}
        elif mark == 'Mode':
            assert symbols <= {'o', 's', 't', 'd', '+'}
            assert len(symbols) > 1
        else:
            assert symbols == {'s'}


def test_legend_on_off(frame):
    legend_box = frame.plotOptions.showLegend
    for _ in range(2):
        legend_box.setChecked(True)
        assert frame.legend is not None
        assert frame.legend.isVisible()
        assert frame.legend.scene() is frame.plot.scene()
        assert len(frame.legend.items) == len(_curves(frame))
        legend_box.setChecked(False)
        assert frame.legend is None or not frame.legend.isVisible()


def test_x_axis_and_options(frame):
    opts = frame.plotOptions
    for xaxis in (FIBERS, WAVELENGTHS, VNUMBER):
        frame.xAxisSelector.setCurrentIndex(xaxis)
        assert len(frame.X) == (1 if xaxis == FIBERS else 4)
        assert _curves(frame)
        # Only "cutoff (V)" is computed: cutoffs need the V number axis.
        assert opts.showCutoffs.isEnabled() == (xaxis == VNUMBER)

    opts.showCutoffs.setChecked(True)
    opts.showLayers.setChecked(True)
    opts.showCurrentFiberWl.setChecked(True)
    for xaxis in (WAVELENGTHS, VNUMBER):
        frame.xAxisSelector.setCurrentIndex(xaxis)
        assert _curves(frame)


def test_layers_normalized(frame):
    model = frame.plotModel
    model.setData(model.index(0, 0), 2, Qt.ItemDataRole.UserRole)  # b
    frame.plotOptions.showLayers.setChecked(True)
    frame.xAxisSelector.setCurrentIndex(FIBERS)
    frame.xAxisSelector.setCurrentIndex(WAVELENGTHS)


def test_hidden_modes_not_plotted(frame):
    n = len(_curves(frame))
    mode = next(iter(frame.doc.modes[0][0]))
    frame.doc.selection[mode] = False
    frame.updatePlot()
    assert len(_curves(frame)) == n - 1


def test_add_remove_rows(frame):
    model = frame.plotModel
    assert not frame.minusBut.isEnabled()
    frame.plusBut.click()
    assert len(model.plots) == 2
    assert model.plots[1][0] == 1
    assert frame.minusBut.isEnabled()
    frame.plusBut.click()
    frame.plusBut.click()  # no more params
    assert len(model.plots) == 3
    assert not frame.plusBut.isEnabled()
    frame.yAxisTable.removeRow()
    assert len(model.plots) == 2
    model.removeRow(0)
    model.removeRow(0)  # keep at least one
    assert len(model.plots) == 1


def test_yaxis_editor(frame, qtbot):
    model = frame.plotModel
    index = model.index(0, 0)
    items, values = model.data(index, YAXISLIST)
    assert list(items) == ["cutoff (V)", "neff", "b"]
    assert list(values) == [0, 1, 2]

    table = frame.yAxisTable
    editor = table.propertyItemDelegate.createEditor(
        table.viewport(), QtWidgets.QStyleOptionViewItem(), index)
    assert isinstance(editor, QtWidgets.QComboBox)
    editor.deleteLater()

    editor = table.lineStyleItemDelegate.createEditor(
        table.viewport(), QtWidgets.QStyleOptionViewItem(), model.index(0, 1))
    table.lineStyleItemDelegate.setEditorData(editor, model.index(0, 1))
    assert editor.currentIndex() == 0
    editor.setCurrentIndex(1)
    table.lineStyleItemDelegate.setModelData(editor, model,
                                             model.index(0, 1))
    assert model.plots[0][1] == LINESV[1]
    editor.deleteLater()


def test_save_load_round_trip(frame):
    model = frame.plotModel
    frame.plusBut.click()
    model.setData(model.index(1, 1), LINESV[2], Qt.ItemDataRole.UserRole)
    model.setData(model.index(1, 2), 's', Qt.ItemDataRole.UserRole)
    frame.xAxisSelector.setCurrentIndex(WAVELENGTHS)
    frame.plotOptions.showLegend.setChecked(True)
    frame.plotOptions.showLayers.setChecked(True)

    saved = json.loads(json.dumps(frame.save()))
    assert saved['yaxis'] == [[0, LINESV[0], None], [1, LINESV[2], 's']]

    frame.plotModel.load([[0, LINESV[0], None]])
    frame.xAxisSelector.setCurrentIndex(VNUMBER)
    frame.plotOptions.load({'legend': False, 'cutoffs': False,
                            'layers': False, 'current': False})

    frame.load(saved)
    assert frame.save() == saved
    assert frame.plotOptions.showLegend.isChecked()
    neff = [c for c in _curves(frame)
            if (c.name() or "").endswith("(neff)")]
    assert neff
    assert all(c.opts['pen'].style() == Qt.PenStyle.DashLine for c in neff)


def test_load_old_solver_pen_style(frame):
    """Files saved before the Qt6 port stored the pen style as an int
    (hash(Qt.DotLine) == 3)."""
    frame.load({'xaxis': VNUMBER,
                'options': {'legend': False, 'cutoffs': False,
                            'layers': False, 'current': False},
                'yaxis': [[1, 3, 'Mode']]})
    curves = _curves(frame)
    assert curves
    assert all(c.opts['pen'].style() == Qt.PenStyle.DotLine for c in curves)


def test_options_button(frame, qtbot):
    frame.optionsBut.setChecked(True)
    assert frame.plotOptions.isVisible()
    frame.plotOptions.hide()
    assert not frame.optionsBut.isChecked()
