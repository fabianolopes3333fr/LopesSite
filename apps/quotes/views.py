from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.db.models import Q
from .models import Paint, PaintCategory, Quote, QuoteStatusUpdate
from .forms import QuoteRequestForm 
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



def quote_request(request):
    if request.method == 'POST':
        form = QuoteRequestForm(request.POST, request.FILES)
        try:
            if form.is_valid():
                quote = form.save(commit=False)
                quote.status = 'pending'
                quote.created_at = timezone.now()
                quote.save()
                
                # Envia email de confirmação
                context = {
                    'name': quote.name,
                    'quote_id': quote.id,
                    'service_type': quote.get_service_type_display(),
                    'description': quote.description,
                }
                html_message = render_to_string('email/quote_confirmation.html', context)
                plain_message = strip_tags(html_message)
                
                send_mail(
                    'Confirmation de demande de devis',
                    plain_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [quote.email],
                    html_message=html_message
                )

                messages.success(request, 'Votre demande de devis a été envoyée avec succès!')
                return redirect('quote_confirmation', quote_id=quote.id)
        except ValidationError as e:
            messages.error(request, f"Erreur de validation: {str(e)}")
        except Exception as e:
            messages.error(request, f"Une erreur s'est produite lors de l'envoi de votre demande. Veuillez réessayer.")
            # Log the error for debugging
            print(f"Error in quote_request: {str(e)}")
    else:
        form = QuoteRequestForm()

    return render(request, 'quotes/request_form.html', {'form': form})

def quote_confirmation(request, quote_id):
    quote = get_object_or_404(Quote, id=quote_id)
    return render(request, 'quotes/confirmation.html', {'quote': quote})

def quote_status(request, quote_id):
    quote = get_object_or_404(Quote, id=quote_id)
    updates = quote.status_updates.all().order_by('-created_at')
    return render(request, 'quotes/status.html', {
        'quote': quote,
        'updates': updates
    })


@staff_member_required
def admin_update_status(request, quote_id):
    if request.method == 'POST':
        quote = get_object_or_404(Quote, id=quote_id)
        new_status = request.POST.get('status')
        comment = request.POST.get('comment', '')

        # Atualiza o status
        quote.status = new_status
        quote.save()

        # Cria registro de atualização
        update = QuoteStatusUpdate.objects.create(
            quote=quote,
            status=new_status,
            comment=comment,
            created_by=request.user
        )

        # Envia notificação por email
        context = {
            'name': quote.name,
            'quote_id': quote.id,
            'new_status': quote.get_status_display(),
            'comment': comment,
        }
        html_message = render_to_string('email/status_update.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            'Mise à jour du statut de votre devis',
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [quote.email],
            html_message=html_message
        )

        messages.success(request, 'Status atualizado com sucesso!')
        return redirect('admin:quotes_quote_change', quote_id)

    return redirect('admin:quotes_quote_changelist')
