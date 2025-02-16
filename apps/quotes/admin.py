
from django.contrib import admin
from .models import Supplier,Quote ,Paint, PaintVariant


class PaintVariantInline(admin.TabularInline):  # ou admin.StackedInline
    model = PaintVariant
    extra = 1  # Número de formulários vazios extras para adicionar
    fields = ['color_code', 'color_name', 'size', 'price_adjustment', 'stock_quantity', 'image']

@admin.register(Paint)
class PaintAdmin(admin.ModelAdmin):
    list_display = ('name', 'supplier', 'category', 'base_price', 'stock_quantity', 'is_active')
    list_filter = ('is_active', 'category', 'supplier', 'finish')
    search_fields = ('name', 'description', 'sku')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [PaintVariantInline]

@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ('name', 'service', 'area', 'status', 'created_at')
    list_filter = ('service', 'status', 'created_at')
    search_fields = ('name', 'email', 'service', 'details')
    readonly_fields = ('created_at',)
