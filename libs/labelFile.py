# -*- coding: utf8 -*-
# Copyright (c) 2016 Tzutalin
# Create by TzuTaLin <tzu.ta.lin@gmail.com>

from PyQt4.QtGui import QImage

from base64 import b64encode, b64decode
from new_function.shape_property import *
from libs.pascal_voc_io import PascalVocWriter
from libs.pascal_voc_io import XML_EXT
import os.path
import cv2


class LabelFileError(Exception):
    pass

# 文件保存
class LabelFile(object):
    # It might be changed as window creates. By default, using XML ext
    # suffix = '.lif'
    suffix = XML_EXT
    canfix = '.txt'

    def __init__(self, filename=None):
        self.shapes = ()
        self.imagePath = None
        self.imageData = None
        self.verified = False

    # 保存成pascalVoc格式(自定义格式)
    def savePascalVocFormat(self, filename, shapes, imagePath, imageData,type,
                            lineColor=None, fillColor=None, databaseSrc=None):
        imgFolderPath = os.path.dirname(imagePath)          # 图片路径
        imgFolderName = os.path.split(imgFolderPath)[-1]    # 文件夹名
        imgFileName = os.path.basename(imagePath)           # 文件名
        # imgFileNameWithoutExt = os.path.splitext(imgFileName)[0]
        # Read from file path because self.imageData might be empty if saving to
        # Pascal format
        image=cv2.imread(imagePath)
        imageShape = [image.shape[0], image.shape[1],image.shape[2]]

        writer = PascalVocWriter(imgFolderName, imgFileName,# 初始化写入类
                                 imageShape,databaseSrc,imagePath)
        writer.verified = self.verified


        for shape in shapes:                                # 保存点集 points label type difficult
            points = shape['points']
            label = shape['label']
            # Add Chris
            difficult = int(shape['difficult'])
            type = int(shape['type'])
            order = int(shape['order'])
            current_id = int(shape['current_id'])
            track_id = int(shape['track_id'])
            occluded = int(shape['occluded'])
            exist_3D = int(shape['exist_3D'])

            # 当3D框存在对应的2D框，就无需保存，与2D框的属性保存在一起
            if type == ShapeType['cuboid'].value and shape['exist_2D']: continue


            if type in [ShapeType['rect'].value,ShapeType['point'].value]:
                points_3D=[]
                if shape['exist_3D']:
                    for tmp_shape in shapes:
                        if tmp_shape['current_id']==shape['current_id'] and int(tmp_shape['type'])==ShapeType['cuboid'].value:
                            points_3D = tmp_shape['points']
                bndbox = LabelFile.convertPoints2BndBox(points)
                writer.addBndBox(bndbox[0], bndbox[1], bndbox[2], bndbox[3], label, difficult, type,order,current_id,track_id,occluded,exist_3D,points_3D)
            else:
                writer.addLine(points, label, difficult, type, order,current_id,track_id,occluded,exist_3D)
        writer.save(targetFile=filename)
        return

    # 切换核实模式
    def toggleVerify(self):
        self.verified = not self.verified

    ''' ttf is disable
    def load(self, filename):
        import json
        with open(filename, 'rb') as f:
                data = json.load(f)
                imagePath = data['imagePath']
                imageData = b64decode(data['imageData'])
                lineColor = data['lineColor']
                fillColor = data['fillColor']
                shapes = ((s['label'], s['points'], s['line_color'], s['fill_color'])\
                        for s in data['shapes'])
                # Only replace data after everything is loaded.
                self.shapes = shapes
                self.imagePath = imagePath
                self.imageData = imageData
                self.lineColor = lineColor
                self.fillColor = fillColor

    def save(self, filename, shapes, imagePath, imageData, lineColor=None, fillColor=None):
        import json
        with open(filename, 'wb') as f:
                json.dump(dict(
                    shapes=shapes,
                    lineColor=lineColor, fillColor=fillColor,
                    imagePath=imagePath,
                    imageData=b64encode(imageData)),
                    f, ensure_ascii=True, indent=2)
    '''

    @staticmethod
    def isLabelFile(filename):
        fileSuffix = os.path.splitext(filename)[1].lower()
        return fileSuffix == LabelFile.suffix

    @staticmethod
    def convertPoints2BndBox(points):
        xmin = float('inf')
        ymin = float('inf')
        xmax = float('-inf')
        ymax = float('-inf')
        for p in points:
            x = p[0]
            y = p[1]
            xmin = min(x, xmin)
            ymin = min(y, ymin)
            xmax = max(x, xmax)
            ymax = max(y, ymax)

        # Martin Kersner, 2015/11/12
        # 0-valued coordinates of BB caused an error while
        # training faster-rcnn object detector.
        if xmin < 1:
            xmin = 1

        if ymin < 1:
            ymin = 1

        return (int(xmin), int(ymin), int(xmax), int(ymax))
