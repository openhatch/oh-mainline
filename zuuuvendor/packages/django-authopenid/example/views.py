# -*- coding: utf-8 -*-
from django.contrib.auth.forms import *
from django.shortcuts import render_to_response as render
from django.template import RequestContext, loader, Context

from django_authopenid.forms import *


def home(request):
    form1 = OpenidSigninForm()
    form2 = AuthenticationForm()
    return render("home.html", {
        'form1': form1,
        'form2': form2
    }, context_instance=RequestContext(request))