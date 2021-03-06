# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-10-04 10:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('credo_modules', '0013_organization_types_update'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='organizationtype',
            options={'ordering': ['title']},
        ),
        migrations.AddField(
            model_name='organizationtype',
            name='enable_new_carousel_view',
            field=models.BooleanField(default=False, verbose_name='Enable new carousel view (horizontal nav bar)'),
        ),
    ]
