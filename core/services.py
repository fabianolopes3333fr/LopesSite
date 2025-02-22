# services.py
from django.core.mail import send_mail
from django.conf import settings 
from django.utils.translation import gettext as _
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from apps.users.models import NewsletterSubscription
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator


class NewsletterService:
    @staticmethod
    def send_welcome_email(name, email):
        subject = 'Bienvenue à notre newsletter!'
        message = f'''
        Bonjour {name},
        
        Merci de vous être inscrit à notre newsletter.
        
        Cordialement,
        L'équipe Lopes Peinture
        '''
        
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )

    @staticmethod
    def send_newsletter(subject, content):
        recipients = NewsletterSubscription.objects.filter(
            is_active=True
        ).values_list('email', flat=True)

        for email in recipients:
            send_mail(
                subject,
                content,
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )

class QuoteEmailService:
    @staticmethod
    def send_confirmation(quote):
        """Envia email de confirmação para o cliente"""
        context = {
            'name': quote.name,
            'quote_id': quote.id,
            'quote': quote,
            'status_url': f"{settings.SITE_URL}/quotes/status/{quote.id}/"
        }
        
        html_message = render_to_string('email/confirmation.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            'Confirmation de votre demande de devis',
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [quote.email],
            html_message=html_message
        )

    @staticmethod
    def send_status_update(quote, status_update):
        """Envia notificação de atualização de status"""
        context = {
            'name': quote.name,
            'quote_id': quote.id,
            'new_status': quote.get_status_display(),
            'comment': status_update.comment,
            'status_url': f"{settings.SITE_URL}/quotes/status/{quote.id}/"
        }
        
        html_message = render_to_string('email/status_update.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            'Mise à jour de votre devis',
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [quote.email],
            html_message=html_message
        )
        

    
@staticmethod
def send_verification_email(request, user):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    verification_url = request.build_absolute_uri(f'/verify-email/{uid}/{token}/')

    subject = 'Vérifiez votre adresse e-mail'
    message = render_to_string('email/verification_email.html', {
        'user': user,
        'verification_url': verification_url,
    })

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
        html_message=message,
    )
@staticmethod
def send_password_reset_email(request, user):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    reset_url = request.build_absolute_uri(f'/reset-password/{uid}/{token}/')

    subject = 'Réinitialisation de votre mot de passe'
    message = render_to_string('email/password_reset_email.html', {
        'user': user,
        'reset_url': reset_url,
    })

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
        html_message=message,
    )
        