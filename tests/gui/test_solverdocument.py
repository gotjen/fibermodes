"""Tests for fibermodesgui.modesolver.solverdocument.SolverDocument."""

import csv

import pytest
from qtpy import QtWidgets

from fibermodes import HE11, Simulator, PSimulator
from fibermodesgui.modesolver.solverdocument import SolverDocument

from .conftest import SMF28


@pytest.fixture
def doc(qtbot):
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)
    d = SolverDocument(parent)
    yield d
    d.stop_thread()


def _prepare(doc):
    doc.filename = SMF28
    doc.wavelengths = [1310e-9, 1550e-9]
    doc.params = ["neff", "cutoff (V)"]


def test_not_ready_does_not_start(doc):
    _prepare(doc)
    assert doc.initialized
    assert not doc.isRunning()
    assert doc.modes == []


@pytest.mark.parametrize("numprocs, cls", [(0, PSimulator), (1, Simulator)])
def test_compute(doc, qtbot, numprocs, cls):
    """The computation runs in the QThread, with the sequential simulator
    and with the multiprocessing one."""
    doc.numProcs = numprocs if numprocs else 2
    assert isinstance(doc.simulator, cls)
    _prepare(doc)
    doc.ready = True

    available = []
    doc.valueAvailable.connect(lambda *args: available.append(args))
    with qtbot.waitSignals([doc.computeStarted, doc.computeFinished],
                           order="strict", timeout=120000):
        doc.start()
    doc.wait()

    assert len(doc.modes) == 1             # one fiber
    assert len(doc.modes[0]) == 2          # two wavelengths
    assert HE11 in doc.modes[0][1]
    assert doc.toCompute == 0
    assert len(available) == len(doc.values)
    neff = doc.values[(0, 1, HE11, 0)]
    assert 1.4444 < neff < 1.4489


def test_mode_kind(doc):
    for kind in ("scalar", "both", "vector"):
        doc.modeKind = kind
        assert doc.modeKind == kind


def test_numax_mmax(doc):
    doc.numax = -1
    assert doc.numax is None
    doc.numax = 2
    assert doc.numax == 2
    doc.mmax = 0
    assert doc.mmax is None
    doc.mmax = 3
    assert doc.mmax == 3


def test_export(doc, qtbot, tmp_path):
    doc.numProcs = 1
    _prepare(doc)
    doc.ready = True
    with qtbot.waitSignal(doc.computeFinished, timeout=120000):
        doc.start()
    doc.wait()

    target = tmp_path / "out.csv"
    doc.export(str(target), 1, 0)
    with open(target, newline='') as f:
        rows = list(csv.reader(f))
    assert rows[0] == ["Mode", "neff", "cutoff (V)"]
    assert rows[1][0] == str(doc.modes[0][1][0])
    assert len(rows) == len(doc.modes[0][1]) + 1


def test_clear_caches(doc, qtbot):
    doc.numProcs = 1
    _prepare(doc)
    doc.ready = True
    with qtbot.waitSignal(doc.computeFinished, timeout=120000):
        doc.start()
    doc.wait()
    doc.clear_all_caches()
    assert doc.values == {}
    assert doc.modes == []
