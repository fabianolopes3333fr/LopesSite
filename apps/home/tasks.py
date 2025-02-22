# apps/testimonials/tasks.py
from celery import shared_task
from utils.services import GoogleReviewsService

@shared_task
def sync_google_reviews():
    service = GoogleReviewsService()
    return service.sync_reviews()