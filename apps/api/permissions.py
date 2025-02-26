from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permite acesso de escrita apenas para administradores.
    """

    def has_permission(self, request, view):
        # Permite acesso de leitura para todos
        if request.method in permissions.SAFE_METHODS:
            return True

        # Permite acesso de escrita apenas para administradores
        return request.user and request.user.is_staff


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permite acesso de escrita apenas para o proprietário do objeto.
    """

    def has_object_permission(self, request, view, obj):
        # Permite acesso de leitura para todos
        if request.method in permissions.SAFE_METHODS:
            return True

        # Permite acesso de escrita para administradores
        if request.user and request.user.is_staff:
            return True

        # Verifica se o objeto tem um atributo 'created_by'
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
        return False


class CanPublishPage(permissions.BasePermission):
    """
    Permite publicar uma página apenas para usuários com permissão específica.
    """

    def has_permission(self, request, view):
        return request.user and (
            request.user.is_staff or 
            request.user.has_perm('pages.publish_page')
        )
        
class CanManageWidgets(permissions.BasePermission):
    """
    Permite gerenciar widgets apenas para usuários com permissão específica.
    """
    
    def has_permission(self, request, view):
        return request.user and (
            request.user.is_staff or 
            request.user.has_perm('widgets.manage_widgets')
        )
        
class CanManageSiteSettings(permissions.BasePermission):
    """
    Permite gerenciar configurações do site apenas para usuários com permissão específica.
    """
    
    def has_permission(self, request, view):
        return request.user and (
            request.user.is_staff or 
            request.user.has_perm('config.manage_site_settings')
        )
        
class CanManagePageRevisions(permissions.BasePermission):
    """
    Permite gerenciar revisões de página apenas para usuários com permissão específica.
    """
    
    def has_permission(self, request, view):
        return request.user and (
            request.user.is_staff or 
            request.user.has_perm('pages.manage_page_revisions')
        )