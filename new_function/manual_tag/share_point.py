import copy
import numpy as np
from new_function.shape_property import ShapeProperty

dot_library=[]
pos_library=[]

class Dot:
    shape_id = 0
    vertex_id = 0

    def __init__(self, shape_id, vertex_id):
        self.shape_id = shape_id
        self.vertex_id = vertex_id

class DotPosition():
    def __init__(self, dot):
        self.dot_position = []
        self.dot_position.append(dot)

    def addPosition(self, dot):
        if dot not in self.dot_position:
            self.dot_position.append(dot)

class DotSet:
    def __init__(self):
        global dot_library,pos_library
        dot_library=[]
        pos_library=[]


    # 增加点，图形，图像集
    def addShapes(self,shapes):
        self.resetDotSet()
        for shape_id, shape in enumerate(shapes):
            self.addShape(shape,shape_id)

    def addShape(self,shape,shape_id):
        if shape.type != ShapeProperty.SHAPE_TYPE.index('block'):
            return
        for vertex_id, point in enumerate(shape.points):
            self.addPoint(point, Dot(shape_id, vertex_id), shape)

    def addPoint(self,point,dot,shape_dst):
        global dot_library,pos_library
        index = self.closeEnough(point)
        if index!=-1:
            pos_library[index].addPosition(dot)
        else:
            index = len(dot_library)
            dot_library.append(point)
            pos_library.append(DotPosition(dot))
        shape_dst[dot.vertex_id] = dot_library[index]

    # def addPoint(self,point,dot,shape_dst):
    #     global dot_library, pos_library
    #     try:
    #         index = dot_library.index(point)
    #         pos_library[index].addPosition(dot)
    #     except Exception:
    #         dot_library.append(point)
    #         index = dot_library.index(point)
    #         pos_library.append(DotPosition(dot))
    #     shape_dst[dot.vertex_id] = dot_library[index]

    # 删除点，图形
    def delShape(self,shape,shapes):
        for point in shape:
            self.delPoint(point,shapes)
        index = shapes.index(shape)
        shapes.pop(index)

    def delPoint(self,point,shapes):
        global dot_library,pos_library
        index=dot_library.index(point)
        dot_library.pop(index)
        for dot in pos_library[index].dot_position:
            shapes[dot.shape_id].pop(dot.vertex_id)

    def resetDotSet(self):
        global dot_library,pos_library
        dot_library=[]
        pos_library=[]

    def closeEnough(self,pos,distance=4):
        global dot_library,pos_library
        for index,point in enumerate(dot_library):
            if abs(point.x()-pos.x())>2 or abs(point.y()-pos.y())>2:              # 加速，减少运算
                continue
            if pow(point.x()-pos.x(),2)+pow(point.y()-pos.y(),2)<distance:
                return index
        return -1

    def closeEnoughPoints(self,pos1,pos2,distance):
        return pow(pos1.x()-pos2.x(),2)+pow(pos1.y()-pos2.y(),2)<distance

    # 删除非边缘的独立点
    def delSinglePoint(self,shapes,size,del_points):
        for shape_id,shape in enumerate(shapes):
            if shape.type != ShapeProperty.SHAPE_TYPE.index('block'):
                continue
            for vertex_id,point in enumerate(shape.points):
                # 不是边缘点且是单个点需要删除
                if (not self.isEdgePoint(point,size)) and self.isSinglePoint(point) \
                        and vertex_id not in del_points[shape_id]:                      # del_points不能重复
                    del_points[shape_id].append(vertex_id)

    # 是否为边缘点
    def isEdgePoint(self,point,size):
        return point.x()==0 or point.x()==size[1] or point.y()==0 or point.y()==size[0]
    # 是否为独立点
    def isSinglePoint(self,point):
        index=dot_library.index(point)
        position=pos_library[index].dot_position
        shape_id_list=[dot.shape_id for dot in position]
        return len(np.unique(shape_id_list))==1
        # return len(pos_library[index].dot_position)==1

    # 删除重复点
    def delRepeatPoint(self,shapes,del_points):
        for shape_id,shape in enumerate(shapes):
            if shape.type != ShapeProperty.SHAPE_TYPE.index('block'):
                continue
            pre_point = shape[0]
            for vertex_id,point in enumerate(shape.points[1:]):
                cur_point = point
                if self.closeEnoughPoints(cur_point,pre_point,4):
                # if cur_point==pre_point:
                    if vertex_id not in del_points[shape_id]:                           # del_points不能重复
                        del_points[shape_id].append(vertex_id)
                else:
                    pre_point=cur_point

    # 筛选 稀疏化点集后待删除点集
    def selectDelPoints(self,shapes,del_points):
        global dot_library,pos_library
        for shape_id,del_point in enumerate(del_points):                        # 遍历待删除点
            del_count=0
            for delpoint_index,vertex_id in enumerate(del_point):
                index = dot_library.index(shapes[shape_id].points[vertex_id])
                dots = pos_library[index]                                       # 待删除点的关联点
                for dot in dots.dot_position:
                    if dot.vertex_id not in del_points[dot.shape_id]:           # 如果待删除点有关联点，且其关联点不能删除，则此点不能删除
                        del_point.pop(delpoint_index - del_count)                        # 删除后，del_point改变，需要减去index
                        del_count += 1
                        break

    # 整体删除点集
    def delPoints(self,shapes,del_points):
        for shape_id,points in enumerate(del_points):
            points.sort(reverse=False)
            for index,vertex in enumerate(points):
                shapes[shape_id].points.pop(vertex-index)
        length=len(shapes)
        for index in range(length):
            if len(shapes[length-index-1].points)==0:
                shapes.pop(length-index-1)
