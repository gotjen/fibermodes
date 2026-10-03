
from qtpy import QtCore, QtGui, QtWidgets
from fibermodes import FiberFactory
from fibermodes.fiber import material, geometry
from fibermodesgui import util, blockSignals
from fibermodesgui.widgets import AppWindow
from fibermodesgui.widgets import SLRCWidget
from .fiberproperties import FiberPropertiesWindow
from .infotable import FiberInfoTable
from .fiberplot import FiberPlot
import os
from tempfile import TemporaryFile
from shutil import copyfileobj


class FiberEditor(AppWindow):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.factory = FiberFactory()

        self.setWindowTitle(self.tr("Fiber Editor"))

        actions = {
            'new': (
                self.tr("&New"),
                'document-new',
                QtGui.QKeySequence.StandardKey.New,
                self.actionNew
            ),
            'open': (
                self.tr("&Open"),
                'document-open',
                QtGui.QKeySequence.StandardKey.Open,
                self.actionOpen
            ),
            'save': (
                self.tr("&Save"),
                'document-save',
                QtGui.QKeySequence.StandardKey.Save,
                self.save
            ),
            'saveas': (
                self.tr("Save &As..."),
                'document-save-as',
                QtGui.QKeySequence.StandardKey.SaveAs,
                self.actionSaveAs
            ),
            'quit': (
                self.tr("&Quit"),
                None,  # 'application-exit',
                QtGui.QKeySequence.StandardKey.Quit,
                self.close
            ),
            'info': (
                self.tr("&Fiber properties"),
                'document-properties',
                [QtGui.QKeySequence("Ctrl+I")],
                self.actionInfo
            ),
            'add': (
                self.tr("&Add layer"),
                'list-add',
                [QtGui.QKeySequence("Ctrl+Shift++")],
                self.actionAddLayer
            ),
            'remove': (
                self.tr("&Remove layer"),
                'list-remove',
                [QtGui.QKeySequence("Ctrl+-")],
                self.actionRemoveLayer
            ),
        }

        menus = [
            (
                self.tr("&File"), [
                    'new',
                    'open',
                    '-',
                    'save',
                    'saveas',
                    '-',
                    'quit'
                ]
            ),
            (
                self.tr("Fibe&r"), [
                    'info',
                    '-',
                    'add',
                    'remove'
                ]
            )
        ]

        toolbars = [
            ['new', 'open', 'save', 'info'],
            ['add', 'remove']
        ]

        self.initActions(actions)
        self.initMenubars(self.menuBar(), menus)
        self.initToolbars(toolbars)
        self._initLayout()
        self.setDirty(False)
        self.actionNew()

    def actionNew(self):
        if self._closeDocument():
            self.factory = FiberFactory()
            self.factory.addLayer(name="core", radius=4e-6, index=1.454)
            self.factory.addLayer(name="cladding", index=1.444)
            self.initLayerList()
            self.updateInfo()

    def actionOpen(self, filename=None):
        if not self._closeDocument():
            return

        if not filename:
            openDialog = QtWidgets.QFileDialog()
            openDialog.setWindowTitle(self.tr("Open fiber..."))
            openDialog.setDirectory(self._dir)
            openDialog.setAcceptMode(
                QtWidgets.QFileDialog.AcceptMode.AcceptOpen)
            openDialog.setNameFilter(self.tr("Fibers (*.fiber)"))
            if QtWidgets.QDialog.DialogCode(openDialog.exec()) == \
                    QtWidgets.QDialog.DialogCode.Accepted:
                filename = openDialog.selectedFiles()[0]
                self._dir = openDialog.directory()

        if filename:
            with open(filename, 'r') as f:
                self.factory.load(f)
            self._dir = os.path.dirname(filename)
            self.initLayerList()
            self.setDirty(False)
            self.setDocumentName(filename)
            self.statusBar().showMessage(self.tr("Fiber opened"), 5000)
            self.updateInfo()

    def save(self):
        if self.documentName() == "":
            self.actionSaveAs()
            return  # actionSaveAs will call save again

        # Use temporary file to prevent overwriting existing file in case
        # of error
        with TemporaryFile(mode="w+") as f:
            self.factory.dump(f)
            f.seek(0)
            with open(self.documentName(), 'w') as fd:
                copyfileobj(f, fd)

        # with open(self.documentName(), 'w') as f:
        #     self.factory.dump(f)
        self.setDirty(False)
        self.statusBar().showMessage(self.tr("Fiber saved"), 5000)
        super().save()

    def actionSaveAs(self):
        saveDialog = QtWidgets.QFileDialog()
        saveDialog.setWindowTitle(self.tr("Save fibers as..."))
        saveDialog.setDirectory(self._dir)
        saveDialog.setAcceptMode(QtWidgets.QFileDialog.AcceptMode.AcceptSave)
        saveDialog.setNameFilter(self.tr("Fibers (*.fiber)"))
        saveDialog.setDefaultSuffix('fiber')
        if QtWidgets.QDialog.DialogCode(saveDialog.exec()) == \
                QtWidgets.QDialog.DialogCode.Accepted:
            self.setDocumentName(saveDialog.selectedFiles()[0])
            self.save()
            self._dir = saveDialog.directory()

    def actionInfo(self):
        FiberPropertiesWindow(self.factory._fibers, self).exec()

    def actionAddLayer(self):
        self.addLayer()

    def actionRemoveLayer(self):
        self.removeLayer()

    def setDirty(self, df):
        super().setDirty(df)
        self.actions['save'].setEnabled(df)
        self.fnumInput.setRange(1, len(self.factory))
        self.fnumSlider.setRange(1, self.fnumInput.maximum())
        self.updateInfo()

    def _initLayout(self):
        self.layerName = QtWidgets.QLineEdit()
        self.layerName.textChanged.connect(self.changeLayerName)
        self.layerName.setEnabled(False)

        self.layerList = QtWidgets.QListWidget()
        self.layerList.itemSelectionChanged.connect(self.selectLayer)
        self.layerList.itemActivated.connect(self.actLayerName)
        self.initLayerList()

        layout1 = QtWidgets.QVBoxLayout()
        layout1.addWidget(QtWidgets.QLabel(self.tr("Fiber layers:")))
        layout1.addWidget(self.layerList)
        frame1 = QtWidgets.QFrame()
        frame1.setLayout(layout1)

        lnFormLayout = QtWidgets.QFormLayout()
        lnFormLayout.addRow(QtWidgets.QLabel(self.tr("Layer name:")),
                            self.layerName)

        l2splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)
        l2splitter.addWidget(self._initGeomFrame())
        l2splitter.addWidget(self._initMatFrame())
        layout2 = QtWidgets.QVBoxLayout()
        layout2.addLayout(lnFormLayout)
        layout2.addWidget(l2splitter)
        frame2 = QtWidgets.QFrame()
        frame2.setLayout(layout2)

        self.wlInput = QtWidgets.QDoubleSpinBox()
        self.wlInput.setSuffix(" nm")
        self.wlInput.setRange(500, 3000)
        self.wlInput.setSingleStep(1)
        self.wlInput.setValue(1550)
        self.wlInput.valueChanged.connect(self.wlChanged)
        self.fnumInput = QtWidgets.QSpinBox()
        self.fnumInput.setValue(1)
        self.fnumInput.setMinimum(1)
        self.fnumInput.setMaximum(len(self.factory))
        self.fnumInput.valueChanged.connect(self.fnumChanged)
        wlForm = QtWidgets.QFormLayout()
        wlForm.addRow(QtWidgets.QLabel(self.tr("Wavelength:")),
                      self.wlInput)
        wlForm.addRow(QtWidgets.QLabel(self.tr("Fiber #")),
                      self.fnumInput)
        self.fnumSlider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.fnumSlider.setValue(self.fnumInput.value())
        self.fnumSlider.setMinimum(1)
        self.fnumSlider.setMaximum(self.fnumInput.maximum())
        self.fnumSlider.valueChanged.connect(self.fnumChanged)
        self.infoTable = FiberInfoTable()
        self.fiberPlot = FiberPlot()
        infoTab = QtWidgets.QTabWidget()
        infoTab.addTab(self.infoTable, self.tr("Info"))
        infoTab.addTab(self.fiberPlot, self.tr("Graph"))
        layout3 = QtWidgets.QVBoxLayout()
        layout3.addLayout(wlForm)
        layout3.addWidget(self.fnumSlider)
        layout3.addWidget(infoTab)
        frame3 = QtWidgets.QFrame()
        frame3.setLayout(layout3)

        splitter = QtWidgets.QSplitter(self)
        splitter.addWidget(frame1)
        splitter.addWidget(frame2)
        splitter.addWidget(frame3)

        self.setCentralWidget(splitter)

    def _initGeomFrame(self):
        self.geomType = QtWidgets.QComboBox()
        self.geomType.addItems(geometry.__all__)
        self.geomType.setEnabled(False)
        self.geomType.setCurrentIndex(-1)
        self.geomType.currentIndexChanged.connect(self.selectGeomType)
        self.geomLayout = QtWidgets.QFormLayout()
        self.geomLayout.addRow(QtWidgets.QLabel(self.tr("Geometry type:")),
                               self.geomType)
        geomFrame = QtWidgets.QGroupBox(self.tr("Geometry"))
        geomFrame.setLayout(self.geomLayout)
        return geomFrame

    def _initMatFrame(self):
        self.matType = QtWidgets.QComboBox()
        self.matType.addItems(material.__all__)
        self.matType.setEnabled(False)
        self.matType.setCurrentIndex(-1)
        self.matType.currentIndexChanged.connect(self.selectMatType)
        self.matPropBut = QtWidgets.QPushButton(self.getIcon('info'), "")
        self.matPropBut.clicked.connect(self.aboutFiberMaterial)
        self.matPropBut.setEnabled(False)
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.matType)
        layout.addWidget(self.matPropBut)
        self.matLayout = QtWidgets.QFormLayout()
        self.matLayout.addRow(QtWidgets.QLabel(self.tr("Material type:")),
                              layout)
        matFrame = QtWidgets.QGroupBox(self.tr("Material"))
        matFrame.setLayout(self.matLayout)
        return matFrame

    def initLayerList(self):
        self.layerList.clear()
        for i, layer in enumerate(self.factory.layers, 1):
            if layer.name == "":
                name = "layer {}".format(i)
            else:
                name = layer.name
            self.layerList.addItem(name)

        self.actions['remove'].setEnabled(False)
        # No layer is selected: do not rename one through textChanged.
        with blockSignals(self.layerName):
            self.layerName.setText("")

    def selectLayer(self):
        index = self.layerList.currentRow()
        self.layerName.setEnabled(True)
        with blockSignals(self.layerName):
            self.layerName.setText(self.factory.layers[index].name)
        self.initGeom()
        self.initMat()
        if index == len(self.factory.layers) - 1:
            self.actions['remove'].setEnabled(False)
        else:
            self.actions['remove'].setEnabled(True)

    def addLayer(self):
        index = self.layerList.currentRow()
        self.factory.addLayer(index + 1)
        self.layerList.insertItem(index + 1, "layer {}".format(index+2))
        self._adjustLayerNames()
        self.layerList.setCurrentRow(index + 1)
        self.setDirty(True)

    def removeLayer(self):
        index = self.layerList.currentRow()
        self.layerList.takeItem(index)
        self.factory.removeLayer(index)
        self._adjustLayerNames()
        self.layerList.setCurrentRow(index)
        self.setDirty(True)

    def _adjustLayerNames(self):
        for i, layer in enumerate(self.factory.layers):
            if layer.name == "":
                name = "layer {}".format(i+1)
                if self.layerList.item(i):
                    self.layerList.item(i).setText(name)

    def changeLayerName(self, newText):
        index = self.layerList.currentRow()

        self.factory.layers[index].name = newText
        if newText == "":
            name = "layer {}".format(index+1)
        else:
            name = newText
        if self.layerList.currentItem():
            self.layerList.currentItem().setText(name)
        self.setDirty(True)

    def actLayerName(self, item):
        self.layerName.setFocus()

    def _updateParam(self, pname, pindex, value):
        layerIndex = self.layerList.currentRow()
        layer = self.factory.layers[layerIndex]
        layer[pname][pindex] = value
        self.setDirty(True)

    def initGeom(self):
        layerIndex = self.layerList.currentRow()
        if layerIndex == len(self.factory.layers) - 1:
            self.geomType.setEnabled(False)
        else:
            self.geomType.setEnabled(True)

        geomtype = self.factory.layers[layerIndex].type
        gtidx = self.geomType.findText(geomtype)
        # We call selectGeomType directly instead of emitting the signal,
        # to prevent it setting dirty state, since we only display the
        # current state, we are not changing the geometry type
        with blockSignals(self.geomType):
            self.geomType.setCurrentIndex(gtidx)
            self.selectGeomType(gtidx, False)

    def selectGeomType(self, index, change=True):
        util.clearLayout(self.geomLayout, 2)
        layerIndex = self.layerList.currentRow()
        self.factory.layers[layerIndex].type = self.geomType.currentText()
        if index == 0:
            self.setStepIndexGeom()
        elif index == 1:
            self.setSuperGaussianGeom()
        if change:
            self.setDirty(True)

    def setStepIndexGeom(self):
        layerIndex = self.layerList.currentRow()
        if layerIndex == len(self.factory.layers) - 1:
            return

        layer = self.factory.layers[layerIndex]
        self.radiusInput = SLRCWidget()
        self.radiusInput.setSuffix(" µm")
        self.radiusInput.setScaleFactor(1e6)
        self.radiusInput.codeParams = ['r', 'fp', 'mp']
        self.radiusInput.setValue(layer.radius)
        self.radiusInput.valueChanged.connect(self.updateRadius)

        self.geomLayout.addRow(QtWidgets.QLabel(self.tr("Radius:")),
                               self.radiusInput)

    def setSuperGaussianGeom(self):
        layerIndex = self.layerList.currentRow()
        layer = self.factory.layers[layerIndex]
        self.setStepIndexGeom()

        self.muInput = SLRCWidget()
        self.muInput.setSuffix(" µm")
        self.muInput.setScaleFactor(1e6)
        self.muInput.setRange(-100, 100)
        self.muInput.codeParams = ['r', 'fp', 'mp']
        self.muInput.setValue(layer.tparams[1])
        self.muInput.valueChanged.connect(
            lambda v: self._updateParam("tparams", 1, v))

        self.cInput = SLRCWidget()
        self.cInput.setRange(0.001, 100)
        self.cInput.codeParams = ['r', 'fp', 'mp']
        self.cInput.setScaleFactor(1e6)
        self.cInput.setValue(layer.tparams[2])
        self.cInput.valueChanged.connect(
            lambda v: self._updateParam("tparams", 2, v))

        self.mInput = SLRCWidget()
        self.mInput.setRange(1, 100)
        self.mInput.codeParams = ['r', 'fp', 'mp']
        self.mInput.setValue(layer.tparams[3])
        self.mInput.valueChanged.connect(
            lambda v: self._updateParam("tparams", 3, v))

        self.geomLayout.addRow(QtWidgets.QLabel(self.tr("Center (mu):")),
                               self.muInput)
        self.geomLayout.addRow(QtWidgets.QLabel(self.tr("Width (c):")),
                               self.cInput)
        self.geomLayout.addRow(QtWidgets.QLabel(self.tr("m parameter:")),
                               self.mInput)

    def updateRadius(self, value):
        self._updateParam("tparams", 0, value)

    def initMat(self):
        self.matType.setEnabled(True)
        self.matPropBut.setEnabled(True)
        layerIndex = self.layerList.currentRow()
        mattype = self.factory.layers[layerIndex].material
        mtidx = self.matType.findText(mattype)
        state = self.matType.blockSignals(True)
        self.matType.setCurrentIndex(mtidx)
        self.selectMatType(mtidx, False)
        self.matType.blockSignals(state)

    def selectMatType(self, index, change=True):
        layerIndex = self.layerList.currentRow()
        layer = self.factory.layers[layerIndex]
        layer.material = self.matType.currentText()
        util.clearLayout(self.matLayout, 2)
        mat = material.__dict__[layer.material]

        if mat.nparams == 0:
            pass  # No parameters to display

        elif issubclass(mat, material.Fixed):
            if change:
                layer.mparams = [1.444]
            self.setFixedMaterial(layer)

        elif issubclass(mat, material.compmaterial.CompMaterial):
            if change:
                layer.mparams = [0.05]
            self.setConcentrationMaterial(layer)

        if change:
            self.setDirty(True)

    def setFixedMaterial(self, layer):
        self.indexInput = SLRCWidget()
        self.indexInput.setRange(1, 2)
        self.indexInput.setSingleStep(0.01)
        self.indexInput.setValue(layer.mparams[0])
        self.indexInput.valueChanged.connect(self.updateIndex)
        self.indexInput.codeParams = ['r', 'fp', 'mp']

        self.matLayout.addRow(QtWidgets.QLabel(self.tr("Index:")),
                              self.indexInput)

    def updateIndex(self, value):
        self._updateParam("mparams", 0, value)

    def setConcentrationMaterial(self, layer):
        layerIndex = self.layerList.currentRow()
        layer = self.factory.layers[layerIndex]
        self.molInput = SLRCWidget()
        self.molInput.setSuffix(" %")
        self.molInput.setScaleFactor(100)
        self.molInput.setValue(layer.mparams[0])
        self.molInput.valueChanged.connect(self.updateMol)
        self.molInput.codeParams = ['r', 'fp', 'mp']

        self.matLayout.addRow(
            QtWidgets.QLabel(self.tr("Molar concentration:")),
            self.molInput)

    def updateMol(self, value):
        self._updateParam("mparams", 0, value)

    def updateInfo(self):
        if self.factory.layers:
            self.infoTable.updateInfo(
                self.factory[self.fnumInput.value()-1],
                self.wlInput.value() * 1e-9)
            self.fiberPlot.updateInfo(
                self.factory[self.fnumInput.value()-1],
                self.wlInput.value() * 1e-9)

    def fnumChanged(self, value):
        if self.fnumInput.value() != value:
            self.fnumInput.setValue(value)
        if self.fnumSlider.value() != value:
            self.fnumSlider.setValue(value)
        self.updateInfo()

    def wlChanged(self, value):
        self.updateInfo()

    def aboutFiberMaterial(self):
        layerIndex = self.layerList.currentRow()
        layer = self.factory.layers[layerIndex]
        mat = material.__dict__[layer.material]
        msgBox = QtWidgets.QMessageBox()
        msgBox.setWindowTitle(mat.name)
        text = "<h1>{}</h1>".format(mat.name)
        if mat.info:
            text += "<p>{}</p>".format(mat.info)
        if mat.url:
            text += '<p><a href="{url}">{url}</a></p>'.format(url=mat.url)
        msgBox.setText(text)
        msgBox.exec()
