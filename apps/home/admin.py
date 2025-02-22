from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import AboutUs, Testimonial, GoogleReviewsSettings
from utils.services import GoogleReviewsService

@admin.register(AboutUs)
class AboutUsAdmin(admin.ModelAdmin):
    list_display = ('title',)


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('author_name', 'company', 'rating_stars', 'platform', 'verified', 'featured', 'active')
    list_filter = ('platform', 'rating', 'verified', 'featured', 'active', 'date_posted')
    search_fields = ('author_name', 'author_title', 'company', 'text')
    actions = ['verify_testimonials', 'feature_testimonials', 'unfeature_testimonials']
    
    fieldsets = (
        (None, {
            'fields': ('author_name', 'author_title', 'company', 'rating', 'text')
        }),
        (_('Image'), {
            'fields': ('author_image',)
        }),
        (_('Détails'), {
            'fields': ('platform', 'external_id', 'verified', 'featured', 'active')
        }),
    )

    def get_fields(self, request, obj=None):
        fields = list(super().get_fields(request, obj))
        if obj:  # Se estiver editando
            # Adiciona botão de sincronização
            fields.extend(['_sync_now_button'])  # Usando extend ao invés de +
        return fields

    def rating_stars(self, obj):
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        return format_html('<span style="color: #FFD700;">{}</span>', stars)
    rating_stars.short_description = _('Note')

    def verify_testimonials(self, request, queryset):
        queryset.update(verified=True)
    verify_testimonials.short_description = _('Marquer comme vérifié')

    def feature_testimonials(self, request, queryset):
        queryset.update(featured=True)
    feature_testimonials.short_description = _('Mettre en avant')

    def unfeature_testimonials(self, request, queryset):
        queryset.update(featured=False)
    unfeature_testimonials.short_description = _('Ne plus mettre en avant')

@admin.register(GoogleReviewsSettings)
class GoogleReviewsSettingsAdmin(admin.ModelAdmin):
    list_display = ('place_id', 'last_sync', 'auto_import', 'min_rating')
    
    def has_add_permission(self, request):
        return not GoogleReviewsSettings.objects.exists()

    def response_change(self, request, obj):
        if "_sync-now" in request.POST:
            service = GoogleReviewsService()
            service.sync_reviews()
            self.message_user(request, _("Synchronisation des avis Google terminée."))
            return self.response_post_save_change(request, obj)
        return super().response_change(request, obj)

    def get_fields(self, request, obj=None):
        fields = list(super().get_fields(request, obj))
        if obj:  # Se estiver editando
            fields.extend(['_sync_now_button'])  # Usando extend ao invés de +
        return fields

    def _sync_now_button(self, obj):
        return format_html(
            '<input type="submit" name="_sync-now" value="{}" class="button">',
            _("Synchroniser maintenant")
        )
    _sync_now_button.short_description = ""