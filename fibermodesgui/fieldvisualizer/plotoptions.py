from qtpy import QtCore, QtWidgets
from fibermodes.field import Field
from .colormapwidget import ColorMapWidget
from .quiverwidget import QuiverWidget


class PlotOptions(QtWidgets.QDockWidget):

    hidden = QtCore.Signal()

    def __init__(self, pwin, parent=None, f=QtCore.Qt.WindowType.Widget):
        super().__init__(parent, f)
        self.win = pwin
        self.setWindowTitle(self.tr("Plot Options"))

        frame = QtWidgets.QFrame()
        layout = QtWidgets.QVBoxLayout()
        frame.setLayout(layout)

        self.field = QtWidgets.QComboBox()
        self.field.addItems(Field.FTYPES)
        self.field.setCurrentIndex(Field.FTYPES.index('Emod'))
        layout.addWidget(self.field)

        flayout = QtWidgets.QFormLayout()

        nplabel = QtWidgets.QLabel(self.tr("Number of points"))
        self.np = QtWidgets.QSpinBox()
        self.np.setRange(50, 5000)
        self.np.setValue(200)
        self.np.setSingleStep(50)
        nplabel.setBuddy(self.np)
        flayout.addRow(nplabel, self.np)

        rlabel = QtWidgets.QLabel(self.tr("Radius"))
        self.radius = QtWidgets.QDoubleSpinBox()
        self.radius.setRange(0.001, 1000)
        self.radius.setValue(pwin.fiber.innerRadius(-1) * 1.5e6)
        self.radius.setSuffix(" µm")
        self.radius.setSingleStep(0.1)
        rlabel.setBuddy(self.radius)
        flayout.addRow(rlabel, self.radius)

        layout.addLayout(flayout)

        self.plotLayers = QtWidgets.QPushButton(
            self.tr("Display fiber layers"))
        self.plotLayers.setCheckable(True)
        layout.addWidget(self.plotLayers)

        self.cm = ColorMapWidget()
        layout.addWidget(self.cm)

        self.quiver = QuiverWidget(pwin)
        layout.addWidget(self.quiver)

        layout.addStretch(1)

        self.setWidget(frame)

    def hideEvent(self, event):
        self.hidden.emit()
        return super().hideEvent(event)
