from django.shortcuts import get_object_or_404, render
from django.views.generic import ListView
from django.db.models import Q
from .models import Service, Project
from .forms import ServiceFilterForm

class ServiceListView(ListView):
    model = Service
    template_name = 'services/service_list.html'
    context_object_name = 'services'
    paginate_by = 9 

    def get_queryset(self):
        queryset = super().get_queryset()
        form = ServiceFilterForm(self.request.GET)

        if form.is_valid():
            category = form.cleaned_data.get('category')
            search = form.cleaned_data.get('search')

            if category:
                queryset = queryset.filter(category=category)
            if search:
                queryset = queryset.filter(
                    Q(title__icontains=search) | Q(description__icontains=search)
                )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ServiceFilterForm(self.request.GET)
        return context


def service_detail(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    projects = Project.objects.filter(service=service)
    return render(request, 'services/service_detail.html', {'service': service, 'projects': projects})


class ProjectListView(ListView):
    model = Project
    template_name = 'services/project_list.html'
    context_object_name = 'projects'