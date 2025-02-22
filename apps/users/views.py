import logging
import time
from django.contrib import messages
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.shortcuts import render, redirect
from django.utils.timezone import datetime
from django.utils.translation import gettext as _
from django.contrib.auth import login, logout
from typing import cast
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.http import urlsafe_base64_decode
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.encoding import  force_str
from django.contrib.auth.tokens import default_token_generator
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from utils.validators import validate_password_strength
from utils.email import send_verification_email, send_password_reset_email
from utils.email import NewsletterService
from django.core.validators import EmailValidator
from .models import NewsletterSubscription, CustomUser, ClientProfile
from .forms import (
    CustomUserCreationForm, 
    CustomUserChangeForm, 
    CustomUserProfileForm,
    CustomAuthenticationForm, 
    PasswordResetForm, 
    SetPasswordForm, 
    TwoFactorAuthForm
)
logger = logging.getLogger('registration')
@never_cache
@require_http_methods(["GET", "POST"])
def logout_view(request):
    """
    View para realizar o logout do usuário
    """
    if request.user.is_authenticated:
        # Adiciona mensagem de sucesso
        messages.success(request, _("Vous avez été déconnecté avec succès."))
        # Realiza o logout
        logout(request)
    
    return redirect('login')
def register(request):
    """
    View para registro de novos usuários com validações e proteções
    """
    # Verifica se o usuário já está logado
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    # Proteção contra spam de registro
    if request.method == 'POST':
        client_ip = request.META.get('REMOTE_ADDR')
        registration_attempts = cache.get(f'registration_attempts_{client_ip}', 0)
        
        if registration_attempts > 5:
            messages.error(
                request, 
                _("Trop de tentatives d'inscription. Veuillez réessayer dans une heure.")
            )
            return redirect('register')
        
        cache.set(f'registration_attempts_{client_ip}', registration_attempts + 1, 3600)
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # Verifica se o email já existe
            email = form.cleaned_data['email']
            if CustomUser.objects.filter(email=email).exists():
                messages.error(request, _("Cet e-mail est déjà utilisé."))
                return render(request, 'registration/register.html', {'form': form})
            
            try:
                # Criar usuário
                user = form.save(commit=False)
                user.is_active = False
                
                # Validar senha
                try:
                    validate_password_strength(form.cleaned_data['password1'])
                except ValidationError as e:
                    for error in e.messages:
                        messages.error(request, error)
                    return render(request, 'registration/register.html', {'form': form})
                
                # Salvar usuário
                user.save()
                
                # Adicionar ao grupo de clientes
                client_group, created = Group.objects.get_or_create(
                    name='Clientes',
                    defaults={
                        'name': 'Clientes',
                    }
                )
                user.groups.add(client_group)
                
                # Enviar email de verificação
                try:
                    send_verification_email(request, user)
                except Exception as e:
                    logger.error(f"Erreur d'envoi d'e-mail de vérification: {str(e)}")
                    messages.warning(
                        request,
                        _("Votre compte a été créé, mais l'envoi de l'e-mail de vérification a échoué. "
                          "Veuillez contacter le support.")
                    )
                else:
                    messages.success(
                        request,
                        _("Inscription réussie! Veuillez vérifier votre e-mail pour activer votre compte.")
                    )
                
                return redirect('login')
                
            except Exception as e:
                logger.error(f"Erreur lors de la création du compte: {str(e)}")
                messages.error(
                    request,
                    _("Une erreur s'est produite lors de l'inscription. Veuillez réessayer.")
                )
        else:
            # Mensagens de erro específicas para cada campo
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/register.html', {
        'form': form,
        'title': _('Inscription')
    })

logger = logging.getLogger('authentication')

