from django.shortcuts import render, get_object_or_404
from .models import Service, Project
from django.views.generic import ListView

class ServiceListView(ListView):
    model = Service
    template_name = 'services/service_list.html'
    context_object_name = 'services'

def service_detail(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    projects = Project.objects.filter(service=service)
    return render(request, 'services/detail.html', {'service': service, 'projects': projects})


class ProjectListView(ListView):
    model = Project
    template_name = 'services/project_list.html'
    context_object_name = 'projects'