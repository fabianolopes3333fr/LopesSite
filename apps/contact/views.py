from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.contrib import messages
from django.utils.translation import gettext as _
from .forms import ContactForm
from .models import CompanyInfo

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact_message = form.save()

            # Enviar e-mail de confirmação
            send_mail(
                _('Confirmation de votre message'),
                _('Merci pour votre message. Nous vous répondrons dans les plus brefs délais.'),
                'noreply@lopespeinture.fr',
                [contact_message.email],
                fail_silently=False,
            )

            messages.success(request, _('Votre message a été envoyé avec succès. Nous vous contacterons bientôt.'))
            return redirect('contact')
    else:
        form = ContactForm()

    company_info = CompanyInfo.objects.first()

    context = {
        'form': form,
        'company_info': company_info,
    }
    return render(request, 'contact/contact.html', context)
