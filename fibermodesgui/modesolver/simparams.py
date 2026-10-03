from qtpy import QtGui, QtWidgets


class SimParamsDialog(QtWidgets.QDialog):

    def __init__(self, doc, parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.numProcs = QtWidgets.QSpinBox()
        self.numProcs.setRange(0, 16)
        self.numProcs.setValue(doc.numProcs)
        self.numProcs.setSpecialValueText("auto")
        self.numProcs.setWhatsThis(self.tr(
            "Set the number of processes used for computing. If 'auto', use "
            "all processors. If '1', use the sequential version of the "
            "simulator.\n\n"
            "Be aware than assigning more processes than the number of "
            "processors could decrease performance."))

        deltaValidator = QtGui.QDoubleValidator(1e-31, 1, 1000)
        self.delta = QtWidgets.QLineEdit()
        self.delta.setValidator(deltaValidator)
        self.delta.setText("{:e}".format(doc.simulator.delta))
        self.delta.setWhatsThis(self.tr(
            "Step size used when solving for modes. Smaller number means "
            "increased computation time, while bigger number means more "
            "chances of skipping solutions."))

        flayout = QtWidgets.QFormLayout()
        flayout.addRow(QtWidgets.QLabel(self.tr("Number of processes")),
                       self.numProcs)
        flayout.addRow(QtWidgets.QLabel(self.tr("Delta parameter")),
                       self.delta)

        buttonBox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Close |
            QtWidgets.QDialogButtonBox.StandardButton.Help)
        buttonBox.rejected.connect(self.close)
        buttonBox.helpRequested.connect(
            QtWidgets.QWhatsThis.enterWhatsThisMode)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(flayout)
        layout.addWidget(buttonBox)

        self.setLayout(layout)
