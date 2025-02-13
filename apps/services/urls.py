from django.urls import path
from . import views

urlpatterns = [
    path('', views.ServiceListView.as_view(), name='services'),
    path('<int:service_id>/', views.service_detail, name='service_detail'),
    path('projects/', views.ProjectListView.as_view(), name='projects'),
]