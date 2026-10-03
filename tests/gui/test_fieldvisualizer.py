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
    qtbot.addWidget(parent)
    win = FieldVisualizer(parent)
    qtbot.addWidget(win)
    win.options.np.setValue(50)
    return win


def test_start(viewer, qtbot):
    viewer.show()
    qtbot.waitExposed(viewer)
    assert viewer.windowTitle() == "Field Visualizer"
    assert viewer.dockWidgetArea(viewer.options) == \
        QtCore.Qt.DockWidgetArea.RightDockWidgetArea
    assert viewer.options.field.currentText() == "Emod"
    assert viewer.image.image.shape == (50, 50)


def test_toggle_options(viewer, qtbot):
    viewer.show()
    qtbot.waitExposed(viewer)
    assert viewer.options.isVisible()
    viewer.actions['options'].trigger()
    assert not viewer.actions['options'].isChecked()
    assert not viewer.options.isVisible()
    viewer.actions['options'].trigger()
    assert viewer.options.isVisible()


def test_closing_options_unchecks_action(viewer, qtbot):
    viewer.show()
    qtbot.waitExposed(viewer)
    with qtbot.waitSignal(viewer.options.hidden):
        viewer.options.close()
    assert not viewer.actions['options'].isChecked()


@pytest.mark.parametrize("fname", Field.FTYPES)
def test_field_types(viewer, fname):
    viewer.options.field.setCurrentText(fname)
    image = viewer.image.image
    assert image.shape == (50, 50)
    assert numpy.all(numpy.isfinite(image))


def test_radius_and_points(viewer):
    viewer.options.np.setValue(100)
    assert viewer.image.image.shape == (100, 100)
    viewer.options.radius.setValue(10)
    rect = viewer.image.mapRectToParent(viewer.image.boundingRect())
    assert rect.width() == pytest.approx(20e-6)


def test_set_modes(viewer):
    before = viewer.image.image.copy()
    viewer.setModes([[Mode("HE", 1, 1), 0, 0, 1],
                     [Mode("TE", 0, 1), 0, 0, 1]])
    assert not numpy.allclose(before, viewer.image.image)


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

    quiver.color.setColor((255, 0, 0))
    assert arrows[0].opts['brush'].color().red() == 255
    quiver.head.setValue(50)
    quiver.arrow.setValue(20)
    assert arrows[0].opts['headLen'] <= 20


def test_hide_hides_options(viewer, qtbot):
    viewer.show()
    qtbot.waitExposed(viewer)
    viewer.hide()
    assert not viewer.options.isVisible()


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
