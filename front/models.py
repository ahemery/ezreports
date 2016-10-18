from __future__ import unicode_literals

from django.db import models
from django.template.defaultfilters import slugify


class Editeur(models.Model):
    id = models.AutoField(primary_key=True)
    libelle = models.CharField(max_length=250, null=False, unique=True)
    slug = models.SlugField(unique=True)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.libelle)
        super(Editeur, self).save(*args, **kwargs)

    @models.permalink
    def get_absolute_url(self):
        return 'editeur', [self.slug]

    def __str__(self):
        return self.libelle

    class Meta:
        db_table = "editeurs"


class Ressource(models.Model):
    id = models.AutoField(primary_key=True)
    libelle = models.CharField(max_length=250, null=False, unique=True)
    slug = models.SlugField(unique=True)
    editeur = models.ForeignKey(Editeur, null=True, default=None)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.libelle)
        super(Ressource, self).save(*args, **kwargs)

    @models.permalink
    def get_absolute_url(self):
        return 'ressource', [self.slug]

    def __str__(self):
        return self.slug

    class Meta:
        db_table = "ressources"


class Lien(models.Model):
    id = models.AutoField(primary_key=True)
    url = models.CharField(max_length=250, null=False, unique=True)
    # editeur = models.ForeignKey(Editeur, null=True, default=None)
    ressource = models.ForeignKey(Ressource, null=True, default=None)
    slug = models.SlugField(unique=True)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.url)
        super(Lien, self).save(*args, **kwargs)

    @models.permalink
    def get_absolute_url(self):
        return 'lien', [self.slug]

    def __str__(self):
        return self.lien

    class Meta:
        db_table = "liens"


class Utilisateur(models.Model):
    id = models.AutoField(primary_key=True)
    hash = models.CharField(max_length=32)

    class Meta:
        db_table = "utilisateurs"


class Connexion(models.Model):
    utilisateur = models.ForeignKey(Utilisateur, null=False)
    lien = models.ForeignKey(Lien, null=False)
    date = models.DateField(db_index=True)
    time = models.TimeField()
    ip = models.CharField(max_length=50)

    class Meta:
        db_table = "connexions"
