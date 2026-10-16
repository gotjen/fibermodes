"""Tests for fibermodesgui.modesolver.modetable."""

import pytest
from qtpy import QtCore

from fibermodes import HE11

from .conftest import compute, load_fiber

Qt = QtCore.Qt


@pytest.fixture
def solved(modesolver, qtbot, smf28_file):
    modesolver.doc.numProcs = 1
    load_fiber(modesolver, smf28_file)
    compute(qtbot, modesolver, params=("cutoff (V)", "neff", "vg"),
            wavelengths=[1000e-9, 1550e-9])
    modesolver.wavelengthSlider.wavelengthInput.setValue(1)
    return modesolver


def test_shape(solved):
    model = solved.modeTableModel
    assert model.rowCount() == len(solved.doc.modes[0][0])
    assert model.rowCount() > 1
    assert model.rowCount(QtCore.QModelIndex()) == model.rowCount()
    assert model.columnCount() == 4


def test_headers(solved):
    model = solved.modeTableModel
    H, V = Qt.Orientation.Horizontal, Qt.Orientation.Vertical
    assert model.headerData(0, H, Qt.ItemDataRole.DisplayRole) == ""
    assert model.headerData(0, H, Qt.ItemDataRole.ToolTipRole) == \
        "Plot mode"
    assert model.headerData(1, H, Qt.ItemDataRole.DisplayRole) == \
        "cutoff (V)"
    mode = model.headerData(0, V, Qt.ItemDataRole.UserRole)
    assert model.headerData(0, V, Qt.ItemDataRole.DisplayRole) == str(mode)
    assert model.headerData(99, V, Qt.ItemDataRole.DisplayRole) is None


def test_roles(solved):
    model = solved.modeTableModel
    row = model.modes.index(HE11)
    neff = model.index(row, 2)
    value = model.data(neff, Qt.ItemDataRole.UserRole)
    assert isinstance(value, float)
    assert 1.444 < value < 1.449
    assert model.data(neff, Qt.ItemDataRole.DisplayRole) == \
        "{:.5g}".format(value)
    assert model.data(neff, Qt.ItemDataRole.ToolTipRole) == value

    cutoff = model.index(row, 1)
    assert model.data(cutoff, Qt.ItemDataRole.DisplayRole) == "0"

    vg = model.index(row, 3)
    assert model.data(vg, Qt.ItemDataRole.DisplayRole).endswith(" m / us")


def test_check_state(solved):
    model = solved.modeTableModel
    index = model.index(0, 0)
    assert model.flags(index) & Qt.ItemFlag.ItemIsUserCheckable
    assert model.data(index, Qt.ItemDataRole.CheckStateRole) == \
        Qt.CheckState.Checked
    assert model.data(index, Qt.ItemDataRole.DisplayRole) is None

    mode = model.modes[0]
    # A view sends the check state as an int.
    model.setData(index, Qt.CheckState.Unchecked.value,
                  Qt.ItemDataRole.CheckStateRole)
    assert solved.doc.selection[mode] is False
    assert model.data(index, Qt.ItemDataRole.CheckStateRole) == \
        Qt.CheckState.Unchecked

    model.setData(index, Qt.CheckState.Checked,
                  Qt.ItemDataRole.CheckStateRole)
    assert solved.doc.selection[mode] is True


def test_sort_proxy(solved):
    proxy = solved.modeTableProxy
    assert proxy.sortRole() == Qt.ItemDataRole.UserRole
    proxy.sort(2, Qt.SortOrder.DescendingOrder)
    values = [proxy.data(proxy.index(r, 2), Qt.ItemDataRole.UserRole)
              for r in range(proxy.rowCount())]
    assert values == sorted(values, reverse=True)
    proxy.sort(2, Qt.SortOrder.AscendingOrder)
    values = [proxy.data(proxy.index(r, 2), Qt.ItemDataRole.UserRole)
              for r in range(proxy.rowCount())]
    assert values == sorted(values)


def test_selected_modes(solved, qtbot):
    view = solved.modeTableView
    with qtbot.waitSignal(view.selChanged) as blocker:
        view.selectRow(0)
    source = solved.modeTableProxy.mapToSource(
        solved.modeTableProxy.index(0, 0))
    expected = [solved.modeTableModel.modes[source.row()]]
    assert view.selectedModes() == expected
    assert blocker.args == [expected]


def test_wavelength_change_updates_rows(solved):
    model = solved.modeTableModel
    n1000 = model.rowCount()
    solved.wavelengthSlider.wavelengthInput.setValue(2)
    assert model.rowCount() == len(solved.doc.modes[0][1])
    assert model.rowCount() < n1000


def test_value_available_updates_its_column(solved, qtbot):
    """Column 0 is the check box, so parameter j is in column j + 1."""
    model = solved.modeTableModel
    mode = model.modes[0]
    with qtbot.waitSignal(model.dataChanged) as blocker:
        solved.doc.valueAvailable.emit(0, 0, mode, 1)
    top_left = blocker.args[0]
    assert (top_left.row(), top_left.column()) == (0, 2)
