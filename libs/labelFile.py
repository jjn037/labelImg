import json
import os.path
import sys
from pascal_voc_io import PascalVocWriter
from base64 import b64encode, b64decode


class LabelFileError(Exception):
    pass


class LabelFile(object):
    # It might be changed as window creates
    suffix = '.lif'

    def __init__(self, filename=None):
        self.shapes = ()
        self.imagePath = None
        self.imageData = None
        if filename is not None:
            self.load(filename)

    def load(self, filename):
        try:
            with open(filename, 'rb') as f:
                data = json.load(f)
                imagePath = data['imagePath']
                imageData = b64decode(data['imageData'])
                lineColor = data['lineColor']
                fillColor = data['fillColor']
                shapes = (
                    (s['label'],
                     s['points'],
                        s['line_color'],
                        s['fill_color']) for s in data['shapes'])
                # Only replace data after everything is loaded.
                self.shapes = shapes
                self.imagePath = imagePath
                self.imageData = imageData
                self.lineColor = lineColor
                self.fillColor = fillColor
        except Exception as e:
            raise LabelFileError(e)

    def save(self, filename, shapes, imagePath, imageData,
             lineColor=None, fillColor=None):
        try:
            with open(filename, 'wb') as f:
                json.dump(dict(
                    shapes=shapes,
                    lineColor=lineColor, fillColor=fillColor,
                    imagePath=imagePath,
                    imageData=b64encode(imageData)),
                    f, ensure_ascii=True, indent=2)
        except Exception as e:
            raise LabelFileError(e)

    def savePascalVocFormat(
            self,
            savefilename,
            image_size,
            shapes,
            imagePath=None,
            databaseSrc=None,
            shape_type_='RECT'):
        imgFolderPath = os.path.dirname(imagePath)
        imgFolderName = os.path.split(imgFolderPath)[-1]
        imgFileName = os.path.basename(imagePath)
        imgFileNameWithoutExt = os.path.splitext(imgFileName)[0]

        #img = cv2.imread(imagePath)
        writer = PascalVocWriter(
            imgFolderName,
            imgFileNameWithoutExt,
            image_size,
            localImgPath=imagePath,
            shape_type=shape_type_)
        bSave = False
        for shape in shapes:
            points = shape['points']
            label = shape['label']
            if shape['shape_type'] == 0:
                print 'add rects'
                bndbox = LabelFile.convertPoints2BndBox(points)
                writer.addBndBox(
                    bndbox[0],
                    bndbox[1],
                    bndbox[2],
                    bndbox[3],
                    label)
            if shape['shape_type'] == 1:
                print 'add polygons'
                writer.addPolygon(points, label)

            bSave = True

        if bSave:
            writer.save(targetFile=savefilename)
        return

    @staticmethod
    def isLabelFile(filename):
        fileSuffix = os.path.splitext(filename)[1].lower()
        return fileSuffix == LabelFile.suffix

    @staticmethod
    def convertPoints2BndBox(points):
        xmin = sys.maxsize
        ymin = sys.maxsize
        xmax = -sys.maxsize
        ymax = -sys.maxsize
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
        if (xmin < 1):
            xmin = 1

        if (ymin < 1):
            ymin = 1

        return (int(xmin), int(ymin), int(xmax), int(ymax))
