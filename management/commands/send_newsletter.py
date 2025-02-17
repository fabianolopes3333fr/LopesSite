from django.core.management.base import BaseCommand
from core.services import NewsletterService

class Command(BaseCommand):
    help = 'Envia newsletter para todos os inscritos'

    def add_arguments(self, parser):
        parser.add_argument('subject', type=str)
        parser.add_argument('content', type=str)

    def handle(self, *args, **options):
        subject = options['subject']
        content = options['content']
        
        NewsletterService.send_newsletter(subject, content)
        
        self.stdout.write(
            self.style.SUCCESS('Newsletter enviada com sucesso!')
        )
        
        # Para enviar a newsletter, execute o comando abaixo:
        # python manage.py send_newsletter "Novidades de Junho" "Confira nossas ofertas..."