from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from apps.services.models import Project
from django.db.models import Avg, Count
from .models import Testimonial
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse
from .forms import TestimonialForm
from utils.services import GoogleReviewsService



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

def testimonials_section(request):
    testimonials = Testimonial.objects.filter(
        active=True,
        verified=True
    ).order_by('-featured', '-date_posted')[:10]

    stats = Testimonial.objects.filter(active=True, verified=True).aggregate(
        average_rating=Avg('rating'),
        total_reviews=Count('id')
    )

    context = {
        'testimonials': testimonials,
        'average_rating': stats['average_rating'] or 0,
        'total_reviews': stats['total_reviews'] or 0
    }

    return render(request, 'testimonials/testimonials_section.html', context)

def testimonials_list(request):
    testimonials = Testimonial.objects.filter(
        active=True, 
        verified=True
    ).order_by('-featured', '-date_posted')

    stats = Testimonial.objects.filter(
        active=True, 
        verified=True
    ).aggregate(
        average_rating=Avg('rating'),
        total_reviews=Count('id')
    )

    context = {
        'testimonials': testimonials,
        'stats': stats,
        'form': TestimonialForm()
    }
    return render(request, 'testimonials/list.html', context)

def submit_testimonial(request):
    if request.method == 'POST':
        form = TestimonialForm(request.POST)
        if form.is_valid():
            testimonial = form.save(commit=False)
            testimonial.platform = 'site'
            testimonial.save()
            
            messages.success(
                request, 
                _("Merci pour votre témoignage! Il sera publié après validation.")
            )
            return redirect('testimonials:list')
        else:
            messages.error(
                request,
                _("Veuillez corriger les erreurs dans le formulaire.")
            )
    return redirect('testimonials:list')

@user_passes_test(lambda u: u.is_staff)
def sync_google_reviews(request):
    service = GoogleReviewsService()
    success = service.sync_reviews()
    
    return JsonResponse({
        'success': success,
        'message': _("Synchronisation réussie!") if success else _("Erreur de synchronisation")
    })