def user_login(request):
    """
    View para autenticação de usuários com proteções de segurança
    """
    # Proteção contra múltiplas tentativas
    client_ip = request.META.get('REMOTE_ADDR')
    login_attempts = cast(int, cache.get(f'login_attempts_{client_ip}', 0))
    
    if login_attempts > 10:  # Limite de 10 tentativas por hora
        messages.error(
            request, 
            _("Trop de tentatives de connexion. Veuillez réessayer dans une heure.")
        )
        return redirect('login')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        
        # Incrementa tentativas de login
        cache.set(f'login_attempts_{client_ip}', login_attempts + 1, 3600)  # 1 hora
        
        if form.is_valid():
            user = cast(CustomUser, form.get_user())
            
            # Verificação de conta bloqueada
            if user.account_locked:
                logger.warning(f"Tentative de connexion sur un compte verrouillé: {user.email}")
                messages.error(
                    request, 
                    _("Votre compte est verrouillé. Contactez l'administrateur pour résoudre ce problème.")
                )
                return render(request, 'registration/login.html', {
                    'form': form,
                    'title': _('Connexion')
                })
            
            # Verificação de autenticação de dois fatores
            if user.two_factor_enabled:
                request.session['user_id'] = user.pk
                request.session['two_factor_auth_timestamp'] = str(datetime.now())
                return redirect('two_factor_auth')
            
            try:
                # Login bem-sucedido
                login(request, user)
                user.reset_failed_login_attempts()
                
                # Limpa cache de tentativas para este IP
                cache.delete(f'login_attempts_{client_ip}')
                
                # Log de sucesso
                logger.info(f"Connexion réussie: {user.email}")
                
                return redirect('home')
                
            except Exception as e:
                logger.error(f"Erreur lors de la connexion: {str(e)}")
                messages.error(
                    request,
                    _("Une erreur s'est produite. Veuillez réessayer.")
                )
        
        else:
            # Tratamento de tentativa de login falha
            email = request.POST.get('username')
            if email:
                try:
                    user = CustomUser.objects.get(email=email)
                    user.increment_failed_login_attempts()
                    
                    # Log de tentativa falha
                    logger.warning(f"Échec de connexion pour: {email}")
                    
                    # Mensagens baseadas no número de tentativas
                    if user.failed_login_attempts >= 3:
                        messages.warning(
                            request, 
                            _("Attention: Plusieurs tentatives de connexion échouées. "
                              "Votre compte sera verrouillé après 5 tentatives.")
                        )
                    if user.failed_login_attempts >= 5:
                        user.account_locked = True
                        user.save()
                        messages.error(
                            request,
                            _("Compte verrouillé par mesure de sécurité. "
                              "Veuillez contacter l'administrateur.")
                        )
                        
                except CustomUser.DoesNotExist:
                    # Não revela se o usuário existe ou não
                    # Atraso artificial para prevenir enumeração de usuários
                    import time
                    time.sleep(1)
                    pass
            
            messages.error(request, _("Email ou mot de passe incorrect."))
    
    else:            
        form = CustomAuthenticationForm()
    
    return render(request, 'registration/login.html', {
        'form': form,
        'title': _('Connexion')
    })

def two_factor_auth(request):
    # Verifica se temos um user_id na sessão
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    
    try:
        user = CustomUser.objects.get(pk=user_id)
    except CustomUser.DoesNotExist:
        return redirect('login')

    if request.method == 'POST':
        form = TwoFactorAuthForm(request.POST)
        if form.is_valid():
            token = form.cleaned_data['token']
            
            if user.verify_2fa(token):
                # Autenticação bem sucedida
                login(request, user)
                # Limpa o user_id da sessão
                del request.session['user_id']
                return redirect('home')
            else:
                messages.error(request, _("Code de vérification invalide."))
    else:
        form = TwoFactorAuthForm()

    return render(request, 'registration/two_factor_auth.html', {'form': form})


