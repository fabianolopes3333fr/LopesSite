# apps/testimonials/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from .models import Testimonial

@receiver(post_save, sender=Testimonial)
def notify_new_testimonial(sender, instance, created, **kwargs):
    if created and instance.platform == 'site':
        # Notifica administradores sobre novo depoimento
        send_mail(
            subject="Nouveau témoignage à valider",
            message=f"Un nouveau témoignage de {instance.author_name} est en attente de validation.",
            from_email=None,
            recipient_list=['admin@example.com']
        )