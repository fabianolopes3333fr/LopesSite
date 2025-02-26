from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import CDNProvider, CDNFile
from .forms import CDNProviderForm, CDNFileForm

@login_required
def cdn_provider_list(request):
    providers = CDNProvider.objects.all()
    return render(request, 'cdn/provider_list.html', {'providers': providers})

@login_required
def cdn_provider_detail(request, pk):
    provider = get_object_or_404(CDNProvider, pk=pk)
    return render(request, 'cdn/provider_detail.html', {'provider': provider})

@login_required
def cdn_provider_create(request):
    if request.method == 'POST':
        form = CDNProviderForm(request.POST)
        if form.is_valid():
            provider = form.save()
            messages.success(request, 'CDN Provider created successfully.')
            return redirect('cdn_provider_detail', pk=provider.pk)
    else:
        form = CDNProviderForm()
    return render(request, 'cdn/provider_form.html', {'form': form})

@login_required
def cdn_provider_update(request, pk):
    provider = get_object_or_404(CDNProvider, pk=pk)
    if request.method == 'POST':
        form = CDNProviderForm(request.POST, instance=provider)
        if form.is_valid():
            form.save()
            messages.success(request, 'CDN Provider updated successfully.')
            return redirect('cdn_provider_detail', pk=provider.pk)
    else:
        form = CDNProviderForm(instance=provider)
    return render(request, 'cdn/provider_form.html', {'form': form, 'provider': provider})

@login_required
def cdn_provider_delete(request, pk):
    provider = get_object_or_404(CDNProvider, pk=pk)
    if request.method == 'POST':
        provider.delete()
        messages.success(request, 'CDN Provider deleted successfully.')
        return redirect('cdn_provider_list')
    return render(request, 'cdn/provider_confirm_delete.html', {'provider': provider})

@login_required
def cdn_file_list(request):
    files = CDNFile.objects.all().order_by('-created_at')
    paginator = Paginator(files, 20)  # Show 20 files per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'cdn/file_list.html', {'page_obj': page_obj})

@login_required
def cdn_file_detail(request, pk):
    cdn_file = get_object_or_404(CDNFile, pk=pk)
    return render(request, 'cdn/file_detail.html', {'cdn_file': cdn_file})

@login_required
def cdn_file_upload(request):
    if request.method == 'POST':
        form = CDNFileForm(request.POST, request.FILES)
        if form.is_valid():
            cdn_file = form.save()
            messages.success(request, 'File uploaded successfully.')
            return redirect('cdn_file_detail', pk=cdn_file.pk)
    else:
        form = CDNFileForm()
    return render(request, 'cdn/file_upload.html', {'form': form})

@login_required
def cdn_file_delete(request, pk):
    cdn_file = get_object_or_404(CDNFile, pk=pk)
    if request.method == 'POST':
        cdn_file.delete()
        messages.success(request, 'File deleted successfully.')
        return redirect('cdn_file_list')
    return render(request, 'cdn/file_confirm_delete.html', {'cdn_file': cdn_file})

@login_required
def invalidate_cache(request, pk):
    provider = get_object_or_404(CDNProvider, pk=pk)
    if request.method == 'POST':
        paths = request.POST.getlist('paths')
        success = provider.invalidate_cache(paths)
        if success:
            messages.success(request, 'Cache invalidation request sent successfully.')
        else:
            messages.error(request, 'Failed to send cache invalidation request.')
        return redirect('cdn_provider_detail', pk=provider.pk)
    return render(request, 'cdn/invalidate_cache.html', {'provider': provider})

def cdn_file_url(request, pk):
    cdn_file = get_object_or_404(CDNFile, pk=pk)
    return JsonResponse({'url': cdn_file.get_absolute_url()})