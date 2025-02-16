from django.shortcuts import render, redirect
from .forms import QuoteForm  # Alterado de QuoteRequestForm para QuoteForm
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.db.models import Q
from .models import Paint, PaintCategory

class PaintCatalogView(ListView):
    model = Paint
    template_name = 'quotes/catalog.html'
    context_object_name = 'paints'
    paginate_by = 12

    def get_queryset(self):
        queryset = Paint.objects.filter(is_active=True)
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
            
        return queryset.select_related('category', 'supplier')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = PaintCategory.objects.all()
        return context

class PaintDetailView(DetailView):
    model = Paint
    template_name = 'shop/paint_detail.html'
    context_object_name = 'paint'

def request_quote(request):
    if request.method == 'POST':
        form = QuoteForm(request.POST)  # Alterado de QuoteRequestForm para QuoteForm
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre demande de devis a été envoyée avec succès!')
            return redirect('home')
    else:
        form = QuoteForm()  # Alterado de QuoteRequestForm para QuoteForm
    return render(request, 'quotes/request_quote.html', {'form': form})

