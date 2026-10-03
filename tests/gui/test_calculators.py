"""Tests for the wavelength and material calculators."""

import pytest
from qtpy import QtCore

from fibermodes import Wavelength
from fibermodes.fiber import material
from fibermodesgui.materialcalculator import MaterialCalculator
from fibermodesgui.wavelengthcalculator import WavelengthCalculator


@pytest.fixture
def wlcalc(qtbot):
    w = WavelengthCalculator()
    qtbot.addWidget(w)
    return w


@pytest.fixture
def matcalc(qtbot):
    w = MaterialCalculator()
    qtbot.addWidget(w)
    return w


def test_wavelength_initial(wlcalc):
    wl = Wavelength(1550e-9)
    assert wlcalc.linput.value() == pytest.approx(1550)
    assert wlcalc.kinput.value() == pytest.approx(wl.k0, abs=1e-3)
    assert wlcalc.winput.value() == pytest.approx(wl.omega * 1e-12, abs=1e-3)
    assert wlcalc.finput.value() == pytest.approx(wl.frequency * 1e-12,
                                                  abs=1e-3)
    assert wlcalc.band.text() == "C band"
    assert wlcalc.band.alignment() & QtCore.Qt.AlignmentFlag.AlignCenter


@pytest.mark.parametrize("nm, band", [
    (1000, ""), (1310, "O band"), (1400, "E band"), (1500, "S band"),
    (1550, "C band"), (1600, "L band"), (1650, "U band"), (1700, ""),
])
def test_wavelength_band(wlcalc, nm, band):
    wlcalc.linput.setValue(nm)
    assert wlcalc.band.text() == band


@pytest.mark.parametrize("box, attr, scale", [
    ("kinput", "k0", 1),
    ("winput", "omega", 1e-12),
    ("finput", "frequency", 1e-12),
])
def test_wavelength_inputs(wlcalc, box, attr, scale):
    wl = Wavelength(1310e-9)
    getattr(wlcalc, box).setValue(getattr(wl, attr) * scale)
    assert wlcalc.linput.value() == pytest.approx(1310, abs=1e-2)


def test_material_list(matcalc):
    names = [matcalc.matinput.itemText(i)
             for i in range(matcalc.matinput.count())]
    assert "Fixed" not in names
    assert "Silica" in names


def test_material_select_all(matcalc):
    for i in range(matcalc.matinput.count()):
        matcalc.matinput.setCurrentIndex(i)
        mat = material.__dict__[matcalc.matinput.currentText()]
        assert matcalc.material is mat
        assert matcalc.cinput.isEnabled() == matcalc.iscomp
        assert mat.name in matcalc.infotext.toPlainText()


def test_material_index(matcalc):
    matcalc.matinput.setCurrentText("Silica")
    n = material.Silica.n(Wavelength(1550e-9))
    assert matcalc.iinput.value() == pytest.approx(n, abs=1e-6)
    matcalc.winput.setValue(1310)
    n = material.Silica.n(Wavelength(1310e-9))
    assert matcalc.iinput.value() == pytest.approx(n, abs=1e-6)


def test_material_concentration(matcalc):
    matcalc.matinput.setCurrentText("SiO2GeO2")
    assert matcalc.cinput.isEnabled()
    n0 = matcalc.iinput.value()
    matcalc.cinput.setValue(5)
    assert matcalc.iinput.value() > n0
