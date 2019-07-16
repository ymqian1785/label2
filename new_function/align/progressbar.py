# coding:utf-8
import sys
import threading
from PyQt4.QtCore import *
from PyQt4.QtGui import *

class ProgressBar(QDialog,threading.Thread):
    speed_of_progress_signa1 = pyqtSignal(int)
    data_cope_over_signal = pyqtSignal(bool)
    data_download_over_signal = pyqtSignal(bool)

    def __init__(self,parent = None):
        super(ProgressBar,self).__init__(parent=None)
        self.setGeometry(300,300,250,150)
        self.setWindowTitle('ProgressBar')
        self.pbar = QProgressBar()
        self.pbar.setGeometry(30, 40, 200, 25)      # x,y,w,h
        self.layout=QGridLayout()
        self.layout.addWidget(self.pbar,1,0,1,2)
        self.layout.setMargin(15)
        self.layout.setSpacing(10)

        self.setLayout(self.layout)
        self.step = 0
        self.speed_of_progress_signa1.connect(self.setValue)
        self.pbar.setValue(0)

    def setValue(self,value):
        self.pbar.setValue(value)

    def onCancel(self):
        self.close()