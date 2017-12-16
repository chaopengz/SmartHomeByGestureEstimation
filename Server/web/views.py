# coding:utf-8
from django.shortcuts import render, render_to_response
from django.http import *
from django.template import loader, context, RequestContext
from Furniture import *
import json
from django.http import JsonResponse
from python.poseEstimationTest import *

left = Light()
right = Light()
soft = Soft()
tv = TV()
poseEstimation = PoseEstimation()


# Create your views here.
class SmartHomeWeb():
    @staticmethod
    def index(request):
        return render_to_response("test.html")

    @staticmethod
    def receivePic(request):
        if request.method == "POST":
            # 接受图片，进行手势判断,修改家具对应的state
            filename = request.FILES['image'].name
            imagePath = '../uploadImage/' + filename
            # print 'imagePath is ', imagePath
            destination = open(imagePath, 'wb+')
            for chunk in request.FILES['image'].chunks():
                destination.write(chunk)
            destination.close()

            resultPath = '/home/yihongwei/workspace/SmartHomeByGestureEstimation/' \
                         'Server/static/resultImages/' + filename
            centerHumanKeypoint = poseEstimation.KeypointDetection(imagePath, resultPath)
            poseKind = poseEstimation.getPoseKind(centerHumanKeypoint)

            resultImage = '/static/resultImages/' + filename
            poseEstimation.setResultImage(resultImage)
            SmartHomeWeb.changeFrunitureState(poseKind)

            return HttpResponse(poseKind)
        else:
            return HttpResponse("Only post will be process!")

    @staticmethod
    def getFurnitureState(request):
        result = {'left': left.getState(), 'right': right.getState(), 'tv': tv.getState(), 'soft': soft.getState()}
        return HttpResponse(json.dumps(result), content_type='application/json')

    @staticmethod
    def getPics(request):
        resultImage = poseEstimation.getResultImage()
        return HttpResponse(json.dumps(resultImage), content_type='application/json')

    @staticmethod
    def changeFrunitureState(poseKind):
        if poseKind == 4:
            tv.changeState()
        elif poseKind == 3:
            left.changeState()
        elif poseKind == 1:
            right.changeState()
        else:
            pass

    @staticmethod
    def uploadImage(request):
        return render_to_response("upload.html")
