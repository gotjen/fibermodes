
from qtpy import QtCore, QtWidgets


class FiberSlider(QtWidgets.QFrame):

    valueChanged = QtCore.Signal(int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        label = QtWidgets.QLabel(self.tr("Fiber"))

        self.fiberInput = QtWidgets.QSpinBox()
        self.fiberInput.valueChanged.connect(self.changeValue)

        self.totLabel = QtWidgets.QLabel()

        self.slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.slider.valueChanged.connect(self.changeValue)

        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(label)
        hlayout.addWidget(self.fiberInput)
        hlayout.addWidget(self.totLabel)

        vlayout = QtWidgets.QVBoxLayout()
        vlayout.addLayout(hlayout)
        vlayout.addWidget(self.slider)

        self.setLayout(vlayout)

        self.setNum(0)

    def setNum(self, value):
        mv = 1 if value else 0
        self.totLabel.setText("/ {}".format(value))
        self.fiberInput.setRange(mv, value)
        self.slider.setRange(mv, value)

    def changeValue(self, value):
        if value != self.fiberInput.value():
            self.fiberInput.setValue(value)
        if value != self.slider.value():
            self.slider.setValue(value)
        self.valueChanged.emit(value)
