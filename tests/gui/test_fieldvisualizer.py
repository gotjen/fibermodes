"""Tests for the field visualizer (fibermodesgui.fieldvisualizer)."""

import os.path
from types import SimpleNamespace

import numpy
import pytest
from qtpy import QtCore, QtWidgets

from fibermodes import FiberFactory, Mode
from fibermodes.field import Field
from fibermodesgui.fieldvisualizer import FieldVisualizer
from fibermodesgui.fieldvisualizer.colormapwidget import ColorMapWidget

SMF28 = os.path.normpath(os.path.join(
    os.path.dirname(__file__), os.pardir, "fiber", "smf28.fiber"))


class FakeModeSolver(QtWidgets.QMainWindow):

    """The attributes of ModeSolver that FieldVisualizer reads."""

    def __init__(self):
        super().__init__()
        factory = FiberFactory()
        with open(SMF28) as f:
            factory.load(f)
        simulator = SimpleNamespace(fibers=[factory[0]],
                                    wavelengths=[1550e-9])
        self.doc = SimpleNamespace(simulator=simulator)
        self.fiberSlider = SimpleNamespace(
            fiberInput=SimpleNamespace(value=lambda: 1))
        self.wavelengthSlider = SimpleNamespace(
            wavelengthInput=SimpleNamespace(value=lambda: 1))


@pytest.fixture
def viewer(qtbot):
    parent = FakeModeSolver()
    win = FieldVisualizer(parent)
    # Register only the child: deleting the parent would also delete it.
    qtbot.addWidget(win)
    win.options.np.setValue(50)
    yield win
    del parent  # keep the parent (and so its child) alive until teardown


def test_start(viewer, qtbot):
    viewer.show()
    qtbot.waitExposed(viewer)
    assert viewer.windowTitle() == "Field Visualizer"
    assert viewer.dockWidgetArea(viewer.options) == \
        QtCore.Qt.DockWidgetArea.RightDockWidgetArea
    assert viewer.options.field.currentText() == "Emod"
    assert viewer.image.image.shape == (50, 50)


def test_options_dock(viewer, qtbot):
    """The F4 action toggles the dock, and closing the dock unchecks it."""
    viewer.show()
    qtbot.waitExposed(viewer)
    assert viewer.options.isVisible()
    viewer.actions['options'].trigger()
    assert not viewer.actions['options'].isChecked()
    assert not viewer.options.isVisible()
    viewer.actions['options'].trigger()
    assert viewer.options.isVisible()

    with qtbot.waitSignal(viewer.options.hidden):
        viewer.options.close()
    assert not viewer.actions['options'].isChecked()

    viewer.actions['options'].trigger()
    viewer.hide()  # hiding the window hides the dock
    assert not viewer.options.isVisible()


def test_field_type(viewer):
    """The combo box selects the field component."""
    emod = viewer.image.image.copy()
    viewer.options.field.setCurrentText("Ez")
    image = viewer.image.image
    assert image.shape == (50, 50)
    assert numpy.all(numpy.isfinite(image))
    assert not numpy.allclose(image, emod)


@pytest.mark.stress
@pytest.mark.parametrize("fname", Field.FTYPES)
def test_all_field_types_finite(viewer, fname):
    """Edge case: polar components can give NaN on the r = 0 axis.
    tests/test_field.py computes some components without checking them."""
    viewer.options.field.setCurrentText(fname)
    assert numpy.all(numpy.isfinite(viewer.image.image))


def test_radius_and_points(viewer):
    viewer.options.np.setValue(100)
    assert viewer.image.image.shape == (100, 100)
    viewer.options.radius.setValue(10)
    rect = viewer.image.mapRectToParent(viewer.image.boundingRect())
    assert rect.width() == pytest.approx(20e-6)


def test_set_modes(viewer):
    before = viewer.image.image.copy()
    viewer.setModes([[Mode("HE", 1, 1), 0, 0, 2]])
    assert numpy.allclose(viewer.image.image, 2 * before)


def test_plot_layers(viewer):
    viewer.options.plotLayers.setChecked(True)
    layers = viewer._FieldVisualizer__layers
    assert layers is not None
    assert layers.isVisible()
    assert layers.pen().style() == QtCore.Qt.PenStyle.DotLine
    viewer.options.plotLayers.setChecked(False)
    assert not layers.isVisible()


def test_colormap_changes_lookup_table(viewer):
    viewer.options.cm.cm.item.loadPreset('parula')
    lut = viewer.image.lut
    assert lut is not None
    expected = viewer.options.cm.getLookupTable(100)
    assert numpy.array_equal(lut, expected)


def test_quiver(viewer, qtbot):
    quiver = viewer.options.quiver
    arrows = quiver._QuiverWidget__quiver
    assert arrows
    assert not any(a.isVisible() for a in arrows)
    quiver.setChecked(True)
    assert all(a.isVisible() for a in arrows)

    quiver.grid.setValue(5)
    arrows = quiver._QuiverWidget__quiver
    assert len(arrows) == 25
    assert all(a.isVisible() for a in arrows)

    # The color dialog emits sigColorChanging while the user picks.
    quiver.color.setColor((255, 0, 0), finished=False)
    assert arrows[0].opts['brush'].color().red() == 255
    quiver.head.setValue(50)
    quiver.arrow.setValue(20)
    assert arrows[0].opts['headLen'] <= 20


def test_colormap_presets(qtbot):
    from pyqtgraph.graphicsItems.GradientEditorItem import Gradients
    for name in ('parula', 'viridis', 'inferno', 'plasma', 'magma'):
        assert name in Gradients
    w = ColorMapWidget()
    qtbot.addWidget(w)
    with qtbot.waitSignal(w.sigGradientChanged):
        w.cm.item.loadPreset('parula')
    lut = w.getLookupTable(10)
    assert lut.shape[0] == 10


def test_range_change_prints_nothing(viewer, capsys):
    viewer.graph.setRange(xRange=(-1e-5, 1e-5), yRange=(-1e-5, 1e-5))
    assert capsys.readouterr().out == ""
