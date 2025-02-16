from django.urls import path
from .views import ColorCatalogView

urlpatterns = [
    path('catalog/', ColorCatalogView.as_view(), name='color_catalog'),
]
