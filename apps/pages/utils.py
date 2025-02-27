from django.utils.translation import gettext_lazy as _

def get_seo_suggestions(page):
    """
    Gera sugestões de otimização SEO para uma página.
    """
    suggestions = []

    if not page.meta_title:
        suggestions.append(_("Add a meta title to improve search engine visibility."))
    elif len(page.meta_title) < 30:
        suggestions.append(_("Your meta title is too short. Aim for 50-60 characters."))

    if not page.meta_description:
        suggestions.append(_("Add a meta description to improve click-through rates from search results."))
    elif len(page.meta_description) < 100:
        suggestions.append(_("Your meta description is too short. Aim for 150-160 characters."))

    if not page.meta_keywords:
        suggestions.append(_("Consider adding meta keywords to help with content categorization."))

    if not page.og_image:
        suggestions.append(_("Add an Open Graph image to improve social media sharing appearance."))

    # Adicione mais sugestões conforme necessário

    return suggestions