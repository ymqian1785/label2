from ctypes import *
from PyQt4.QtCore import QPoint
from new_function.default_path import *

default_dll_path = DefaultPath.lassoDllPath                # detectDllGPUPath

class EdgeFitting:
    isInit = False
    dllEnd = True
    photo_path = ''

    def __init__(self,dll_path=default_dll_path):
        self.lasso_dll = cdll.LoadLibrary(dll_path)
        self.lasso_dll.on_mouse.restype = c_char_p

    def initScissor(self,photo_path):
        if not os.path.exists(photo_path):
            photo_path = self.photo_path
        self.isInit = True
        self.lasso_dll.initPhoto(photo_path)

    def resetScissor(self):
        self.isInit = False


    def getEdge(self,event,x,y):
        self.dllEnd = False
        result = []
        if not self.isInit:
            self.initScissor()
        try:
            datas=self.lasso_dll.on_mouse(event,x,y)
            result = self.dataToPoints(datas)
        except Exception:
            print(Exception)
            print(x,y)
        self.dllEnd = True
        return result

    def dataToPoints(self,datas):
        datas = string_at(datas,len(datas)).decode()
        if datas=='': return []
        points=[]
        for data in datas.split('(')[1:]:
            point=data.split(',')
            points.append(QPoint(int(point[0]),int(point[1])))
        return points