
from django.contrib import admin
from .models import Supplier,Quote ,Paint, PaintVariant, QuoteStatusUpdate, QuotePhoto


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
    
class QuoteStatusUpdateInline(admin.TabularInline):
    model = QuoteStatusUpdate
    extra = 1

@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'email', 'service_type', 'status', 'created_at', 'estimated_price'
    )
    list_filter = ('status', 'service_type', 'created_at')
    search_fields = ('name', 'email', 'phone', 'description')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [QuoteStatusUpdateInline]
    actions = ['mark_as_pending', 'mark_as_approved', 'mark_as_completed']
    
    def mark_as_pending(self, request, queryset):
        queryset.update(status='pending')
    mark_as_pending.short_description = "Marquer comme en attente"

    def mark_as_approved(self, request, queryset):
        queryset.update(status='approved')
    mark_as_approved.short_description = "Marquer comme approuvé"

    def mark_as_completed(self, request, queryset):
        queryset.update(status='completed')
    mark_as_completed.short_description = "Marquer comme terminé"
    
    # fieldsets = (
    #     ('Informations Client', {
    #         'fields': (
    #             'name', 'email', 'phone', 'address', 'postal_code', 'city'
    #         )
    #     }),
    #     ('Détails du Projet', {
    #         'fields': (
    #             'service_type', 'area_size', 'description', 'preferred_date',
    #             'budget_range'
    #         )
    #     }),
    #     ('Gestion', {
    #         'fields': (
    #             'status', 'estimated_price', 'admin_notes',
    #             ('created_at', 'updated_at')
    #         )
    #     })
    # )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if change and 'status' in form.changed_data:
            QuoteStatusUpdate.objects.create(
                quote=obj,
                status=obj.status,
                comment=f"Status updated to {obj.get_status_display()}",
                created_by=request.user
            )
@admin.register(QuoteStatusUpdate)
class QuoteStatusUpdateAdmin(admin.ModelAdmin):
    list_display = ('quote', 'status', 'created_at', 'created_by')
    list_filter = ('status', 'created_at')
    search_fields = ('quote__name', 'quote__email', 'comment')