@login_required
@require_http_methods(["GET", "POST"])
def profile(request):
    """
    View para gerenciar perfil do usuário e seus dados adicionais
    """
    user = request.user
    # Obtém ou cria o perfil do usuário
    profile, created = ClientProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        user_form = CustomUserChangeForm(request.POST, instance=user)
        profile_form = CustomUserProfileForm(request.POST, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            try:
                user = user_form.save(commit=False)
                
                # Verifica se o email foi alterado
                if user.has_changed('email'):
                    user.email_verified = False
                    # Limpa cache relacionado ao usuário
                    cache.delete(f'login_attempts_{user.pk}')
                    cache.delete(f'reset_attempts_{user.pk}')
                
                user.save()
                profile_form.save()
                
                logger.info(f"Profil mis à jour pour l'utilisateur: {user.email}")
                messages.success(
                    request, 
                    _("Votre profil a été mis à jour avec succès.")
                )
                
                return redirect('profile')
                
            except Exception as e:
                logger.error(f"Erreur lors de la mise à jour du profil: {str(e)}")
                messages.error(
                    request, 
                    _("Une erreur s'est produite lors de la mise à jour de votre profil. "
                      "Veuillez réessayer.")
                )
        else:
            # Tratamento de erros do formulário do usuário
            for field, errors in user_form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            
            # Tratamento de erros do formulário do perfil
            for field, errors in profile_form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    
    else:
        user_form = CustomUserChangeForm(instance=user)
        profile_form = CustomUserProfileForm(instance=profile)
    
    return render(request, 'registration/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'title': _('Mon Profil'),
        'user': user
    })


@never_cache
@require_http_methods(["GET", "POST"])
def password_reset_request(request):
    """
    View para solicitar redefinição de senha com proteções contra ataques
    """
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            
            # Proteção contra força bruta
            client_ip = request.META.get('REMOTE_ADDR')
            reset_attempts = cache.get(f'reset_attempts_{client_ip}', 0)
            
            if reset_attempts > 3:
                logger.warning(f"Trop de tentatives de réinitialisation depuis IP: {client_ip}")
                messages.error(
                    request, 
                    _("Trop de tentatives. Veuillez réessayer dans une heure.")
                )
                return redirect('password_reset')
                
            cache.set(f'reset_attempts_{client_ip}', reset_attempts + 1, 3600)  # 1 hora
            
            try:
                user = CustomUser.objects.get(email=email)
                
                # Verifica reset pendente
                reset_key = f'password_reset_{user.pk}'
                if cache.get(reset_key):
                    logger.info(f"Tentative de réinitialisation multiple pour: {email}")
                    messages.info(
                        request, 
                        _("Un e-mail de réinitialisation a déjà été envoyé. "
                          "Veuillez attendre quelques minutes avant de réessayer.")
                    )
                    return redirect('login')
                
                try:
                    # Envia email de reset
                    send_password_reset_email(request, user)
                    cache.set(reset_key, True, 300)  # 5 minutos
                    
                    logger.info(f"E-mail de réinitialisation envoyé à: {email}")
                    messages.success(
                        request, 
                        _("Les instructions de réinitialisation du mot de passe "
                          "ont été envoyées à votre adresse e-mail.")
                    )
                    return redirect('login')
                    
                except Exception as e:
                    logger.error(f"Erreur d'envoi d'e-mail de réinitialisation: {str(e)}")
                    messages.error(
                        request, 
                        _("Une erreur s'est produite lors de l'envoi de l'e-mail. "
                          "Veuillez réessayer plus tard.")
                    )
                    
            except CustomUser.DoesNotExist:
                # Prevenção contra enumeração de usuários
                logger.info(f"Tentative de réinitialisation pour email inexistant: {email}")
                time.sleep(1)  # Atraso artificial
                messages.success(
                    request, 
                    _("Si un compte existe avec cette adresse e-mail, "
                      "vous recevrez les instructions de réinitialisation.")
                )
                return redirect('login')
    else:
        form = PasswordResetForm()
    
    return render(request, 'registration/password_reset_form.html', {
        'form': form,
        'title': _('Réinitialisation du mot de passe')
    })

