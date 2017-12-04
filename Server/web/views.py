from django.shortcuts import render, render_to_response
from django.http import *
from django.template import loader, context, RequestContext


# Create your views here.
def index(request):
    return render_to_response("index.html")


