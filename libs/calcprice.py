import os
from PyQt4.QtCore import *
import xml.etree.ElementTree as ET

class CalcPrice(QThread):
    finishSignal = pyqtSignal(list)

    def __init__(self,xml_path,parent=None):
        super(CalcPrice, self).__init__(parent)
        self.xml_path=xml_path

    def run(self):
        num_list = [0, 0, 0, 0, 0, 0]
        files = os.listdir(self.xml_path)
        for file in files:
            if not os.path.isdir(file):
                f = self.xml_path + "/" + file
                self.statisticsLabel(f, num_list)
        print('finish the work')
        self.finishSignal.emit(num_list)

    def statisticsLabel(self,xmlname, num_list):
        xmldoc = ET.parse(xmlname)
        root = xmldoc.getroot()
        # 计算不同类型各有多少个
        for type in root.iter('type'):
            if type.text.strip() == '0':
                num_list[0] += 1
            elif type.text.strip() == '1':
                num_list[1] += 1
            elif type.text.strip() == '2':
                num_list[2] += 1
            elif type.text.strip() == '3':
                num_list[3] += 1
            elif type.text.strip() == '4':
                num_list[4] += 1
            elif type.text.strip() == '5':
                num_list[5] += 1
        # 存在多少个3D框（3D框和2D框保存在一起，需要区别计算）
        for exist_3D in root.iter('exist_3D'):
            if exist_3D.text.strip() == '1':
                num_list[5] += 1

        for object in root.iter('object'):
            for obejct_ in object.iter('type'):
                if obejct_.text.strip() != '2':
                    continue
                for xmin in object.iter('xmin'):
                    xmins = xmin.text.strip().split(';')
                    num_list[1] += len(xmins)
        return num_list
