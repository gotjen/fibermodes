from qtpy import QtWidgets
from datetime import datetime


class FiberPropertiesWindow(QtWidgets.QDialog):

    def __init__(self, fibers, parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self._fibers = fibers
        self.setWindowTitle(self.tr("Fiber Properties"))

        self.nameInput = QtWidgets.QLineEdit()
        self.authorInput = QtWidgets.QLineEdit()
        self.crdateLabel = QtWidgets.QLabel()
        self.tstampLabel = QtWidgets.QLabel()
        self.descriptionInput = QtWidgets.QPlainTextEdit()

        formLayout = QtWidgets.QFormLayout()
        formLayout.addRow(QtWidgets.QLabel(self.tr("Name")),
                          self.nameInput)
        formLayout.addRow(QtWidgets.QLabel(self.tr("Author")),
                          self.authorInput)
        formLayout.addRow(QtWidgets.QLabel(self.tr("Created")),
                          self.crdateLabel)
        formLayout.addRow(QtWidgets.QLabel(self.tr("Modified")),
                          self.tstampLabel)
        formLayout.addRow(QtWidgets.QLabel(self.tr("Description")),
                          self.descriptionInput)

        buttonBox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(formLayout)
        layout.addWidget(buttonBox)
        self.setLayout(layout)

    def exec(self):
        self.nameInput.setText(self._fibers["name"])
        self.authorInput.setText(self._fibers["author"])
        self.crdateLabel.setText(datetime.fromtimestamp(
            self._fibers["crdate"]).strftime('%Y-%m-%d %H:%M:%S'))
        self.tstampLabel.setText(datetime.fromtimestamp(
            self._fibers["tstamp"]).strftime('%Y-%m-%d %H:%M:%S'))
        self.descriptionInput.setPlainText(self._fibers["description"])
        return super().exec()

    def accept(self):
        if self._fibers["name"] != self.nameInput.text():
            self._fibers["name"] = self.nameInput.text()
            self.parent().setDirty(True)
        if self._fibers["author"] != self.authorInput.text():
            self._fibers["author"] = self.authorInput.text()
            self.parent().setDirty(True)
        if self._fibers["description"] != self.descriptionInput.toPlainText():
            self._fibers["description"] = self.descriptionInput.toPlainText()
            self.parent().setDirty(True)
        super().accept()
