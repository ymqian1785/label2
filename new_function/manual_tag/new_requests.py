# python
# coding:utf-8
# @Time    : 2018/11/1 17:30
# @Author  : pantao
# @File    : new_requests.py

from PyQt4.QtCore import *


# 对车道线按x轴进行排序，赋予laneline_id:1-n
def sortLaneline(shape_list):
    laneline_list=[]
    others_list=[]
    for shape in shape_list:
        if 'xian' in shape['label']:           # 车道线设为：bai_xuxian；bai_shixian；huang_xuxian；huang_shixian(标注人员的要求，用英文字符，他们看起来费力)
            laneline_list.append(shape)
            # laneline_list.append([shape,shape['points'][0][0]])             # laneline第一个点的x
        else:
            others_list.append(shape)

    laneline_list=sorted(laneline_list,key=lambda shape:int(shape['points'][0][0]),reverse=False)
    shapes = [setLanelineID(index,laneline) for index,laneline in enumerate(laneline_list)]
    for other_shape in others_list:
        shapes.append(other_shape)
    return shapes

def setLanelineID(index,laneline):
    laneline['laneline_id']=index+1
    return laneline


# 自适应两个点
def self_adaption(pos1,pos2):
    dis=(pos2.y()-pos1.y())%10
    add_dis=0 if abs(dis)<5 else 10
    pos=QPoint(pos2.x(),pos2.y()-dis+add_dis)
    return pos
