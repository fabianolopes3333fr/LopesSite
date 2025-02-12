from django.contrib import admin
from .models import Color, ColorCombination

@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ('name', 'hex_code')
    search_fields = ('name', 'hex_code')

@admin.register(ColorCombination)
class ColorCombinationAdmin(admin.ModelAdmin):
    list_display = ('name',)
    filter_horizontal = ('colors',)
    search_fields = ('name', 'description')
