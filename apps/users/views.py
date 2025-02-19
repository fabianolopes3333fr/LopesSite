from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from .forms import CustomUserCreationForm
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.http import JsonResponse
from core.services import NewsletterService
from .models import NewsletterSubscription
from django.contrib.auth.models import Group

def logout_view(request):
    logout(request)
    return redirect('home')

def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.is_valid = False
            user.is_active = False
            user.save()
            
            group = Group.objects.get(name='utilisateur')
            user.groups.add(group)
            
            login(request, user)
            messages.success(request, "Registration successful.")
            return redirect('home')
        messages.error(request, "Unsuccessful registration. Invalid information.")
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"You are now logged in as {email}.")
                return redirect('home')
            else:
                messages.error(request,"Invalid username or password.")
        else:
            messages.error(request,"Invalid username or password.")
    form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form})

def profile(request):
    return render(request, 'users/profile.html')


# class SignUpView(CreateView):
#     form_class = CustomUserCreationForm
#     success_url = reverse_lazy('login')
#     template_name = 'registration/register.html'



# newsletter signup view

def newsletter_signup(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')

        try:
            # Verifica se já existe
            if NewsletterSubscription.objects.filter(email=email).exists():
                return JsonResponse({
                    'status': 'error',
                    'message': 'Cet email est déjà inscrit.'
                })

            # Salva no banco
            subscription = NewsletterSubscription.objects.create(
                name=name,
                email=email
            )

            # Envia email de boas-vindas
            NewsletterService.send_welcome_email(name, email)

            return JsonResponse({
                'status': 'success',
                'message': 'Inscription réussie!'
            })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': 'Une erreur est survenue.'
            })

    return JsonResponse({
        'status': 'error',
        'message': 'Méthode non autorisée'
    })