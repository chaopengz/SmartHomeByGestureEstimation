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
def index(request):
    return render_to_response("test.html")


def receivePic(request):
    if request.method == "POST":
        # 接受图片，进行手势判断,修改家具对应的state
        filename = request.FILES['image'].name
        # imagePath = '/home/ubuntu/flower/media/uploads/' + str(int(time.time() * 1000)) + "-" + filename
        imagePath = '..\uploadImage\images\\' + filename
        print 'imagePath is ', imagePath
        destination = open(imagePath, 'wb+')
        for chunk in request.FILES['image'].chunks():
            destination.write(chunk)
        destination.close()
        resultPath = '..\\resultImages\\' + filename
        centerHumanKeypoint = poseEstimation.getCenterKeypointsIndex(imagePath, resultPath)
        poseKind = poseEstimation.getPoseKind(centerHumanKeypoint)
        tv.changeState()
        return HttpResponse(poseKind)
    else:
        tv.changeState()
        return render_to_response("index.html")


def getFurnitureState(request):
    result = {'left': left.state, 'right': right.state, 'tv': tv.state, 'soft': soft.state}
    return HttpResponse(json.dumps(result), content_type='application/json')


def getPics(request):
    l = [];
    l.append("/images/1.jpg")
    l.append("/images/2.jpg")
    l.append("/images/3.jpg")
    return HttpResponse(json.dumps(l), content_type='application/json')
