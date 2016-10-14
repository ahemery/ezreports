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


class Base(models.Model):
    id = models.AutoField(primary_key=True)
    url = models.CharField(max_length=250, null=False, unique=True)
    editeur = models.ForeignKey(Editeur, null=True, default=None)
    slug = models.SlugField(unique=True)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.url)
        super(Base, self).save(*args, **kwargs)

    @models.permalink
    def get_absolute_url(self):
        return 'base', [self.slug]

    def __str__(self):
        return self.url

    class Meta:
        db_table = "bases"
