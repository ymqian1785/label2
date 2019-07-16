#coding:utf-8
'''画布类，中间的画布配置，type={rect,point,line}'''

# from PyQt4.QtGui import *
#from PyQt4.QtOpenGL import *
from PyQt4.QtCore import *
import numpy as np
import math
# from scipy import optimize

from libs.shape import Shape
from libs.lib import distance
from new_function.shape_property import *
from new_function.edge_fitting.edge_fitting import *
from new_function.road_segment.road_segment import *
from new_function.manual_tag.share_point import *

CURSOR_DEFAULT = Qt.ArrowCursor         # 鼠标：箭头形状
CURSOR_POINT = Qt.PointingHandCursor    # 鼠标：手指形状
CURSOR_DRAW = Qt.CrossCursor            # 鼠标：十字形状
CURSOR_MOVE = Qt.ClosedHandCursor       # 鼠标：拳头形状
CURSOR_GRAB = Qt.OpenHandCursor         # 鼠标：小手形状

# class Canvas(QGLWidget):


class Canvas(QWidget):
    zoomRequest = pyqtSignal(int)
    scrollRequest = pyqtSignal(int, int, QPointF)
    newShape = pyqtSignal()
    selectionChanged = pyqtSignal(bool)
    shapeMoved = pyqtSignal()
    drawingPolygon = pyqtSignal(bool)
    blockMode = pyqtSignal(int)

    CREATE, EDIT, CORRECT = list(range(3))

    epsilon = 3.0

    # 画布初始化
    def __init__(self, *args, **kwargs):
        super(Canvas, self).__init__()
        # Initialise local state.
        self.type  = 0                                  # 画布上的图形类型
        self.lineflag = 0
        self.mode = self.EDIT                           # 画布的编辑模式
        self.shapes = []
        self.current = None                             # 当前图形
        self.tmpCuboid=None                             # 当前长方体
        self.point = None
        self.lines = Shape()
        self.selectedShape = None                       # 保存被选中的图形save the selected shape here
        self.selectedShapeCopy = None
        self.drawingLineColor = QColor(0, 0, 255)       # 线和矩形的颜色
        self.drawingRectColor = QColor(0, 0, 255) 
        self.line = Shape(line_color=self.drawingLineColor)
        self.blockPrevPoint = QPoint()                  # 初始化前一个点
        self.prevPoint = QPointF()                      # 初始化前一个点
        self.offsets = QPointF(), QPointF()             # 偏置？
        self.scale = 1.0                                # 间隔
        self.pixmap = QPixmap()
        self.visible = {}
        self._hideBackround = False
        self.hideBackround = False
        self.hShape = None                              # 顶点所属的图形   **
        self.hVertex = None                             # 鼠标选中的顶点   **
        self.hEdge = None                               # 鼠标选中的边
        self.hShape_backup = None                       # hShape备份 这两个值总是被重置，导致我想用时找不到它们
        self.hVertex_backup = None                      # hVertex备份
        self._painter = QPainter()
        self._cursor = CURSOR_DEFAULT                   # 光标形状(鼠标焦点)
        # Menus:
        self.menus = (QMenu(), QMenu())                 # 两个菜单栏
        # Set widget options.
        self.setMouseTracking(True)                     # 跟踪鼠标
        self.setFocusPolicy(Qt.WheelFocus)              # 滚轮对于画布的事件
        self.verified = False
        self.trafficSign = False                        # 当前图片是否有交通标志
        self.hopeline = False
        self.moveFlag = False                           # 是否移动
        self.switchMode = BlockMode['block']            # 点集与点混用
        self.scissor=EdgeFitting()                      # 智能剪刀
        self.block_begin = False                        # 开始标注
        self.line_begin = False                         # block中画线标注
        self.del_block = False                          # 用矩形框删除block块
        self.blockline_begin = False                    # 开始block的line标注
        self.correct_points=[]                          # block中正确的点集
        self.select_points=[]                           # block中单击的点集（）
        self.lanelineShape = None                       # 点
        self.isBlockPressMouse = False                  # 是否按下鼠标
        self.isLanelineLabel = False                    # 是否是车道线标注

    # 设置画线的颜色
    def setDrawingColor(self, qColor):
        self.drawingLineColor = qColor
        self.drawingRectColor = qColor

    # 回车事件(覆盖光标)
    def enterEvent(self, ev):
        self.overrideCursor(self._cursor)

    # 离开事件(重置光标)
    def leaveEvent(self, ev):
        self.restoreCursor()

    # 焦点离开事件
    def focusOutEvent(self, ev):
        self.restoreCursor()

    def isVisible(self, shape):
        return self.visible.get(shape, True)

    # 设置为画框模式
    def drawing(self):
        return self.mode == self.CREATE or self.mode == self.CORRECT

    # 设置为编辑属性模式
    def editing(self):
        return self.mode == self.EDIT

    # 设置为编辑模式
    def setEditing(self, value=True):
        self.mode = self.EDIT if value else self.CREATE
        if not value:  # Create
            self.unHighlight()
            self.deSelectShape()
        self.prevPoint = QPointF()
        # self.repaint()

    def setCorrecting(self,value=True):
        self.mode = self.EDIT if value else self.CORRECT
        self.unHighlight()
        self.deSelectShape()
        self.prevPoint = QPointF()

    # 设置类型0,1,2
    def settype(self,value= 0):
        self.type = value

    def unHighlight(self):
        if self.hShape:
            self.hShape.highlightClear()
        self.hVertex = self.hShape = None

    # 顶点选择(判断是否存在顶点)
    def selectedVertex(self):
        return self.hVertex is not None

    # 鼠标移动事件
    def mouseMoveEvent(self, ev):
        """用最后一个点和当前坐标更新直线."""
        pos = self.transformPos(ev.pos())
        pos = self.formatPoint(pos)

        if self.isBlockPressMouse: return
        # if self.drawing() and self.type == ShapeType['block'].value and self.block_begin:    # 画区域块
        #     if self.switchMode==BlockMode['block'] and self.scissor.dllEnd:
        #         lasso_points=self.scissor.getEdge(0,pos.x(),pos.y())
        #         self.lines.points = self.correct_points + lasso_points[1:]
        #     elif self.switchMode==BlockMode['line'] and self.line_begin:
        #         if len(self.lines.points)==0: return
        #         pre_pos=self.lines.points[-1]
        #         if calcPointsDistance(pos,pre_pos)>4:
        #             self.lines.points.append(pos)
        #     elif self.switchMode==BlockMode['point']:
        #         self.lines.points = self.correct_points + [pos]
        #     self.repaint()
        #     return

        if self.drawing():                  # 多边形绘制
            self.overrideCursor(CURSOR_DRAW)
            if self.type == ShapeType['block'].value and self.block_begin:    # 画区域块
                if self.switchMode==BlockMode['block'] and self.scissor.dllEnd:
                    lasso_points=self.scissor.getEdge(0,pos.x(),pos.y())
                    self.lines.points = self.correct_points + lasso_points[1:]
                elif self.switchMode==BlockMode['line'] and self.line_begin:
                    if len(self.lines.points)==0: return
                    pre_pos=self.lines.points[-1]
                    if calcPointsDistance(pos,pre_pos)>4:
                        self.lines.points.append(pos)
                elif self.switchMode==BlockMode['point']:
                    self.lines.points = self.correct_points + [pos]
                self.repaint()
                return

            if self.type in [ShapeType['line'].value,ShapeType['block'].value]:
                for shape in reversed([s for s in self.shapes if self.isVisible(s)]):
                    if shape.edit == True:
                        shape.highlightClear()
                        index = shape.nearestVertex(pos, self.epsilon)
                        if index is 0 and len(self.lines)>1:
                            self.hVertex, self.hShape = index, shape
                            self.overrideCursor(CURSOR_POINT)
                            shape.highlightVertex(0, shape.NEAR_VERTEX)
                            self.hopeline = True

            if self.current and self.type in [ShapeType['rect'].value,ShapeType['cuboid'].value]:
                color = self.drawingLineColor
                if self.outOfPixmap(pos):
                    # Don't allow the user to draw outside the pixmap.
                    # Project the point to the pixmap's edges.
                    pos = self.intersectionPoint(self.current[-1], pos)
                                                                # 如果足够接近，就不移动
                elif len(self.current) > 1 and self.closeEnough(pos, self.current[0]):
                    # Attract line to starting point and colorise to alert the
                    # user:
                    pos = self.current[0]
                    color = self.current.line_color
                    self.overrideCursor(CURSOR_POINT)
                    self.current.highlightVertex(0, Shape.NEAR_VERTEX)
                self.line[1] = pos
                self.line.line_color = color
                self.prevPoint = QPointF()
                self.current.highlightClear()
            elif self.current and self.type==ShapeType['circle'].value:
                self.line.type=4
                self.line.points=[self.current[0],pos]
                self.line.close()
            else:
                self.prevPoint = pos
            self.repaint()
            return

        if Qt.RightButton & ev.buttons():   # Polygon copy moving.鼠标右击
            if self.selectedShapeCopy and self.prevPoint:
                self.overrideCursor(CURSOR_MOVE)
                self.boundedMoveShape(self.selectedShapeCopy, pos)
                self.repaint()
            elif self.selectedShape:
                self.selectedShapeCopy = self.selectedShape.copy()
                self.repaint()
            return

        if Qt.LeftButton & ev.buttons():    # 多边形移动
            if self.selectedVertex():
                self.boundedMoveVertex(pos)
                self.shapeMoved.emit()
                self.repaint()
                self.moveFlag=True
            elif self.selectedShape and self.prevPoint:
                self.overrideCursor(CURSOR_MOVE)
                self.boundedMoveShape(self.selectedShape, pos)
                self.shapeMoved.emit()
                self.repaint()
            else:
                self.overrideCursor(CURSOR_MOVE)
                self.boundedMoveShape(self.selectedShape, pos)
                self.shapeMoved.emit()
                self.repaint()
            return

        # Just hovering over the canvas, 2 posibilities:
        # - Highlight shapes
        # - Highlight vertex
        # Update shape/vertex fill and tooltip value accordingly.
        self.setToolTip("Image")
        for shape in reversed([s for s in self.shapes if self.isVisible(s)]):
            # Look for a nearby vertex to highlight. If that fails,
            # check if we happen to be inside a shape.
            index = shape.nearestVertex(pos, self.epsilon)
            # index_edge = shape.nearestEdge(pos, self.epsilon)
            if index is not None:
                if self.selectedVertex():
                    self.hShape.highlightClear()
                self.hVertex, self.hShape = index, shape
                # self.hEdge = index_edge
                shape.highlightVertex(index, shape.MOVE_VERTEX)
                self.overrideCursor(CURSOR_POINT)
                self.setToolTip("Click & drag to move point")
                self.setStatusTip(self.toolTip())
                self.update()
                break
            elif shape.containsPoint(pos):
                if self.selectedVertex():
                    self.hShape.highlightClear()
                self.hVertex=None
                self.hShape=shape
                # self.hEdge=index_edge
                self.setToolTip("Click & drag to move shape '%s'"% shape.label)
                self.setStatusTip(self.toolTip())
                self.overrideCursor(CURSOR_GRAB)
                self.update()
                break
        else:  # Nothing found, clear highlights, reset state.
            if self.hShape:
                self.hShape.highlightClear()
                self.update()
            self.hVertex, self.hShape,self.hEdge = None, None, None
        self.overrideCursor(CURSOR_DEFAULT)

    def getEllipsePoints(self,shape):
        points=shape.points
        radius=math.sqrt(pow(points[0].x()-points[1].x(),2)+pow(points[0].y()-points[1].y(),2))
        point1=QPointF(points[0].x(),points[0].y()+radius)
        point2=QPointF(points[0].x()+radius,points[0].y())
        shape.points=[points[0],point1,point2]


    # 鼠标按下事件
    def mousePressEvent(self, ev):
        pos = self.transformPos(ev.pos())
        pos = self.formatPoint(pos)

        if ev.button() == Qt.LeftButton:    # 左键按下-button事件产生的按钮
            if self.drawing() :
                if  self.type == ShapeType['rect'].value:
                    self.handleDrawing(pos)
                    # if self.current==None:
                    #     self.line.type = self.type
                    #     self.current = Shape(type=self.type)
                elif self.type == ShapeType['block'].value:
                    self.isBlockPressMouse = True
                    self.blockPrevPoint = pos
                    if len(self.lines) == 0:
                        self.block_begin=True
                        self.lines.type = self.type
                        self.lines.edit = True
                        self.shapes.append(self.lines)
                        self.setHiding(False)
                        self.scissor.getEdge(4, pos.x(), pos.y())
                        self.update()
                    if self.switchMode == BlockMode['line']:
                        self.line_begin=True
                elif self.type == ShapeType['circle'].value:
                    if self.current:
                        assert len(self.current.points)==1
                        # self.shapes.remove(self.current)
                        self.getEllipsePoints(self.line)
                        self.current.points=self.line.points
                        self.finalise()
                    else:
                        self.line.type = self.type
                        self.current = Shape(type=self.type,order=len(self.shapes)+1)
                        self.current.addPoint(pos)
                        self.current.type = 4
                        self.line.points = [pos, pos]
                        self.setHiding()
                        self.drawingPolygon.emit(True)
                        self.update()
                elif self.type == ShapeType['cuboid'].value:
                    if self.tmpCuboid==None:
                        # self.line.type = self.type
                        # self.current = Shape(type=self.type)
                        self.tmpCuboid = Shape(type=self.type,order=len(self.shapes) + 1,maxPoints=8)
                    self.handleDrawing(pos)
            else:
                self.selectShapePoint(pos)
                if self.selectedShape is not None and self.selectedShape.type==ShapeProperty.SHAPE_TYPE.index('line'):
                    self.lanelineShape=self.selectedShape
                self.prevPoint = pos
                self.repaint()
                                            # 右键按下-拷贝/移动
        elif ev.button() == Qt.RightButton and self.editing():
            self.selectShapePoint(pos)
            self.prevPoint = pos
            self.update()

    # 鼠标抬起事件
    def mouseReleaseEvent(self, ev):
        if ev.button() == Qt.RightButton:   # 右键抬起
                                            # 复制矩形框
            menu = self.menus[bool(self.selectedShapeCopy)]
            self.restoreCursor()
            if not menu.exec_(self.mapToGlobal(ev.pos())) and self.selectedShapeCopy:
                                            # 通过删除阴影复制来取消移动。
                self.selectedShapeCopy = None
                self.repaint()
                                            # 左键抬起(选中图形)-移动
        elif ev.button() == Qt.LeftButton:                          # 左键抬起
            if self.selectedShape:                                  # 选中图形
                if self.selectedVertex():                           # 选中图形的点
                    if self.moveFlag and self.hShape.type==ShapeType['line'].value:          # 车道线曲线拟合
                        if self.hVertex != 0 and self.hVertex+1 != len(self.hShape) and self.isLanelineLabel:
                            p1=self.prevPoint
                            p3=self.hShape[self.hVertex]
                            self.changePosition(self.hShape[:self.hVertex+1],p1,self.hShape[0],p3)
                            # self.changePosition(self.hShape[self.hVertex-1:],p1,self.hShape[-1],p3)
                        elif self.isLanelineLabel:
                            p1=self.prevPoint
                            p3=self.hShape[self.hVertex]
                            p2=self.hShape[0] if self.hShape[0].x()!=p3.x() else self.hShape[-1]
                            self.changePosition(self.hShape,p1,p2,p3)
                        # else:

                        self.moveFlag=False
                    self.overrideCursor(CURSOR_POINT)
                else:                                               # 车道线添加点
                    # if self.hShape.type==ShapeProperty.SHAPE_TYPE.index('line'):
                    self.overrideCursor(CURSOR_GRAB)
            else:                                                   # 没有选中图形
                if self.drawing() and self.type == ShapeProperty.SHAPE_TYPE.index('block'):# 图像块处理
                    pos = self.blockPrevPoint
                    self.createBlock(pos)
                    self.isBlockPressMouse = False
                    self.update()
                else:                                                # 创建图形
                    if self.drawing():
                        pos = self.transformPos(ev.pos())
                        pos = self.formatPoint(pos)
                        self.handleDrawing(pos)

    # # 块处理
    # def copeBlock(self,pos):
    #     if self.mode == self.CREATE:        # 创建块
    #         self.createBlock(pos)
    #     elif self.mode == self.CORRECT:     # 修正块
    #         self.createBlock(pos)

    # 创建块
    def createBlock(self,pos):
        self.select_points.append(pos)
        if self.switchMode == BlockMode['point']:
            self.correct_points.append(pos)
        elif self.switchMode == BlockMode['line']:
            self.correct_points = selectPoints_list(self.lines.points, self.select_points)
        elif self.switchMode == BlockMode['block']:
            lasso_points = self.scissor.getEdge(0, pos.x(), pos.y())
            self.lines.points = self.correct_points + lasso_points
            self.correct_points = selectPoints_list(self.lines.points, self.select_points)
            self.scissor.getEdge(4, pos.x(), pos.y())
        self.lines.points = copy.copy(self.correct_points)


    # 移动结束
    def endMove(self, copy=False):
        assert self.selectedShape and self.selectedShapeCopy
        shape = self.selectedShapeCopy
        if copy:
            self.shapes.append(shape)
            self.selectedShape.selected = False
            self.selectedShape = shape
            self.repaint()
        else:
            self.selectedShape.points = [p for p in shape.points]
        self.selectedShapeCopy = None

    # 隐藏矩形框背景
    def hideBackroundShapes(self, value):
        self.hideBackround = value
        if self.selectedShape:
            # Only hide other shapes if there is a current selection.
            # Otherwise the user will not be able to select a shape.
            self.setHiding(True)
            self.repaint()

    # 绘制图形
    def handleDrawing(self, pos):
       if self.type == ShapeType['rect'].value:
           if self.current and self.current.reachMaxPoints() is False:
               minX=min(self.current[0].x(),self.line[1].x())
               maxX=max(self.current[0].x(),self.line[1].x())
               minY=min(self.current[0].y(),self.line[1].y())
               maxY=max(self.current[0].y(),self.line[1].y())
               self.current.popPoint()
               # initPos = self.current[0]
               # minX = initPos.x()
               # minY = initPos.y()
               # targetPos = self.line[1]
               # maxX = targetPos.x()
               # maxY = targetPos.y()
               self.current.addPoint(QPointF(minX,minY))
               self.current.addPoint(QPointF(maxX, minY))
               self.current.addPoint(QPointF(maxX,maxY))
               self.current.addPoint(QPointF(minX, maxY))

               # initPos = self.current[0]
               # minX = initPos.x()
               # minY = initPos.y()
               # targetPos = self.line[1]
               # maxX = targetPos.x()
               # maxY = targetPos.y()
               # self.current.addPoint(QPointF(maxX, minY))
               # self.current.addPoint(targetPos)
               # self.current.addPoint(QPointF(minX, maxY))
               if self.del_block:
                   self.finalise_del()
                   self.del_block=False
                   return
               self.finalise()
           elif not self.outOfPixmap(pos):
               self.current = Shape(order=len(self.shapes)+1)
               self.current.type = self.type
               self.current.addPoint(pos)
               self.line.points = [pos, pos]
               self.setHiding()
               #self.drawingPolygon.emit(True)
               self.update()
       if self.type == ShapeType['point'].value:
           if self.lanelineShape is not None:
               self.lanelineShape.addPoint(pos)
               self.finalise_point()
           else:
               self.point = Shape(order=len(self.shapes)+1)
               self.point.type = self.type
               self.point.addPoint(pos)
               self.shapes.append(self.point)
               self.newShape.emit()
           self.setHiding(False)
           self.update()
       elif self.type == ShapeType['line'].value:
           if len(self.lines)>0:
               try:
                  self.shapes.remove(self.lines)
               except Exception:
                  self.lines=Shape(order=len(self.shapes)+1)
           self.lines.type = self.type
           self.lines.addPoint(pos)
           self.lines.edit = True
           self.shapes.append(self.lines)
           self.setHiding(False)
           #self.newShape.emit()
           self.update()
           self.finalise_line()
       elif self.type == ShapeType['block'].value:
           if len(self.lines)>0:
               try:
                  self.shapes.remove(self.lines)
               except Exception:
                  self.lines=Shape(order=len(self.shapes)+1)
           self.lines.type = self.type
           self.lines.addPoint(pos)
           self.lines.edit = True
           self.shapes.append(self.lines)
           self.setHiding(False)
           self.update()
       elif self.type == ShapeType['cuboid'].value:
           if self.current and self.current.reachMaxPoints() is False:
               minX=min(self.current[0].x(),self.line[1].x())
               maxX=max(self.current[0].x(),self.line[1].x())
               minY=min(self.current[0].y(),self.line[1].y())
               maxY=max(self.current[0].y(),self.line[1].y())
               self.current.popPoint()
               # initPos = self.current[0]
               # minX = initPos.x()
               # minY = initPos.y()
               # targetPos = self.line[1]
               # maxX = targetPos.x()
               # maxY = targetPos.y()
               self.current.addPoint(QPointF(minX,minY))
               self.current.addPoint(QPointF(maxX, minY))
               self.current.addPoint(QPointF(maxX,maxY))
               self.current.addPoint(QPointF(minX, maxY))
               self.finalise_cuboid()
           elif not self.outOfPixmap(pos):
               self.current = Shape(order=len(self.shapes)+1)
               self.current.type = self.type
               self.current.addPoint(pos)
               self.line.points = [pos, pos]
               self.setHiding()
               #self.drawingPolygon.emit(True)
               self.update()



    def formatPoint(self,point):
        (width,height) = (self.pixmap.width(), self.pixmap.height())
        x=0 if point.x()<0 else  point.x()
        y=0 if point.y()<0 else  point.y()
        x=width-1 if x>width-1 else  x
        y=height-1 if y>height-1 else  y
        return QPoint(round(x),round(y))

    # 隐藏背景
    def setHiding(self, enable=True):
        self._hideBackround = self.hideBackround if enable else False

    # 判断是否要关闭形状
    def canCloseShape(self):
        return self.drawing() and self.current and len(self.current) > 2

    # 鼠标双击事件
    def mouseDoubleClickEvent(self, ev):
        # We need at least 4 points here, since the mousePress handler
        # adds an extra one before this handler is called.
        if self.canCloseShape() and len(self.current) > 3:
            self.current.popPoint()
            self.finalise()
        if self.type == 2:
            if ev.button() == Qt.LeftButton and self.selectedShape and self.selectedVertex():
                self.fitCurve(self.hShape.points)
                self.repaint()
            if self.hopeline == True:
                self.lineflag = 1
                self.lines.close()
                #self.shapes.append(self.lines)
                self.lines = None
                self.setHiding(False)
                self.newShape.emit()
                self.update()
                self.lines = Shape(order=len(self.shapes)+1)
                self.hopeline = False

    def fitCurve(self,points):
        listx = []
        listy = []
        for point in points:
            listx.append(point.x())
            listy.append(point.y())
        listx_np = np.array(listx)

        m = []
        for index in range(4):
            a = np.array(listy) ** (index)
            m.append(a)
        A = np.array(m).T
        b = listx_np.reshape(listx_np.shape[0], 1)

        def projection(A, b):
            AA = A.T.dot(A)  # A乘以A转置
            w = np.linalg.inv(AA).dot(A.T).dot(b)
            return A.dot(w)

        fitting_listx = projection(A, b)
        fitting_listx.shape = (fitting_listx.shape[0],)

        for index,point in enumerate(zip(fitting_listx[1:-1],listy[1:-1])):
            points[index+1].setX(point[0])
            points[index+1].setY(point[1])
        # points = []
        # for point in zip(fitting_listx,listy):
        #     points.append(QPointF(point[0], point[1]))

    def selectShape(self, shape):
        self.deSelectShape()
        shape.selected = True
        self.selectedShape = shape
        self.setHiding()
        self.selectionChanged.emit(True)
        self.update()

    # 选择包含此点的第一个形状(右击选择点)
    def selectShapePoint(self, point):
        self.deSelectShape()
        if self.selectedVertex():  # A vertex is marked for selection.
            index, shape = self.hVertex, self.hShape
            self.hVertex_backup,self.hShape_backup = self.hVertex, self.hShape
            shape.highlightVertex(index, shape.MOVE_VERTEX)
            self.selectShape(shape)
            return
        for shape in reversed(self.shapes):
            if self.isVisible(shape) and shape.containsPoint(point):
                self.selectShape(shape)
                self.calculateOffsets(shape, point)
                return

    # 计算偏置距离(移动距离)
    def calculateOffsets(self, shape, point):
        rect = shape.boundingRect()
        x1 = rect.x() - point.x()
        y1 = rect.y() - point.y()
        x2 = (rect.x() + rect.width()) - point.x()
        y2 = (rect.y() + rect.height()) - point.y()
        self.offsets = QPointF(x1, y1), QPointF(x2, y2)

    # 边界处移动顶点
    def boundedMoveVertex(self, pos):
        index, shape = self.hVertex, self.hShape
        point = shape[index]
        if self.outOfPixmap(pos):
            pos = self.formatPoint(pos)
            # pos = self.intersectionPoint(point, pos)


        shiftPos = pos - point
        if shape.type == 4:
            if index == 0:
                shiftPos1=QPointF(pos.x()-shape.points[1].x(),0)
                shiftPos2=QPointF(0,pos.y()-shape.points[2].y())
                shape.moveVertexBy(1, shiftPos1)
                shape.moveVertexBy(2, shiftPos2)
            elif index == 1:
                shiftPos.setX(0)
            elif index == 2:
                shiftPos.setY(0)
        shape.moveVertexBy(index, shiftPos)

        if shape.type == 0:
           lindex = (index + 1) % 4
           rindex = (index + 3) % 4
           if index % 2 == 0:
               rshift = QPointF(shiftPos.x(), 0)
               lshift = QPointF(0, shiftPos.y())
           else:
               lshift = QPointF(shiftPos.x(), 0)
               rshift = QPointF(0, shiftPos.y())
           shape.moveVertexBy(rindex, rshift)
           shape.moveVertexBy(lindex, lshift)

    # 边界处移动图形
    def boundedMoveShape(self, shape, pos):
        if shape is None or self.outOfPixmap(pos):
            return False  # No need to move
        o1 = pos + self.offsets[0]
        if self.outOfPixmap(o1):
            pos -= QPointF(min(0, o1.x()), min(0, o1.y()))
        o2 = pos + self.offsets[1]
        if self.outOfPixmap(o2):
            pos += QPointF(min(0, self.pixmap.width() - o2.x()),
                           min(0, self.pixmap.height() - o2.y()))
        # The next line tracks the new position of the cursor
        # relative to the shape, but also results in making it
        # a bit "shaky" when nearing the border and allows it to
        # go outside of the shape's area for some reason. XXX
        #self.calculateOffsets(self.selectedShape, pos)
        dp = pos - self.prevPoint
        if dp:
            shape.moveBy(dp)
            self.prevPoint = pos
            return True
        return False

    # 车道线点集联动
    def changePosition(self,points,p1,p2,p3):
        old_index=self.hVertex
        for index,point in enumerate(points[1:-1]):
            dx=int((p3.x()-p1.x())*(p2.x()-point.x())/(p2.x()-p1.x()))
            dy=int((point.y()-p2.y())*(p3.y()-p2.y())/(p1.y()-p2.y())-(point.y()-p2.y()))
            pos=QPointF(point.x()+dx,point.y()+dy)
            self.hVertex=index+1
            self.boundedMoveVertex(pos)
        self.hVertex=old_index


    # 设置选择属性，发出selectionChanged信号
    def deSelectShape(self):
        if self.selectedShape:
            self.selectedShape.selected = False
            self.selectedShape = None
            self.setHiding(False)
            self.selectionChanged.emit(False)
            self.update()

    # 删除选中图形
    def deleteSelected(self):
        if self.selectedShape:
            shape = self.selectedShape
            self.shapes.remove(self.selectedShape)
            self.selectedShape = None
            self.update()
            return shape

    # 拷贝选中的图形
    def copySelectedShape(self):
        if self.selectedShape:
            shape = self.selectedShape.copy()
            self.deSelectShape()
            self.shapes.append(shape)   # 增加拷贝图形
            shape.selected = True
            self.selectedShape = shape
            self.boundedShiftShape(shape)
            return shape

    def boundedShiftShape(self, shape):
        # Try to move in one direction, and if it fails in another.
        # Give up if both fail.
        point = shape[0]
        offset = QPointF(2.0, 2.0)
        self.calculateOffsets(shape, point)
        self.prevPoint = point
        if not self.boundedMoveShape(shape, point - offset):
            self.boundedMoveShape(shape, point + offset)

    def exportPhoto(self):
        self.value = True


    # 重绘事件
    def paintEvent(self, event):
        #self.lines = []
        index = 0
        if not self.pixmap:
            return super(Canvas, self).paintEvent(event)

        p = self._painter
        p.begin(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.HighQualityAntialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)

        p.scale(self.scale, self.scale)
        p.translate(self.offsetToCenter())

        p.drawPixmap(0, 0, self.pixmap)
        Shape.scale = self.scale
        for shape in self.shapes:
            if (shape.selected or not self._hideBackround) and self.isVisible(shape):
                # shape.fill = shape.selected or shape == self.hShape
                shape.paint(p)
                if shape.type == ShapeProperty.SHAPE_TYPE.index('point'):
                    index += 1
                    font = QFont()
                    font.setPointSize(8)
                    font.setBold(True)
                    font.setWeight(75)
                    p.setFont(font)
                    p.drawText(shape.points[0].x()+5, shape.points[0].y()+5,str(index) )
                # if shape.type == ShapeProperty.SHAPE_TYPE.index('line'):
                #     if len(self.lines) == 2:
                #         p.drawPolyline()
                #         p.drawLine(self.lines[0].x(), self.lines[0].y(), self.lines[1].x(), self.lines[1].y())
                #         self.lines.pop(0)
        if self.current:
            self.current.paint(p)
            self.line.paint(p)
        if self.selectedShapeCopy:
            self.selectedShapeCopy.paint(p)

            # Paint rect
        if self.current is not None and len(self.line) == 2:
            leftTop = self.line[0]
            rightBottom = self.line[1]
            rectWidth = rightBottom.x() - leftTop.x()
            rectHeight = rightBottom.y() - leftTop.y()
            p.setPen(self.drawingRectColor)
            p.drawRect(leftTop.x(), leftTop.y(), rectWidth, rectHeight)

        if self.drawing() and not self.prevPoint.isNull() and not self.outOfPixmap(self.prevPoint):
            p.setPen(QColor(0, 0, 0))
            p.drawLine(self.prevPoint.x(), 0, self.prevPoint.x(), self.pixmap.height())
            p.drawLine(0, self.prevPoint.y(), self.pixmap.width(), self.prevPoint.y())

        self.setAutoFillBackground(True)
        if self.verified:
            pal = self.palette()
            pal.setColor(self.backgroundRole(), QColor(184, 239, 38, 128))
            self.setPalette(pal)
        elif self.trafficSign:
            pal = self.palette()
            pal.setColor(self.backgroundRole(), QColor(137, 207, 240, 128))
            self.setPalette(pal)
        else:
            pal = self.palette()
            pal.setColor(self.backgroundRole(), QColor(232, 232, 232, 255))
            self.setPalette(pal)

        p.end()


    def save_image(self):
        image = QImage(int(self.pixmap.width()),int(self.pixmap.height()), QImage.Format_RGB888)
        image.fill(Qt.black)
        index = 0

        p = self._painter
        p.begin(image)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.HighQualityAntialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)

        # p.scale(self.scale, self.scale)
        # p.translate(self.offsetToCenter())

        Shape.scale = self.scale
        for shape in self.shapes:
            if (shape.selected or not self._hideBackround) and self.isVisible(shape):
                shape.paint_without_vertex(p)
                if shape.type == ShapeProperty.SHAPE_TYPE.index('point'):
                    index += 1
                    font = QFont()
                    font.setPointSize(8)
                    font.setBold(True)
                    font.setWeight(75)
                    p.setFont(font)
                    p.drawText(shape.points[0].x()+5, shape.points[0].y()+5,str(index) )

        if self.current:
            self.current.paint_without_vertex(p)
            self.line.paint_without_vertex(p)
        if self.selectedShapeCopy:
            self.selectedShapeCopy.paint_without_vertex(p)

            # Paint rect
        if self.current is not None and len(self.line) == 2:
            leftTop = self.line[0]
            rightBottom = self.line[1]
            rectWidth = rightBottom.x() - leftTop.x()
            rectHeight = rightBottom.y() - leftTop.y()
            p.setPen(self.drawingRectColor)
            p.drawRect(leftTop.x(), leftTop.y(), rectWidth, rectHeight)

        if self.drawing() and not self.prevPoint.isNull() and not self.outOfPixmap(self.prevPoint):
            p.setPen(QColor(0, 0, 0))
            p.drawLine(self.prevPoint.x(), 0, self.prevPoint.x(), image.height())
            p.drawLine(0, self.prevPoint.y(), image.width(), self.prevPoint.y())

        self.setAutoFillBackground(True)
        # if self.verified:
        #     pal = self.palette()
        #     pal.setColor(self.backgroundRole(), QColor(184, 239, 38, 128))
        #     self.setPalette(pal)
        # elif self.trafficSign:
        #     pal = self.palette()
        #     pal.setColor(self.backgroundRole(), QColor(137, 207, 240, 128))
        #     self.setPalette(pal)
        # else:
        pal = self.palette()
        pal.setColor(self.backgroundRole(), QColor(232, 232, 232, 255))
        self.setPalette(pal)
        p.end()
        image.save('F:\\234.jpg')


    # 将坐标转换为画布的逻辑坐标
    def transformPos(self, point):
        """Convert from widget-logical coordinates to painter-logical coordinates."""
        return point / self.scale - self.offsetToCenter()

    # 相对于中心位置的偏置
    def offsetToCenter(self):
        s = self.scale
        area = super(Canvas, self).size()
        w, h = self.pixmap.width() * s, self.pixmap.height() * s
        aw, ah = area.width(), area.height()
        x = (aw - w) / (2 * s) if aw > w else 0
        y = (ah - h) / (2 * s) if ah > h else 0
        return QPointF(x, y)

    # 映射
    def outOfPixmap(self, p):
        w, h = self.pixmap.width(), self.pixmap.height()
        return not (0 <= p.x() <= w and 0 <= p.y() <= h)

    # 最终判断(两点相同时，取消画框)
    def finalise(self):
        assert self.current
        if self.current.points[0] == self.current.points[-1]:
            self.current = None
            self.drawingPolygon.emit(False)
            self.update()
            return

        self.current.fill=True
        self.current.close()

        self.shapes.append(self.current)
        self.current = None
        self.setHiding(False)
        self.newShape.emit()
        self.update()                           # 重绘画布

    def finalise_cuboid(self):
        assert self.current
        if self.current.points[0] == self.current.points[-1]:
            self.current = None
            self.drawingPolygon.emit(False)
            self.update()
            return

        for point in self.current.points:
            self.tmpCuboid.addPoint(point)
        self.current.fill=True
        self.current.close()
        self.current = None
        self.setHiding(False)
        if not self.tmpCuboid.reachMaxPoints():
            self.shapes.append(self.tmpCuboid)
        else:
            self.tmpCuboid = None
            self.newShape.emit()
        self.update()                           # 重绘画布

    def finalise_del(self):
        assert self.current
        if self.current.points[0] != self.current.points[-1]:
            delShapes(self.shapes,self.current)

        self.current = None
        self.drawingPolygon.emit(False)
        self.update()
        # self.setHiding(False)


    def finalise_line(self):
        assert self.lines
        if len(self.lines.points)>2 and self.closeEnough(self.lines.points[-1],self.lines.points[-2]):
            self.lines.points.pop()
            self.saveLines()
        self.update()

    def finalise_point(self):
        assert self.lanelineShape
        if len(self.lanelineShape.points) > 2 and self.closeEnough(self.lanelineShape.points[-1], self.lanelineShape.points[-2]):
            self.lanelineShape.points.pop()
            self.setHiding(False)
            self.setEditing(True)  # 修改结束
            self.lanelineShape = None

    def saveLines(self,value=True):                # 大于两个点保存
        # self.lines.points.pop()
        # self.drawingPolygon.emit(False)
        self.lines.close()
        self.lines = Shape(order=len(self.shapes)+1)
        self.setHiding(False)
        if value:
            self.newShape.emit()

    def closeEnough(self, p1, p2):
        #d = distance(p1 - p2)
        #m = (p1-p2).manhattanLength()
        # print "d %.2f, m %d, %.2f" % (d, m, d - m)
        return distance(p1 - p2) < self.epsilon

    # 找到交叉点(self中线段与p1-p2相交的一个)
    def intersectionPoint(self, p1, p2):
        # Cycle through each image edge in clockwise fashion,
        # and find the one intersecting the current line road_segment.
        # http://paulbourke.net/geometry/lineline2d/
        size = self.pixmap.size()
        points = [(0, 0),
                  (size.width(), 0),
                  (size.width(), size.height()),
                  (0, size.height())]
        x1, y1 = p1.x(), p1.y()
        x2, y2 = p2.x(), p2.y()
        d, i, (x, y) = min(self.intersectingEdges((x1, y1), (x2, y2), points))
        x3, y3 = points[i]
        x4, y4 = points[(i + 1) % 4]
        if (x, y) == (x1, y1):
            # Handle cases where previous point is on one of the edges.
            if x3 == x4:
                return QPointF(x3, min(max(0, y2), max(y3, y4)))
            else:  # y3 == y4
                return QPointF(min(max(0, x2), max(x3, x4)), y3)
        return QPointF(x, y)

    # 相交边
    def intersectingEdges(self, x1y1, x2y2, points):
        """For each edge formed by `points', yield the intersection
        with the line road_segment `(x1,y1) - (x2,y2)`, if it exists.
        Also return the distance of `(x2,y2)' to the middle of the
        edge along with its index, so that the one closest can be chosen."""
        x1, y1 = x1y1
        x2, y2 = x2y2
        for i in range(4):
            x3, y3 = points[i]
            x4, y4 = points[(i + 1) % 4]
            denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
            nua = (x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)
            nub = (x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)
            if denom == 0:
                # This covers two cases:
                #   nua == nub == 0: Coincident
                #   otherwise: Parallel
                continue
            ua, ub = nua / denom, nub / denom
            if 0 <= ua <= 1 and 0 <= ub <= 1:
                x = x1 + ua * (x2 - x1)
                y = y1 + ua * (y2 - y1)
                m = QPointF((x3 + x4) / 2, (y3 + y4) / 2)
                d = distance(m - QPointF(x2, y2))
                yield d, i, (x, y)

    # 这几个函数是滚轮调整大小所必须的重构函数
    def sizeHint(self):
        return self.minimumSizeHint()

    def minimumSizeHint(self):
        if self.pixmap:
            return self.scale * self.pixmap.size()
        return super(Canvas, self).minimumSizeHint()

    def wheelEvent(self, ev):
        qt_version = 4 if hasattr(ev, "delta") else 5
        if qt_version == 4:
            if ev.orientation() == Qt.Vertical:
                v_delta = ev.delta()
                h_delta = 0
            else:
                h_delta = ev.delta()
                v_delta = 0
        else:
            delta = ev.angleDelta()
            h_delta = delta.x()
            v_delta = delta.y()

        mods = ev.modifiers()
        if Qt.ControlModifier == int(mods) and v_delta:
            self.zoomRequest.emit(v_delta)
        else:
            pos = self.transformPos(ev.pos())
            pos = self.formatPoint(pos)
            v_delta and self.scrollRequest.emit(v_delta, Qt.Vertical,pos)
            h_delta and self.scrollRequest.emit(h_delta, Qt.Horizontal,pos)
            self.repaint()
        ev.accept()

    # 撤销块编辑
    def revokeBlock(self):
        try:
            self.shapes.remove(self.lines)
        except Exception:
            print('删除失败')
            return
        if self.mode == self.CORRECT:  # 修正块
            self.setEditing(True)  # 修改结束
            self.setCorrecting(True)
        self.saveLines(False)
        self.correct_points = []
        self.select_points = []
        self.block_begin = False
        self.switchMode = BlockMode['block']
        self.blockMode.emit(self.switchMode.value)





    def keyPressEvent(self, ev):
        key = ev.key()
        if key == Qt.Key_Escape and self.current:
            print('ESC press')
            self.current = None
            self.drawingPolygon.emit(False)
            self.update()
        elif key == Qt.Key_Return:                      # 图形创建结束
            if self.type==3 and self.drawing():
                self.lines.points = self.correct_points
                if self.mode == self.CREATE:            # 新建块
                    self.lines.fill=True
                    selectPoints(self.lines)
                    self.saveLines()
                elif self.mode == self.CORRECT:         # 修正块
                    self.modifyBlock()
                self.correct_points = []
                self.select_points = []
                self.block_begin = False
                self.switchMode = BlockMode['block']
                self.blockMode.emit(self.switchMode.value)
            # elif self.canCloseShape():
            #     self.finalise()
        elif key == Qt.Key_Space:                       # 切换画图形的模式
            self.line_begin = False
            self.switchMode = BlockMode((self.switchMode.value + 1) % 2)
            self.blockMode.emit(self.switchMode.value)
            self.lines.points=copy.copy(self.correct_points)
            if self.switchMode==BlockMode['block'] and len(self.select_points)>0:
                pos=self.select_points[-1]
                self.scissor.getEdge(4, pos.x(), pos.y())
            self.repaint()
        elif key == Qt.Key_Backspace:                   # 删除block的上一个点
            if len(self.select_points)<2:               # 剩余一个点时，取消编辑
                self.revokeBlock()
                return
            pre_point=self.select_points[-2]
            index_list=[index for index,element in enumerate(self.correct_points) if element==pre_point]        # 查找该最后一次出现的位置
            if index_list!=[]:
                self.select_points.pop()                                        # 删除待删除点
                del(self.correct_points[index_list[-1]+1:])                     # 删除正确点集中的点
                self.scissor.getEdge(4, pre_point.x(), pre_point.y())           # 给算法标记上待删除的前一点
                self.lines.points=copy.copy(self.correct_points)                # 更新当前图形
                self.update()

    def setLine(self):
        self.line_begin = False
        self.switchMode = BlockMode['line']
        self.blockMode.emit(self.switchMode.value)
        self.lines.points = copy.copy(self.correct_points)
        self.repaint()

    def modifyBlock(self):
        try:
            self.shapes.remove(self.hShape_backup)
            self.shapes.remove(self.lines)
        except Exception:
            print('删除失败')
        tmp_points=[]
        # 1.找点                                    # 最靠近修改线段的两个点self.hVertex_backup,self.hShape_backup
        index_p1,index_p2,position=selectClosePoints(self.hShape_backup.points,self.lines.points[0],self.lines.points[-1],self.hVertex_backup)
        if position:                   # 中间段修改
            lines_points = self.lines.points if index_p1 < index_p2 else list(reversed(self.lines.points))  #
            index_p1,index_p2 = min(index_p1, index_p2),max(index_p1, index_p2)
            tmp_points=self.hShape_backup.points[:index_p1+1]+lines_points+self.hShape_backup.points[index_p2+1:]
        else:                           # 两边段修改
            lines_points = self.lines.points if index_p1 > index_p2 else list(reversed(self.lines.points))  #
            index_p1,index_p2 = min(index_p1, index_p2),max(index_p1, index_p2)
            tmp_points=lines_points+self.hShape_backup.points[index_p1+1:index_p2]

        self.hShape_backup.points=tmp_points
        selectPoints(self.hShape_backup)
        self.shapes.append(self.hShape_backup)

        self.saveLines(False)
        self.setEditing(True)  # 修改结束
        self.setCorrecting(True)


    # 移动图形
    # 移动一个像素
    def moveOnePixel(self, direction):
        # print(self.selectedShape.points)
        if direction == 'Left' and not self.moveOutOfBound(QPointF(-1.0, 0)):
            # print("move Left one pixel")
            self.selectedShape.points[0] += QPointF(-1.0, 0)
            self.selectedShape.points[1] += QPointF(-1.0, 0)
            self.selectedShape.points[2] += QPointF(-1.0, 0)
            self.selectedShape.points[3] += QPointF(-1.0, 0)
        elif direction == 'Right' and not self.moveOutOfBound(QPointF(1.0, 0)):
            # print("move Right one pixel")
            self.selectedShape.points[0] += QPointF(1.0, 0)
            self.selectedShape.points[1] += QPointF(1.0, 0)
            self.selectedShape.points[2] += QPointF(1.0, 0)
            self.selectedShape.points[3] += QPointF(1.0, 0)
        elif direction == 'Up' and not self.moveOutOfBound(QPointF(0, -1.0)):
            # print("move Up one pixel")
            self.selectedShape.points[0] += QPointF(0, -1.0)
            self.selectedShape.points[1] += QPointF(0, -1.0)
            self.selectedShape.points[2] += QPointF(0, -1.0)
            self.selectedShape.points[3] += QPointF(0, -1.0)
        elif direction == 'Down' and not self.moveOutOfBound(QPointF(0, 1.0)):
            # print("move Down one pixel")
            self.selectedShape.points[0] += QPointF(0, 1.0)
            self.selectedShape.points[1] += QPointF(0, 1.0)
            self.selectedShape.points[2] += QPointF(0, 1.0)
            self.selectedShape.points[3] += QPointF(0, 1.0)
        self.shapeMoved.emit()
        self.repaint()

    # 移出边界
    def moveOutOfBound(self, step):
        points = [p1+p2 for p1, p2 in zip(self.selectedShape.points, [step]*4)]
        return True in map(self.outOfPixmap, points)




    # 最终设置标签(文本、线颜色、填充颜色)
    def setLastLabel(self, text, line_color  = None, fill_color = None):
        assert text
        self.shapes[-1].label = text
        self.shapes[-1].current_id = self.shapes[-1].order
        if line_color:
            self.shapes[-1].line_color = line_color
        
        if fill_color:
            self.shapes[-1].fill_color = fill_color
        return self.shapes[-1]

    # 撤销最后的线
    def undoLastLine(self):
        assert self.shapes
        self.current = self.shapes.pop()
        self.current.setOpen()
        self.line.points = [self.current[-1], self.current[0]]
        self.drawingPolygon.emit(True)

    # 重置所有线(去除最后一根线)
    def resetAllLines(self):
        assert self.shapes
        self.current = self.shapes.pop()
        self.current.setOpen()
        self.line.points = [self.current[-1], self.current[0]]
        self.drawingPolygon.emit(True)
        self.current = None
        self.drawingPolygon.emit(False)
        self.update()

    # 加载图片
    def loadPixmap(self, pixmap):
        self.pixmap = pixmap
        self.shapes = []
        self.repaint()

    # 加载图形
    def loadShapes(self, shapes):
        self.shapes = list(shapes)
        self.current = None
        self.repaint()

    def setShapeColor(self,shapes):
        self.setToolTip("Image")
        for shape in reversed(shapes):
            self.hVertex, self.hShape = 2, shape
            shape.highlightVertex(2, shape.MOVE_VERTEX)
        self.update()

    # 设置图形(将画好的图形放到Visible中)
    def setShapeVisible(self, shape, value):
        self.visible[shape] = value
        self.repaint()

    # 当前形状
    def currentCursor(self):
        cursor = QApplication.overrideCursor()
        if cursor is not None:
            cursor = cursor.shape()         # 游标形状(类型)跟全局变量Cursor对比
        return cursor

    # 设置应用程序的光标
    def overrideCursor(self, cursor):
        self._cursor = cursor
        if self.currentCursor() is None:    # 设置游标形状
            QApplication.setOverrideCursor(cursor)
        else:
            QApplication.changeOverrideCursor(cursor)

    # 取消全局鼠标形状设置
    def restoreCursor(self):
        QApplication.restoreOverrideCursor()

    # 重置鼠标形状设置
    def resetState(self):
        self.restoreCursor()
        self.pixmap = None
        self.update()

    def resetLine(self):
        self.lines=Shape(order=len(self.shapes)+1)