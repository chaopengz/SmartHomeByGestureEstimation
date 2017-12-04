from django.shortcuts import render, render_to_response
from django.http import *
from django.template import loader, context, RequestContext
from Furniture import *


# Create your views here.
def index(request):
    return render_to_response("index.html")


def receivePic(request):
    if request.method == "POST":
        # 接受图片，进行手势判断
        pass
    else:
        return render_to_response("index.html")


def getFurnitureState(request):
    pass
