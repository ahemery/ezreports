# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-10-13 17:39
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Base',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('url', models.CharField(max_length=250)),
            ],
            options={
                'db_table': 'bases',
            },
        ),
        migrations.CreateModel(
            name='Plateforme',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('libelle', models.CharField(max_length=250)),
            ],
            options={
                'db_table': 'plateformes',
            },
        ),
        migrations.AddField(
            model_name='base',
            name='plateforme',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='front.Plateforme'),
        ),
    ]