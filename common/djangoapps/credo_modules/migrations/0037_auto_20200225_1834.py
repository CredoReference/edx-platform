# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2020-02-25 23:34
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('credo_modules', '0036_wistiaiframemigration'),
    ]

    operations = [
        migrations.AlterField(
            model_name='courseusagelogentry',
            name='time',
            field=models.DateTimeField(db_index=True),
        ),
    ]
