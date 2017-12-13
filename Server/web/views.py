# coding:utf-8
from django.shortcuts import render, render_to_response
from django.http import *
from django.template import loader, context, RequestContext
from Furniture import *
import json
from django.http import JsonResponse

left = Light()
right = Light()
soft = Soft()
tv = TV()


# Create your views here.
def index(request):
    return render_to_response("test.html")


def receivePic(request):
    if request.method == "POST":
        # 接受图片，进行手势判断,修改家具对应的state
        tv.changeState()
        pass
    else:
        tv.changeState()
        return render_to_response("index.html")


def getFurnitureState(request):
    result = {'left': left.state, 'right': right.state, 'tv': tv.state, 'soft': soft.state}
    return HttpResponse(json.dumps(result), content_type='application/json')
