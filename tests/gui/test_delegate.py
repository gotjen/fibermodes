"""Tests for fibermodesgui.widgets.delegate.ComboItemDelegate."""

import pytest
from qtpy import QtCore, QtGui, QtWidgets

from fibermodesgui.widgets.delegate import ComboItemDelegate


@pytest.fixture
def model():
    m = QtGui.QStandardItemModel(1, 1)
    m.setData(m.index(0, 0), "b", QtCore.Qt.ItemDataRole.DisplayRole)
    m.setData(m.index(0, 0), 1, QtCore.Qt.ItemDataRole.UserRole)
    return m


def test_no_items(qtbot, model):
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)
    delegate = ComboItemDelegate(parent)
    option = QtWidgets.QStyleOptionViewItem()
    assert delegate.createEditor(parent, option, model.index(0, 0)) is None


def test_values(qtbot, model):
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)
    delegate = ComboItemDelegate(parent, ["a", "b", "c"], ["a", "b", "c"])
    index = model.index(0, 0)
    editor = delegate.createEditor(
        parent, QtWidgets.QStyleOptionViewItem(), index)
    assert isinstance(editor, QtWidgets.QComboBox)
    assert editor.count() == 3

    delegate.setEditorData(editor, index)
    assert editor.currentIndex() == 1

    with qtbot.waitSignal(delegate.commitData) as blocker:
        editor.setCurrentIndex(2)
    assert blocker.args == [editor]
    delegate.setModelData(editor, model, index)
    assert index.data() == "c"


def test_role_without_values(qtbot, model):
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)
    role = QtCore.Qt.ItemDataRole.UserRole
    delegate = ComboItemDelegate(parent, ["x", "y", "z"], role=role)
    index = model.index(0, 0)
    editor = delegate.createEditor(
        parent, QtWidgets.QStyleOptionViewItem(), index)
    delegate.setEditorData(editor, index)
    assert editor.currentIndex() == 1
    editor.setCurrentIndex(0)
    delegate.setModelData(editor, model, index)
    assert index.data(role) == 0
