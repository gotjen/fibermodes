"""Tests for fibermodesgui.widgets.appwindow.AppWindow."""

import logging

import pytest
from qtpy import QtGui, QtWidgets

from fibermodesgui.widgets import AppWindow


@pytest.fixture
def win(qtbot):
    w = AppWindow()
    # qtbot closes the window at teardown; a dirty window would ask to save.
    qtbot.addWidget(w, before_close_func=lambda w: w.setDirty(False))
    return w


@pytest.fixture
def no_icon_theme():
    """Use an icon theme that does not exist, to test the fallback."""
    name = QtGui.QIcon.themeName()
    QtGui.QIcon.setThemeName("fibermodes-no-such-theme")
    yield
    QtGui.QIcon.setThemeName(name)


def test_default_actions(win):
    assert isinstance(win.actions['loglevel'], QtGui.QActionGroup)
    assert win.actions['lognotset'].isChecked()
    assert win.actions['capturewarnings'].isCheckable()


def test_log_level_action(win):
    level = logging.root.level
    try:
        win.actions['logerror'].trigger()
        assert logging.root.level == logging.ERROR
        assert win.actions['logerror'].isChecked()
        assert not win.actions['lognotset'].isChecked()
    finally:
        logging.root.setLevel(level)


def test_init_actions(win):
    triggered = []
    win.initActions({
        'plain': ("Plain", None, [], lambda: triggered.append('plain')),
        'withicon': (
            "With icon",
            'document-new',
            QtGui.QKeySequence.keyBindings(
                QtGui.QKeySequence.StandardKey.New),
            None,
        ),
        'group': {
            'g1': ("G1", None, [], None),
            'g2': ("G2", None, [], None),
        },
    })
    assert isinstance(win.actions['plain'], QtGui.QAction)
    win.actions['plain'].trigger()
    assert triggered == ['plain']
    assert not win.actions['withicon'].icon().isNull()
    assert win.actions['withicon'].shortcuts()
    assert win.actions['g1'].actionGroup() is win.actions['group']
    assert win.actions['g2'].isCheckable()


def test_menus_and_toolbars(win):
    win.initMenubars(win.menuBar(), [
        ("&File", ['lognotset', '-', ("Sub", ['logdebug'])]),
    ])
    win.initToolbars([['logdebug', '-', 'loginfo']])
    menus = [a.text() for a in win.menuBar().actions()]
    assert menus == ["&File"]
    assert win.findChildren(QtWidgets.QToolBar)


@pytest.mark.parametrize("name", ["document-new", "pen"])
def test_get_icon_fallback(win, no_icon_theme, name):
    """Icons are found in the 'actions' (document-new) and in the
    'emblems' (pen) folders."""
    icon = win.getIcon(name)
    assert not icon.isNull()
    sizes = {s.width() for s in icon.availableSizes()}
    assert {16, 22, 32} <= sizes


def test_get_icon_unknown(win, no_icon_theme):
    assert win.getIcon("fibermodes-no-such-icon").isNull()


def test_document_name_and_dirty(win, qtbot):
    win.setDocumentName("doc.fiber")
    assert win.documentName() == "doc.fiber"
    assert not win.dirty()
    win.setDirty()
    assert win.dirty()
    with qtbot.waitSignal(win.saved) as blocker:
        win.save()
    assert blocker.args == ["doc.fiber"]


def _patch_exec(monkeypatch, button):
    calls = []

    def fake_exec(self):
        calls.append(self)
        return button.value

    monkeypatch.setattr(QtWidgets.QMessageBox, "exec", fake_exec)
    return calls


def test_close_clean_document(win, monkeypatch):
    calls = _patch_exec(monkeypatch,
                        QtWidgets.QMessageBox.StandardButton.Cancel)
    assert win._closeDocument()
    assert calls == []


@pytest.mark.parametrize("button, result, saved", [
    (QtWidgets.QMessageBox.StandardButton.Save, True, True),
    (QtWidgets.QMessageBox.StandardButton.Discard, True, False),
    (QtWidgets.QMessageBox.StandardButton.Cancel, False, False),
])
def test_close_dirty_document(win, monkeypatch, button, result, saved):
    calls = _patch_exec(monkeypatch, button)
    emitted = []
    win.saved.connect(emitted.append)
    win.setDirty()
    assert win._closeDocument() is result
    assert len(calls) == 1
    assert bool(emitted) is saved


def test_close_event(win, qtbot, monkeypatch):
    _patch_exec(monkeypatch, QtWidgets.QMessageBox.StandardButton.Cancel)
    win.show()
    win.setDirty()
    assert not win.close()
    assert win.isVisible()
    win.setDirty(False)
    with qtbot.waitSignal(win.closed):
        assert win.close()
