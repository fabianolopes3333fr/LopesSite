# services.py
from django.core.mail import send_mail
from django.conf import settings 
from apps.users.models import NewsletterSubscription

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