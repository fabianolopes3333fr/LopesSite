from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods


# @login_required
@require_http_methods(["GET"])
def dashboard(request):
    context = {
        'user': request.user,
    }
    return render(request, 'dashboard/index.html', context)

# @login_required
@require_http_methods(["GET"])
def user_dashboard(request):
    """
    View para exibir o dashboard do usuário
    """
    user = request.user
    profile = getattr(user, 'profile', None)

    context = {
        'title': _('Tableau de bord'),
        'user': user,
        'profile': profile,
    }

    return render(request, 'dashboard/user_dashboard.html', context)