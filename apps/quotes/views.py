from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from django.contrib.auth import login
from django.db import transaction
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.db.models import Q
from .models import Paint, PaintCategory, Quote, QuoteStatusUpdate
from .forms import QuoteForm, QuoteUserForm
from apps.users.models import CustomUser, ClientProfile
from django.conf import settings 
from django.utils import timezone
from django.core.exceptions import ValidationError


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


@require_http_methods(["GET", "POST"])
def create_quote(request):
    """View para criar orçamento e conta de usuário se necessário"""
    quote_form = QuoteForm(request.POST or None)
    user_form = None
    
    if not request.user.is_authenticated:
        user_form = QuoteUserForm(request.POST or None)
    
    if request.method == "POST":
        forms_valid = quote_form.is_valid()
        if user_form:
            forms_valid = forms_valid and user_form.is_valid()
            
        if forms_valid:
            try:
                with transaction.atomic():
                    # Se não está logado, cria novo usuário
                    if user_form:
                        user = user_form.save()
                        # Cria perfil do cliente
                        profile = ClientProfile.objects.create(
                            user=user,
                            phone_number=quote_form.cleaned_data['phone_number'],
                            address=quote_form.cleaned_data['address'],
                            postal_code=quote_form.cleaned_data['postal_code'],
                            city=quote_form.cleaned_data['city']
                        )
                        login(request, user)
                    else:
                        user = request.user
                    
                    # Salva o orçamento
                    quote = quote_form.save(commit=False)
                    quote.user = user
                    quote.save()
                    
                    request.session['quote_reference'] = quote.reference  # Supondo que seu modelo Quote tenha um campo 'reference'
                    
                    messages.success(
                        request, 
                        _("Votre demande de devis a été envoyée avec succès! "
                          "Nous vous contacterons sous peu.")
                    )
                    return redirect('quotes:quote_success')
                    
            except Exception as e:
                messages.error(
                    request,
                    _("Une erreur s'est produite. Veuillez réessayer.")
                )
    
    return render(request, 'quotes/create_quote.html', {
        'quote_form': quote_form,
        'user_form': user_form,
        'title': _('Demande de devis')
    })
    
def quote_success(request):
    context = {
        'title': _('Demande de devis réussie'),
        'quote_reference': request.session.get('quote_reference', ''),
    }
    return render(request, 'quotes/quote_success.html', context)