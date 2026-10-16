from qtpy import QtCore, QtWidgets
from pyqtgraph import GradientWidget
from pyqtgraph.graphicsItems.GradientEditorItem import Gradients
from .parula import cm_data as _parula_data
import numpy


def frgb(rgb):
    return (int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255), 255)


def addCM(name, data):
    np = len(data)
    cp = numpy.linspace(0, 1, np)
    ticks = [(c, frgb(rgb)) for (c, rgb) in zip(cp, data)]
    # TODO: remove unneeded points (if possible...)
    Gradients[name] = {
        'ticks': ticks,
        'mode': 'rgb'
    }


# pyqtgraph already includes viridis, inferno, plasma and magma.
addCM('parula', _parula_data)


class ColorMapWidget(QtWidgets.QGroupBox):

    sigGradientChanged = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(self.tr("Color Map"))
        layout = QtWidgets.QVBoxLayout()

        # TODO: load / save other presets...

        # self._gradients = GradientEditorItem.Gradients
        #
        # self.preset = QtWidgets.QComboBox()
        # self.preset.addItems(list(self._gradients.keys()))
        # self.preset.insertSeparator(len(self._gradients))
        # self.preset.addItem(self.tr('Load ColorMap...'))
        # self.preset.addItem(self.tr('Save ColorMap...'))
        # self.preset.currentIndexChanged.connect(self._loadPreset)
        # layout.addWidget(self.preset)

        self.cm = GradientWidget()
        self.cm.item.loadPreset('inferno')
        self.cm.sigGradientChanged.connect(self.__emitGradientChanged)
        layout.addWidget(self.cm)

        self.setLayout(layout)

    def __emitGradientChanged(self):
        self.sigGradientChanged.emit()

    def getLookupTable(self, np):
        return self.cm.getLookupTable(np)

    # def _loadPreset(self, index):
    #     ni = self.preset.count()
    #     if index == ni-1:  # Save...
    #         return
    #     elif index == ni-2:  # Load...
    #         return
    #     else:
    #         name = self.preset.itemText(index)
    #         st = self._gradients[name]

    #     self.cm.item.restoreState(st)
