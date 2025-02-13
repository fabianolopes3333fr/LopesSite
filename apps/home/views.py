from django.shortcuts import render

# Create your views here.
from django.views.generic import TemplateView
from apps.services.models import Project



def home(request):
    recent_projects = Project.objects.all().order_by('-completion_date')[:6]
    return render(request, 'home/index.html', {'recent_projects': recent_projects})

    context = {
        'recent_projects': recent_projects,
        'image_url1': static('images/project1.jpg'),
        'image_url2': static('images/project2.jpg'),
        'image_url3': static('images/project3.jpg'),
    }
    
    return render(request, 'home/index.html', context)

class AboutView(TemplateView):
    template_name = 'home/about.html'

# class HomePageView(TemplateView):
#     template_name = 'home/index.html'

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['recent_projects'] = Project.objects.all().order_by('-completion_date')[:6]  # Pega os 6 projetos mais recentes
#         return context



# def home(request):
#     return render(request, 'home/index.html')