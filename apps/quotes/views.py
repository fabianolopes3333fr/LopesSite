from django.shortcuts import render, redirect
from .forms import QuoteForm  # Alterado de QuoteRequestForm para QuoteForm
from django.contrib import messages

def request_quote(request):
    if request.method == 'POST':
        form = QuoteForm(request.POST)  # Alterado de QuoteRequestForm para QuoteForm
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre demande de devis a été envoyée avec succès!')
            return redirect('home')
    else:
        form = QuoteForm()  # Alterado de QuoteRequestForm para QuoteForm
    return render(request, 'quotes/request_quote.html', {'form': form})

