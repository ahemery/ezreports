from __future__ import unicode_literals

from django.db import models


class Plateforme(models.Model):
    id = models.AutoField(primary_key=True)
    libelle = models.CharField(max_length=250, null=False)

    def __str__(self):
        return self.libelle

    class Meta:
        db_table = "plateformes"


class Base(models.Model):
    id = models.AutoField(primary_key=True)
    url = models.CharField(max_length=250, null=False)
    plateforme = models.ForeignKey(Plateforme, null=True)

    class Meta:
        db_table = "bases"
