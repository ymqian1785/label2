from PyQt4.QtGui import *
from PyQt4.QtCore import *

from libs.lib import newIcon, labelValidator

BB = QDialogButtonBox


class LabelDialog(QDialog):

    def __init__(self, text="Enter object label", parent=None, listItem=None,listColor = None):
        super(LabelDialog, self).__init__(parent)
        self.edit = QLineEdit()
        self.edit.setText(text)
        self.edit.setValidator(labelValidator())
        self.edit.editingFinished.connect(self.postProcess)
        layout = QVBoxLayout()
        layout.addWidget(self.edit)
        self.buttonBox = bb = BB(BB.Ok | BB.Cancel, Qt.Horizontal, self)
        bb.button(BB.Ok).setIcon(newIcon('done'))
        bb.button(BB.Cancel).setIcon(newIcon('undo'))
        bb.accepted.connect(self.validate)
        bb.rejected.connect(self.reject)
        layout.addWidget(bb)
        self.item = listItem
        self.color = listColor

        if listItem is not None and len(listItem) > 0:
            self.listWidget = QListWidget(self)
            for item in listItem:
                self.listWidget.addItem(item)
            self.listWidget.itemDoubleClicked.connect(self.listItemClick)
            layout.addWidget(self.listWidget)

        self.setLayout(layout)

    def validate(self):
        try:
            if self.edit.text().trimmed():
                self.accept()
        except AttributeError:
            # PyQt5: AttributeError: 'str' object has no attribute 'trimmed'
            if self.edit.text().strip():
                self.accept()

    def postProcess(self):
        try:
            self.edit.setText(self.edit.text().trimmed())
        except AttributeError:
            # PyQt5: AttributeError: 'str' object has no attribute 'trimmed'
            self.edit.setText(self.edit.text())

    def popUp(self, text='', move=True):
        self.edit.setText(text)
        self.edit.setSelection(0, len(text))
        self.edit.setFocus(Qt.PopupFocusReason)
        if move:
            self.move(QCursor.pos())
        return self.edit.text() if self.exec_() else None

    def listItemClick(self, tQListWidgetItem):
        i = 0
        try:
            text = tQListWidgetItem.text().trimmed()
        except AttributeError:
            # PyQt5: AttributeError: 'str' object has no attribute 'trimmed'i
            text = tQListWidgetItem.text().strip()
        for k in self.item:
            if k == text:
                text += ";"
                (r, g, b, a) = self.color[i].getRgb()
                text+=('('+str(r)+','+str(g)+','+str(b)+','+str(a)+')')
                break
            i+=1
        self.edit.setText(text)
        self.validate()
