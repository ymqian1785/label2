from PyQt4.QtCore import *
from new_function.shape_property import *

# 移动修正后的点
def modifyErrorPoints(pre_points,cur_points):
    for pre_point in pre_points:
        index_p=findClosePoint(cur_points,pre_point)
        point=cur_points[index_p]
        pre_point.setX(point.x())
        pre_point.setY(point.y())


# 选择points中离p1，p2最近的点
def selectClosePoints(points,p1,p2,hVertex_index):                # 道路分割修正选取最近点   返回true为线段中间；false为线段两边
    index_p1=findClosePoint(points,p1)
    index_p2=findClosePoint(points,p2)
    return index_p1,index_p2,min(index_p1,index_p2)<=hVertex_index and hVertex_index<=max(index_p1,index_p2)

# 找到离p最近的点
def findClosePoint(points,p):
    index_p=0
    min_p=calcPointsDistance(p,points[0])
    for index,point in enumerate(points):
        distance_p=calcPointsDistance(p,point)
        if distance_p<min_p:
            min_p=distance_p
            index_p=index
    return index_p



# 计算两点的Euclid距离
def calcPointsDistance(p1, p2):
    return pow(p1.x() - p2.x(), 2) + pow(p1.y() - p2.y(), 2)

# 计算三点的角度
def calcAngle(pointA, pointB, pointC):
    if (pointA.x() == pointB.x() and pointB.y() == pointC.y()) or (
            pointA.y() == pointB.y() and pointB.x() == pointC.x()):
        cosAngle = 0  # math.atan2无法计算90°角
    else:
        vector_AB = QPoint(pointA.x() - pointB.x(), pointA.y() - pointB.y())
        vector_CB = QPoint(pointC.x() - pointB.x(), pointC.y() - pointB.y())
        angle_AB = math.atan2(vector_AB.y(), vector_AB.x())
        angle_CB = math.atan2(vector_CB.y(), vector_CB.x())
        cosAngle = math.cos(abs(angle_AB - angle_CB))
    return cosAngle

# 两点是否足够靠近
def closeEnough(p1, p2):
    return calcPointsDistance(p1,p2) < 10

def farEnough(p1,p2):
    return calcPointsDistance(p1,p2) > 50

def selectPoints_list(points,save_points=[]):
    if len(points) < 2:
        return points
    result = []
    pointA = points[0]  # 第一个、第二个点
    result.append(pointA)
    pointB = points[1]
    result.append(pointB)

    for vertex_id, point in enumerate(points[2:]):  # 遍历从第三个点开始的点集
        pointC = point
        cosAngle = calcAngle(pointA, pointB, pointC)  # 如果cosAngle>cos(180-N)即保存
        if pointB in save_points:                       # 保存所有需要保存的点
            result.append(pointB)
            pointA = pointB
            pointB = pointC
            continue
        if cosAngle > ShapeProperty.SEGMENT_ANGLERANGE or farEnough(pointB, pointC):
            # if pointA != pointB and closeEnough(pointA, pointB):
            if closeEnough(pointA, pointB):
                pointB = pointC
                continue
            result.append(pointB)
            pointA = pointB
        pointB = pointC
    result.append(points[-1])
    return result

# 筛选点集
def selectPoints(shape):
  if len(shape.points) < 2:
      return False
  shape.points = selectPoints_list(shape.points)
  return True

def delShapes(shapes,rect):
    total_num=len(shapes)-1
    for shape_id in range(total_num+1):
        if rect.containsShape(shapes[total_num-shape_id]):
            shapes.pop(total_num-shape_id)

