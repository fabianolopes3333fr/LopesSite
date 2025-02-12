from django.contrib import admin
from .models import AboutUs, Testimonial

@admin.register(AboutUs)
class AboutUsAdmin(admin.ModelAdmin):
    list_display = ('title',)

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('name', 'position')
    search_fields = ('name', 'content')
