from django.urls import path
from . import views

urlpatterns = [
    path('', views.color_list, name='color_list'),
]