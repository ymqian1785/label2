#!/usr/bin/env python
# -*- coding: utf-8 -*-
import math
from PyQt4.QtGui import *
from enum import Enum

class ShapeType(Enum):
    rect=0
    point=1
    line=2
    block=3
    circle=4
    cuboid=5


class BlockMode(Enum):
    point=0
    block=1
    line=2

class DownloadType(Enum):
    none=0
    task=1
    rework=2

class ShapeProperty:
    # LABEL_NAMES = ['bai_shixian', 'bai_xuxian', 'huang_shixian', 'huang_xuxian', 'wheel','road', 'sidewalk', 'building',
    #                'wall', 'fence', 'pole', 'traffic light', 'traffic sign', 'vegetation', 'terrain', 'sky', 'person', 'rider', 'car',
    #                'truck', 'bus', 'train', 'motorcycle', 'bicycle','laneline','bicycle','bus','car','motorcycle','person','truck']
    SEGMENT_ANGLE = 30
    SEGMENT_SEMICIRCLE = 180
    SEGMENT_ANGLERANGE = math.cos((SEGMENT_SEMICIRCLE-SEGMENT_ANGLE)*math.pi/SEGMENT_SEMICIRCLE)
    LABEL_TRANSPARENCY_ORIGN = 80
    LABEL_TRANSPARENCY = 80
    LINE_TRANSPARENCY = 80
    SHAPE_FILL_COLOR = []
    SHAPE_LINE_COLOR = []
    SHAPE_LABEL_NAME = []
    SHAPE_LABEL_NAME_CHINESE = ['道路', '轿车', '客车', '卡车', '自行车', '摩托车', '行人', '交通标志', '障碍物', '背景']
    #              矩形   点      线     块      圆
    SHAPE_TYPE = ['rect','point','line','block','circle']
    # LABEL_TRANSPARENCY = 80
    # LABEL_COLOR = [# QColor(255, 0, 0, 80),    QColor(0, 0, 255, 80),
    #                # QColor(255, 0, 255, 80),      QColor(0, 255, 0, 80),
    #                # QColor(255,255,0, 200),
    #                QColor(128, 64, 128, LABEL_TRANSPARENCY),    QColor(244, 35, 232, LABEL_TRANSPARENCY),
    #                QColor(70, 70, 70, LABEL_TRANSPARENCY),      QColor(102, 102, 156, LABEL_TRANSPARENCY),
    #                QColor(190, 153, 153, LABEL_TRANSPARENCY),   QColor(153, 153, 153, LABEL_TRANSPARENCY),
    #                QColor(250, 170, 30, LABEL_TRANSPARENCY),    QColor(220, 220, 0, LABEL_TRANSPARENCY),
    #                QColor(107, 142, 35, LABEL_TRANSPARENCY),    QColor(152, 251, 152, LABEL_TRANSPARENCY),
    #                QColor(70, 130, 180, LABEL_TRANSPARENCY),    QColor(220, 20, 60, LABEL_TRANSPARENCY),
    #                QColor(255, 0, 0, LABEL_TRANSPARENCY),       QColor(0, 0, 142, LABEL_TRANSPARENCY),
    #                QColor(0, 0, 70, LABEL_TRANSPARENCY),        QColor(0, 60, 100, LABEL_TRANSPARENCY),
    #                QColor(0, 80, 100, LABEL_TRANSPARENCY),      QColor(0, 0, 230, LABEL_TRANSPARENCY),
    #                QColor(119, 11, 32, LABEL_TRANSPARENCY),     QColor(255, 255, 0, LABEL_TRANSPARENCY),
    #                QColor(255, 0, 0, LABEL_TRANSPARENCY),       QColor(0, 0, 0, LABEL_TRANSPARENCY),
    #                QColor(0, 0, 255, LABEL_TRANSPARENCY),       QColor(255, 255, 0, LABEL_TRANSPARENCY),
    #                QColor(0, 255, 0, LABEL_TRANSPARENCY),       QColor(255, 0, 255, LABEL_TRANSPARENCY)]

    CAN_FRAMERATE = 10
    PHOTO_FRAMERATE = 33
                                                                                                                                #90-91

    CUBOID_POINT_LINE=[[4,7,8],[4,5,9],[5,6,10],[6,7,11]]
    CUBOID_LINE_POINT=[[0,1],[1,2],[2,3],[3,0],[4,5],[5,6],[6,7],[7,4],[0,4],[1,5],[2,6],[3,7]]



