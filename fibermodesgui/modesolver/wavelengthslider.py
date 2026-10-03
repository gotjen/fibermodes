
from qtpy import QtCore, QtWidgets


class WavelengthSlider(QtWidgets.QFrame):

    valueChanged = QtCore.Signal(int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        label = QtWidgets.QLabel(self.tr("Wavelength"))

        self.wavelengthInput = QtWidgets.QSpinBox()
        self.wavelengthInput.valueChanged.connect(self.changeValue)

        self.totLabel = QtWidgets.QLabel()

        self.slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.slider.valueChanged.connect(self.changeValue)

        self.wlLabel = QtWidgets.QLabel()
        self.vLabel = QtWidgets.QLabel()

        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(label)
        hlayout.addWidget(self.wavelengthInput)
        hlayout.addWidget(self.totLabel)

        h2layout = QtWidgets.QHBoxLayout()
        h2layout.addWidget(self.wlLabel)
        h2layout.addWidget(self.vLabel)

        vlayout = QtWidgets.QVBoxLayout()
        vlayout.addLayout(hlayout)
        vlayout.addWidget(self.slider)
        vlayout.addLayout(h2layout)

        self.setLayout(vlayout)

        self.setNum(0)

    def setNum(self, value):
        mv = 1 if value else 0
        self.totLabel.setText("/ {}".format(value))
        self.wavelengthInput.setRange(mv, value)
        self.slider.setRange(mv, value)

    def value(self):
        return self.wavelengthInput.value()

    def changeValue(self, value):
        if value != self.wavelengthInput.value():
            self.wavelengthInput.setValue(value)
        if value != self.slider.value():
            self.slider.setValue(value)
        self.valueChanged.emit(value)
