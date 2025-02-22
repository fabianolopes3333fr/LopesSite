# apps/testimonials/services.py
import requests
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from apps.home.models import Testimonial, GoogleReviewsSettings
import logging

# Configurar o logger
logger = logging.getLogger('testimonials')

class GoogleReviewsService:
    def __init__(self):
        try:
            self.settings = GoogleReviewsSettings.objects.first()
            if not self.settings:
                raise ValueError("Configurations Google Reviews non trouvées")
        except Exception as e:
            logger.error(f"Erreur d'initialisation GoogleReviewsService: {str(e)}")
            self.settings = None

    def sync_reviews(self):
        """Sincroniza reviews do Google"""
        if not self.settings:
            logger.error("Impossible de synchroniser: configurations non trouvées")
            return False

        try:
            url = "https://maps.googleapis.com/maps/api/place/details/json"
            params = {
                'place_id': self.settings.place_id,
                'fields': 'reviews',
                'key': self.settings.api_key
            }

            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if 'result' in data and 'reviews' in data['result']:
                self._process_reviews(data['result']['reviews'])
                
                # Atualizar última sincronização
                if self.settings:
                    self.settings.last_sync = timezone.now()
                    self.settings.save()
                
                return True
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur de requête API Google: {str(e)}")
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation: {str(e)}")
        
        return False

    def _process_reviews(self, reviews):
        """Processa os reviews recebidos"""
        if not self.settings:
            return

        min_rating = getattr(self.settings, 'min_rating', 4)  # Valor padrão 4 se não definido

        for review in reviews:
            try:
                if review['rating'] < min_rating:
                    continue

                Testimonial.objects.update_or_create(
                    platform='google',
                    external_id=review['time'],
                    defaults={
                        'author_name': review['author_name'],
                        'author_image': review.get('profile_photo_url', ''),
                        'rating': review['rating'],
                        'text': review['text'],
                        'date_posted': datetime.fromtimestamp(review['time']),
                        'verified': True,
                        'active': True
                    }
                )
            except Exception as e:
                logger.error(f"Erreur lors du traitement d'un avis: {str(e)}")