@never_cache
@require_http_methods(["GET", "POST"])
def password_reset_confirm(request, uidb64, token):
    """
    View para confirmar token e permitir que o usuário defina uma nova senha
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None
        logger.warning(f"Tentative de réinitialisation invalide: uidb64={uidb64}")
    
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                try:
                    # Validar força da senha
                    password = form.cleaned_data['new_password1']
                    validate_password_strength(password)
                    
                    # Salvar nova senha
                    form.save()
                    
                    # Resetar estado do usuário
                    user.failed_login_attempts = 0
                    user.account_locked = False
                    user.last_failed_login = None
                    user.save()
                    
                    # Limpar caches relacionados
                    cache.delete(f'password_reset_{user.pk}')
                    cache.delete(f'login_attempts_{user.pk}')
                    
                    logger.info(f"Réinitialisation du mot de passe réussie pour: {user.email}")
                    messages.success(
                        request, 
                        _("Votre mot de passe a été réinitialisé avec succès. "
                          "Vous pouvez maintenant vous connecter avec votre nouveau mot de passe.")
                    )
                    return redirect('login')
                    
                except ValidationError as e:
                    logger.warning(f"Erreur de validation du mot de passe pour: {user.email}")
                    for error in e.messages:
                        messages.error(request, error)
                        
                except Exception as e:
                    logger.error(f"Erreur lors de la réinitialisation du mot de passe: {str(e)}")
                    messages.error(
                        request, 
                        _("Une erreur s'est produite lors de la réinitialisation. "
                          "Veuillez réessayer ou contacter le support.")
                    )
        else:
            form = SetPasswordForm(user)
        
        return render(request, 'registration/password_reset_confirm.html', {
            'form': form,
            'title': _('Nouveau mot de passe'),
            'validlink': True
        })
    else:
        logger.warning(
            f"Tentative de réinitialisation avec token invalide ou expiré: "
            f"uidb64={uidb64}, token={token}"
        )
        messages.error(
            request, 
            _("Le lien de réinitialisation du mot de passe est invalide ou a expiré. "
              "Veuillez faire une nouvelle demande de réinitialisation.")
        )
        return redirect('password_reset')



# newsletter signup view
logger = logging.getLogger('newsletter')
@ensure_csrf_cookie
@require_http_methods(["POST"])
def newsletter_signup(request):
    """
    View para cadastro na newsletter com proteções contra spam
    """
    try:
        # Proteção contra múltiplas tentativas
        client_ip = request.META.get('REMOTE_ADDR')
        signup_attempts = cache.get(f'newsletter_signup_{client_ip}', 0)
        
        if signup_attempts > 5:  # Limite de 5 tentativas por hora
            logger.warning(f"Trop de tentatives d'inscription depuis IP: {client_ip}")
            return JsonResponse({
                'status': 'error',
                'message': _("Trop de tentatives. Veuillez réessayer plus tard.")
            }, status=429)
            
        cache.set(f'newsletter_signup_{client_ip}', signup_attempts + 1, 3600)

        # Validação dos campos
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip().lower()

        if not name or not email:
            return JsonResponse({
                'status': 'error',
                'message': _("Le nom et l'email sont requis.")
            }, status=400)

        # Validação de email
        try:
            validator = EmailValidator(message=_("Adresse e-mail invalide."))
            validator(email)
        except ValidationError as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

        # Verifica se já existe
        if NewsletterSubscription.objects.filter(email=email).exists():
            logger.info(f"Tentative d'inscription avec email existant: {email}")
            return JsonResponse({
                'status': 'error',
                'message': _("Cette adresse e-mail est déjà inscrite à notre newsletter.")
            }, status=400)

        # Salva no banco
        subscription = NewsletterSubscription.objects.create(
            name=name,
            email=email
        )
        
        try:
            # Envia email de boas-vindas
            NewsletterService.send_welcome_email(name, email)
            logger.info(f"Nouvelle inscription newsletter: {email}")
            
            return JsonResponse({
                'status': 'success',
                'message': _("Inscription réussie ! Vous allez recevoir un e-mail de confirmation.")
            }, status=201)
            
        except Exception as e:
            logger.error(f"Erreur d'envoi d'e-mail de bienvenue: {str(e)}")
            # Remove a inscrição se o email falhar
            subscription.delete()
            raise

    except Exception as e:
        logger.error(f"Erreur lors de l'inscription à la newsletter: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': _("Une erreur est survenue. Veuillez réessayer plus tard.")
        }, status=500)