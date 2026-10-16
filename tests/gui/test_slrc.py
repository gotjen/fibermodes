"""Tests for fibermodesgui.widgets.slrc (SLRCWidget and its dialogs)."""

import pytest
from qtpy import QtCore, QtWidgets

from fibermodesgui.widgets import SLRCWidget
from fibermodesgui.widgets.slrc import CodeEditor, ListEditor


@pytest.fixture
def slrc(qtbot):
    w = SLRCWidget()
    qtbot.addWidget(w)
    return w


def _inner_widgets(w):
    layout = w.innerLayout
    return [layout.itemAt(i).widget() for i in range(layout.count())]


def test_construction(slrc):
    assert slrc.kind == 'scalar'
    assert _inner_widgets(slrc) == [slrc.numberInput]
    assert slrc.typeButton.popupMode() == \
        QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup
    assert [a.text() for a in slrc.typeMenu.actions()] == \
        ["scalar", "list", "range", "code"]


def test_scalar_value_signal(slrc, qtbot):
    slrc.setScaleFactor(1e9)
    slrc.setRange(0, 5000)
    with qtbot.waitSignal(slrc.valueChanged) as blocker:
        slrc.numberInput.setValue(1550)
    assert blocker.args[0] == pytest.approx(1550e-9)
    assert slrc.value == pytest.approx(1550e-9)


@pytest.mark.parametrize("value, kind, widgets", [
    ([1, 2, 3], 'list', ['listLabel', 'listButton']),
    ({'start': 1, 'end': 2, 'num': 5}, 'range',
     ['rstartInput', 'rendInput', 'rnumInput']),
    ("return 1", 'code', ['codeButton']),
    (2.5, 'scalar', ['numberInput']),
])
def test_set_value_layout(slrc, value, kind, widgets):
    slrc.setRange(0, 100)
    slrc.setValue(value)
    assert slrc.kind == kind
    assert _inner_widgets(slrc) == [getattr(slrc, n) for n in widgets]


def test_list_count(slrc):
    slrc.setValue([1, 2, 3])
    assert slrc.listLabel.text() == "3 items"
    slrc.setValue([1])
    assert slrc.listLabel.text() == "1 item"


def test_range_inputs(slrc, qtbot):
    slrc.setRange(0, 100)
    slrc.setValue({'start': 1, 'end': 2, 'num': 5})
    assert slrc.rstartInput.value() == 1
    assert slrc.rendInput.value() == 2
    assert slrc.rnumInput.value() == 5
    with qtbot.waitSignal(slrc.valueChanged):
        slrc.rnumInput.setValue(3)
    assert slrc.value == [1, 1.5, 2]


def test_type_actions(slrc, qtbot):
    with qtbot.waitSignal(slrc.valueChanged):
        slrc.listAction.trigger()
    assert slrc.kind == 'list'
    slrc.rangeAction.trigger()
    assert slrc.kind == 'range'
    slrc.codeAction.trigger()
    assert slrc.kind == 'code'
    slrc.scalarAction.trigger()
    assert slrc.kind == 'scalar'


def test_setters(slrc):
    slrc.setSuffix(" nm")
    slrc.setDecimals(2)
    slrc.setRange(-1, 1)
    slrc.setSingleStep(0.5)
    for box in (slrc.numberInput, slrc.rstartInput, slrc.rendInput):
        assert box.suffix() == " nm"
        assert box.decimals() == 2
        assert (box.minimum(), box.maximum()) == (-1, 1)
        assert box.singleStep() == 0.5


def _patch_exec(monkeypatch, cls, result, edit=None):
    def fake_exec(self):
        if edit:
            edit(self)
        return result.value

    monkeypatch.setattr(cls, "exec", fake_exec)


def test_edit_list_accepted(slrc, qtbot, monkeypatch):
    slrc.setValue([1, 2])

    def edit(dlg):
        dlg.numlist.append(3)

    _patch_exec(monkeypatch, ListEditor,
                QtWidgets.QDialog.DialogCode.Accepted, edit)
    with qtbot.waitSignal(slrc.valueChanged):
        slrc.editList()
    assert slrc.value == [1, 2, 3]
    assert slrc.listLabel.text() == "3 items"


def test_edit_list_rejected(slrc, qtbot, monkeypatch):
    slrc.setValue([1, 2])

    def edit(dlg):
        dlg.numlist.append(3)

    _patch_exec(monkeypatch, ListEditor,
                QtWidgets.QDialog.DialogCode.Rejected, edit)
    with qtbot.assertNotEmitted(slrc.valueChanged):
        slrc.editList()
    assert slrc.value == [1, 2]


def test_edit_code(slrc, qtbot, monkeypatch):
    slrc.setValue("return 1")

    def edit(dlg):
        dlg.codeEditor.setPlainText("return 2")

    _patch_exec(monkeypatch, CodeEditor,
                QtWidgets.QDialog.DialogCode.Accepted, edit)
    with qtbot.waitSignal(slrc.valueChanged):
        slrc.editCode()
    assert slrc() == 2


def test_list_editor(qtbot):
    dlg = ListEditor([1.0, 2.0])
    qtbot.addWidget(dlg)
    lst = dlg.numbersList
    assert lst.count() == 2
    flags = lst.item(0).flags()
    assert flags & QtCore.Qt.ItemFlag.ItemIsEditable
    assert dlg.buttonRemove.isEnabled()

    lst.setCurrentRow(0)
    dlg.addItem()
    assert dlg.numlist == [1.0, 1.5, 2.0]
    assert lst.item(1).text() == "1.5"

    lst.setCurrentRow(2)
    dlg.addItem()
    assert dlg.numlist == [1.0, 1.5, 2.0, 2.5]

    lst.setCurrentRow(1)
    dlg.removeItem()
    assert dlg.numlist == [1.0, 2.0, 2.5]

    lst.setCurrentRow(1)
    lst.currentItem().setText("3")
    assert dlg.numlist == [1.0, 3.0, 2.5]


def test_list_editor_single_item(qtbot):
    dlg = ListEditor([1.0])
    qtbot.addWidget(dlg)
    assert not dlg.buttonRemove.isEnabled()
    dlg.addItem()
    assert dlg.numlist == [1.0, 2.0]
    assert dlg.buttonRemove.isEnabled()
    dlg.removeItem()
    assert not dlg.buttonRemove.isEnabled()


def test_code_editor(qtbot):
    dlg = CodeEditor("return x", ["x"])
    qtbot.addWidget(dlg)
    assert dlg.codeEditor.toPlainText() == "return x"
    labels = [w.text() for w in dlg.findChildren(QtWidgets.QLabel)]
    assert "def f(x):" in labels
    dlg.codeEditor.setPlainText("return 2 * x")
    assert dlg.code == "return 2 * x"
