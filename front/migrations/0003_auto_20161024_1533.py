# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-10-24 13:33
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('front', '0002_lien_disabled'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lien',
            name='ressource',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='front.Ressource'),
        ),
    ]