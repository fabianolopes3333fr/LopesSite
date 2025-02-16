from django.views.generic import ListView
from django.db.models import Q
from .models import Color, ColorCombination
from .forms import ColorFilterForm

class ColorCatalogView(ListView):
    model = Color
    template_name = 'colors/color_catalog.html'
    context_object_name = 'colors'
    paginate_by = 16

    def get_queryset(self):
        queryset = super().get_queryset()
        form = ColorFilterForm(self.request.GET)

        if form.is_valid():
            color_type = form.cleaned_data['color_type']
            search = form.cleaned_data['search']

            if color_type and color_type != 'all':
                queryset = queryset.filter(color_type=color_type)

            if search:
                queryset = queryset.filter(Q(name__icontains=search) | Q(hex_code__icontains=search))

        return queryset
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ColorFilterForm(self.request.GET)
        context['combinations'] = ColorCombination.objects.all()[:5]  # Get 5 random combinations
        return context

