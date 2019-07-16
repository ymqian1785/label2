#coding:utf-8
import os
from PyQt4.QtCore import Qt
from PyQt4.QtGui import *
from new_function.default_path import *
from new_function.shape_property import *

class DownloadDialog(QDialog):

    def __init__(self,parent = None):
        super(DownloadDialog,self).__init__(parent=None)
        self.initUi()

    def initUi(self):
        grid=QVBoxLayout()
        layout1=QHBoxLayout()
        layout2=QHBoxLayout()

        self.setLayout(grid)

        self.setGeometry(300,300,250,150)
        self.setWindowTitle('下载任务窗口')
        self.taskLabel=QLabel('任务ID')
        self.taskText=QLineEdit()
        self.buttonBox = bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        bb.accepted.connect(self.validate)
        bb.rejected.connect(self.reject)

        layout1.addWidget(self.taskLabel)
        layout1.addWidget(self.taskText)
        layout2.addWidget(self.buttonBox)
        grid.addLayout(layout1)
        grid.addLayout(layout2)

        self.move(300,150)

    def validate(self):
        try:
            if self.taskText.text().trimmed():
                self.accept()
        except AttributeError:
            # PyQt5: AttributeError: 'str' object has no attribute 'trimmed'
            if self.taskText.text().strip():
                self.accept()

    def setValue(self,value):
        self.pbar.setValue(value)

    def popUp(self,text='',move=True):
        self.taskText.setText(text)
        self.taskText.setSelection(0,len(text))
        self.taskText.setFocus(Qt.PopupFocusReason)
        if move:
            self.move(QCursor.pos())
        text = self.taskText.text() if self.exec_() else ''
        return self.copeText(text.strip('\n'))

    def copeText(self,text):
        task_type = DownloadType['none']
        file_name = None
        file_remote = None
        file_local = None
        text_split=text.split(':')
        if len(text_split)==2:
            file_name=text.split(':')[1]+'.zip'
            file_remote=os.path.join(DefaultPath.ftpDataPath,text_split[0])
            file_local=os.path.join(DefaultPath.root_path,file_remote)

            task_name_split=text_split[1].split('-')
            if task_name_split[-1]=='rework':
                task_type = DownloadType['rework']
            else:
                task_type = DownloadType['task']

        return file_name,file_remote,file_local,task_type