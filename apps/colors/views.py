from django.shortcuts import render
from .models import Color

def color_list(request):
    colors = Color.objects.all()
    return render(request, 'colors/list.html', {'colors': colors})
