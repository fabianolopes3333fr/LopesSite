from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(_("Nom"), max_length=100)
    slug = models.SlugField(_("Slug"), unique=True)

    class Meta:
        verbose_name = _("Catégorie")
        verbose_name_plural = _("Catégories")

    def __str__(self):
        return self.name

class Post(models.Model):
    title = models.CharField(_("Titre"), max_length=200)
    slug = models.SlugField(_("Slug"), unique=True)
    content = models.TextField(_("Contenu"))
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    categories = models.ManyToManyField(Category, related_name="posts")
    image = models.ImageField(_("Image"), upload_to="blog/")
    created_at = models.DateTimeField(_("Date de création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de mise à jour"), auto_now=True)

    class Meta:
        verbose_name = _("Article")
        verbose_name_plural = _("Articles")

    def __str__(self):
        return self.title

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    name = models.CharField(_("Nom"), max_length=100)
    email = models.EmailField(_("Email"))
    content = models.TextField(_("Commentaire"))
    created_at = models.DateTimeField(_("Date de création"), auto_now_add=True)

    class Meta:
        verbose_name = _("Commentaire")
        verbose_name_plural = _("Commentaires")

    def __str__(self):
        return f"Commentaire par {self.name} sur {self.post.title}"
