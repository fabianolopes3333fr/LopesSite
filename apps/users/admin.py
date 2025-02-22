from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, NewsletterSubscription, ClientProfile
from django.utils.translation import gettext_lazy as _


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = (
        'email', 
        'first_name', 
        'last_name', 
        'is_staff', 
        'is_contractor',
        'account_locked',
        'email_verified',
        'two_factor_enabled',
        'get_groups'
    )
    
    list_filter = (
        'is_staff', 
        'is_contractor',
        'account_locked',
        'email_verified',
        'two_factor_enabled',
        'groups',
        'date_joined'
    )
    
    fieldsets = (
        (None, {
            'fields': ('email', 'password')
        }),
        (_('Informations personnelles'), {
            'fields': ('first_name', 'last_name')
        }),
        (_('Permissions'), {
            'fields': (
                'is_staff',
                'is_active',
                'is_superuser',
                'groups',
                'user_permissions'
            )
        }),
        (_('Dates importantes'), {
            'fields': ('last_login', 'date_joined')
        }),
        (_('Informations entrepreneur'), {
            'fields': ('is_contractor', 'company_name')
        }),
        (_('Statut du compte'), {
            'fields': (
                'account_locked',
                'email_verified',
                'two_factor_enabled',
                'failed_login_attempts',
                'last_failed_login'
            )
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'first_name',
                'last_name',
                'password1',
                'password2',
                'is_staff',
                'is_active',
                'is_superuser',
                'groups',
                'user_permissions',
                'is_contractor',
                'company_name'
            )
        }),
    )
    
    search_fields = ('email', 'first_name', 'last_name', 'company_name')
    ordering = ('email',)
    readonly_fields = ('last_login', 'date_joined', 'failed_login_attempts', 'last_failed_login')
    
    def get_groups(self, obj):
        """Retorna os grupos do usuário em formato string"""
        return ", ".join([group.name for group in obj.groups.all()])
    get_groups.short_description = _('Groupes')
    
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(self.readonly_fields)
        if obj:  # Se estiver editando um usuário existente
            readonly_fields.append('email')
        return tuple(readonly_fields)

    actions = ['unlock_accounts', 'lock_accounts', 'reset_failed_attempts']

    def unlock_accounts(self, request, queryset):
        """Desbloqueia as contas selecionadas"""
        queryset.update(account_locked=False, failed_login_attempts=0)
        self.message_user(request, _("Les comptes sélectionnés ont été débloqués."))
    unlock_accounts.short_description = _("Débloquer les comptes sélectionnés")

    def lock_accounts(self, request, queryset):
        """Bloqueia as contas selecionadas"""
        queryset.update(account_locked=True)
        self.message_user(request, _("Les comptes sélectionnés ont été bloqués."))
    lock_accounts.short_description = _("Bloquer les comptes sélectionnés")

    def reset_failed_attempts(self, request, queryset):
        """Reseta as tentativas de login falhas"""
        queryset.update(failed_login_attempts=0)
        self.message_user(request, _("Les tentatives de connexion ont été réinitialisées."))
    reset_failed_attempts.short_description = _("Réinitialiser les tentatives de connexion")


@admin.register(NewsletterSubscription)
class NewsletterSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('email', 'name', 'is_active', 'subscribed_at', 'get_status')
    list_filter = ('is_active', 'subscribed_at')
    search_fields = ('email', 'name')
    ordering = ('-subscribed_at',)
    
    readonly_fields = ('subscribed_at',)
    
    fieldsets = (
        (None, {
            'fields': ('email', 'name')
        }),
        (_('Statut'), {
            'fields': ('is_active', 'subscribed_at')
        }),
    )

    def get_status(self, obj):
        return obj.is_active
    get_status.short_description = _('Statut')
    get_status.boolean = True
    
    actions = ['activate_subscriptions', 'deactivate_subscriptions']

    def activate_subscriptions(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, _("Les abonnements sélectionnés ont été activés."))
    activate_subscriptions.short_description = _("Activer les abonnements sélectionnés")

    def deactivate_subscriptions(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, _("Les abonnements sélectionnés ont été désactivés."))
    deactivate_subscriptions.short_description = _("Désactiver les abonnements sélectionnés")

    def get_readonly_fields(self, request, obj=None):
        """Torna o email readonly após a criação"""
        if obj:  # Se estiver editando um objeto existente
            return list(self.readonly_fields) + ['email']
        return list(self.readonly_fields)
    
    
@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'city', 'postal_code', 'get_email')
    list_filter = ('city', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'phone_number', 'city')
    ordering = ('-created_at',)
    
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('user', 'phone_number')
        }),
        (_('Adresse'), {
            'fields': ('address', 'postal_code', 'city')
        }),
        (_('Informations système'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = _('Email')
    get_email.admin_order_field = 'user__email'

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editando
            return list(self.readonly_fields) + ['user']
        return self.readonly_fields
    
admin.site.register(CustomUser, CustomUserAdmin)
#admin.site.register(Group)
