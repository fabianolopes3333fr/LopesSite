from django.shortcuts import render

# Create your views here.
from django.views.generic import TemplateView
from apps.services.models import Project

class HomePageView(TemplateView):
    template_name = 'home/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_projects'] = Project.objects.all().order_by('-completion_date')[:6]  # Pega os 6 projetos mais recentes
        return context
