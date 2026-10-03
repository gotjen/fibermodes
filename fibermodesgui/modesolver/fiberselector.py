
from qtpy import QtCore, QtWidgets
import os
from datetime import datetime
from string import Template
from fibermodesgui.fibereditor.mainwindow import FiberEditor


class FiberSelector(QtWidgets.QFrame):

    fileLoaded = QtCore.Signal()
    fiberEdited = QtCore.Signal()

    def __init__(self, doc, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self._doc = doc
        self._editWin = None

        self.fiberName = QtWidgets.QLabel(self.tr("<i>Select fiber...</i>"))
        self.fiberName.setTextFormat(QtCore.Qt.TextFormat.RichText)

        self.chooseButton = QtWidgets.QPushButton(
            parent.getIcon('document-open'),
            self.tr("Choose"))
        self.chooseButton.clicked.connect(self.chooseFiber)

        self.editButton = QtWidgets.QPushButton(
            parent.getIcon('document-new'), self.tr("New"))
        self.editButton.clicked.connect(self.editFiber)

        self.propButton = QtWidgets.QPushButton(
            parent.getIcon('info'),
            "")
        self.propButton.setEnabled(False)
        self.propButton.clicked.connect(self.fiberProperties)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.fiberName)
        layout.addWidget(self.chooseButton)
        layout.addWidget(self.editButton)
        layout.addWidget(self.propButton)
        self.setLayout(layout)

        self.editIcon = parent.getIcon('pen')

    def updateFiberName(self):
        name = self._doc.factory.name
        if not name:
            name = os.path.basename(self._doc.filename)
        self.fiberName.setText(name)
        self.editButton.setText(self.tr("Edit"))
        self.editButton.setIcon(self.editIcon)
        self.propButton.setEnabled(True)

    def chooseFiber(self):
        dirname = (os.path.dirname(self._doc.filename)
                   if self._doc.filename
                   else os.getcwd())

        openDialog = QtWidgets.QFileDialog()
        openDialog.setWindowTitle(self.tr("Open fiber..."))
        openDialog.setDirectory(dirname)
        openDialog.setAcceptMode(QtWidgets.QFileDialog.AcceptMode.AcceptOpen)
        openDialog.setNameFilter(self.tr("Fibers (*.fiber)"))
        if QtWidgets.QDialog.DialogCode(openDialog.exec()) == \
                QtWidgets.QDialog.DialogCode.Accepted:
            self._doc.filename = openDialog.selectedFiles()[0]
            self.fileLoaded.emit()

    def editFiber(self):
        if self._editWin is None:
            self._editWin = FiberEditor(self)
            self._editWin.closed.connect(self.editorClosed)
            if self._doc.filename:
                self._editWin.actionOpen(self._doc.filename)
            # self._editWin.setWindowModality(QtCore.Qt.WindowModal)
            self._editWin.saved.connect(self.updateFiber)
        self._editWin.show()
        self._editWin.raise_()

    def updateFiber(self, filename):
        self._doc.filename = filename
        self.fiberEdited.emit()

    def fiberProperties(self):
        propTemplate = Template(self.tr("""<table>
<tr><th align="right">Filename: </th><td>$filename</td></tr>
<tr><th align="right">Name: </th><td>$name</td></tr>
<tr><th align="right">Author: </th><td>$author</td></tr>
<tr><th align="right">Creation date: </th><td>$crdate</td></tr>
<tr><th align="right">Modification date: </th><td>$tstamp</td></tr>
<tr><th align="right">Description: </th><td>$description</td></tr>
</table>
""")).substitute(filename=os.path.relpath(self._doc.filename),
                 name=self._doc.factory.name,
                 author=self._doc.factory.author,
                 crdate=datetime.fromtimestamp(
                    self._doc.factory.crdate).strftime('%Y-%m-%d %H:%M:%S'),
                 tstamp=datetime.fromtimestamp(
                    self._doc.factory.tstamp).strftime('%Y-%m-%d %H:%M:%S'),
                 description=self._doc.factory.description)

        msgBox = QtWidgets.QMessageBox()
        msgBox.setWindowTitle(self.tr("Fiber Properties"))
        msgBox.setText(propTemplate)
        msgBox.exec()

    def editorClosed(self):
        self._editWin = None
