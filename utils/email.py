# utils/email.py
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
import logging


logger = logging.getLogger('send_new_password_email')
def send_verification_email(request, user):
    """
    Envia email de verificação para o usuário
    """
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    verification_link = request.build_absolute_uri(
        f'/verify-email/{uid}/{token}/'
    )
    
    context = {
        'user': user,
        'verification_link': verification_link,
    }
    
    html_message = render_to_string('emails/verification_email.html', context)
    plain_message = render_to_string('emails/verification_email.txt', context)
    
    send_mail(
        subject='Vérifiez votre compte',
        message=plain_message,
        from_email='noreply@yoursite.com',
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )
    
    
# utils/email.py (adicionar ao existente)
def send_password_reset_email(request, user):
    """
    Envia email de redefinição de senha
    """
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    reset_link = request.build_absolute_uri(
        f'/reset-password/{uid}/{token}/'
    )
    
    context = {
        'user': user,
        'reset_link': reset_link,
    }
    
    html_message = render_to_string('emails/password_reset_email.html', context)
    plain_message = render_to_string('emails/password_reset_email.txt', context)
    
    send_mail(
        subject='Réinitialisation de votre mot de passe',
        message=plain_message,
        from_email='noreply@yoursite.com',
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )
    

def send_new_password_email(user, password):
    """
    Envia email com nova senha para o usuário
    """
    subject = _('Nouveau mot de passe')
    context = {
        'user': user,
        'password': password,
    }
    
    # Renderiza as versões HTML e texto do email
    html_message = render_to_string('emails/new_password_email.html', context)
    plain_message = render_to_string('emails/new_password_email.txt', context)
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        # Log do erro
        logger.error(f"Erreur d'envoi d'e-mail de nouveau mot de passe: {str(e)}")
        return False
class NewsletterService:
    @staticmethod
    def send_welcome_email(name, email):
        """
        Envia email de boas-vindas para novo inscrito
        """
        context = {
            'name': name,
            'unsubscribe_url': f"{settings.SITE_URL}/newsletter/unsubscribe?email={email}"
        }
        
        html_message = render_to_string('emails/newsletter_welcome.html', context)
        plain_message = render_to_string('emails/newsletter_welcome.txt', context)
        
        send_mail(
            subject=_("Bienvenue à notre newsletter !"),
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False
        )